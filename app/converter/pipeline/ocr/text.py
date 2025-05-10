import pytesseract
from PIL import Image
from app.converter.stage.stage import Stage


class TextExtractor(Stage):
    def get_name(self):
        return 'text'

    def process(self, data):
        img = Image.open(data['img'])
        return pytesseract.image_to_string(img, lang='rus+eng')
