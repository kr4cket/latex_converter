import pdfplumber
from PyPDF2 import PdfWriter, PdfReader

from app.converter.stage.stage import Stage
from app.converter.utils.helpers import create_dir


class PDFPreprocessor(Stage):
    __output_prefix = "page_"
    __dir = "pdf"

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

                output_filename = f"{directory}/{self.__output_prefix}{i + 1}.pdf"
                with open(output_filename, "wb") as out:
                    writer.write(out)
                pages.append(output_filename)

        return pages

    def get_name(self):
        return 'pdf'


def split_pdf_by_pages(input_pdf, filename, output_prefix="page_") -> list:
    pages = []

    with pdfplumber.open(input_pdf) as pdf:
        total_pages = len(pdf.pages)
        reader = PdfReader(input_pdf)

        for i in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            output_filename = f"../../../temp/{filename}/pdf/{output_prefix}{i + 1}.pdf"
            with open(output_filename, "wb") as out:
                writer.write(out)
            pages.append(output_filename)

    return pages
