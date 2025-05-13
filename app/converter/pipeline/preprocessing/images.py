import os

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

from app.converter.stage.stage import Stage
from app.converter.utils.helpers import pdf_to_image, enhance_image, create_dir


class ImagePreprocessor(Stage):
    __output_prefix = "page_"
    __dir = "img"

    def __init__(self, directory, output_prefix):
        self.__output_prefix = output_prefix
        self.__dir = directory

    def process(self, data):
        input_pdf = data['input']
        directory = f"{data['dir']}/{self.__dir}"
        create_dir(directory)
        pages = []

        with pdfplumber.open(input_pdf) as pdf:
            total_pages = len(pdf.pages)
            reader = PdfReader(input_pdf)

            for i in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])

                output_pdf = f"{directory}/{self.__output_prefix}{i + 1}.pdf"
                with open(output_pdf, "wb") as out:
                    writer.write(out)

                img = pdf_to_image(output_pdf)
                img = enhance_image(img)

                output_img = f"{directory}/{self.__output_prefix}{pref + 1}.png"
                img.save(output_img, 'PNG', quality=95, optimize=True, dpi=(600, 600))

                os.remove(output_pdf)
                pages.append(output_img)

        return pages

    def get_name(self):
        return 'img'
