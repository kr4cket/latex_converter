import cv2
import numpy as np
from PIL import Image
import os
import hashlib

from pix2tex.cli import LatexOCR

from app.converter.stage.stage import Stage


class FormulasExtractor(Stage):
    def __init__(self, required_symbols, math_keywords, cache_dir):
        self.model = LatexOCR()
        self.required_symbols = required_symbols
        self.math_keywords = math_keywords
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def process(self, data):
        img = Image.open(data['img'])
        img_hash = hashlib.md5(np.array(img).tobytes()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{img_hash}.txt")

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return f.read().splitlines()

        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        kernel = np.ones((2, 2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        formulas = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            if not self._is_potential_formula(w, h):
                continue

            region = img.crop((x, y, x + w, y + h))

            if self._is_too_dense(region):
                continue

            try:
                formula = self.model(region).strip()
                if self._is_valid_formula(formula):
                    formulas.append(formula)
            except:
                continue

        unique_formulas = list(set(formulas))
        with open(cache_file, 'w') as f:
            f.write("\n".join(unique_formulas))

        return unique_formulas

    def _is_potential_formula(self, w, h):
        """Определяет, может ли область быть формулой"""
        area = w * h
        if area < 200 or area > 10000:
            return False
        aspect = w / float(h)
        return 0.25 <= aspect <= 4

    def _is_too_dense(self, image, threshold=0.3):
        """Проверяет, слишком ли плотная область (текст плотнее формул)"""
        gray = np.array(image.convert('L'))
        return np.mean(gray < 128) > threshold

    def _is_valid_formula(self, text):
        """Строгая проверка, что текст - это формула"""
        if len(text) < 5 or len(text) > 200:
            return False

        has_symbols = any(c in text for c in self.required_symbols)
        has_math = any(kw in text for kw in self.math_keywords)

        return has_symbols and has_math
