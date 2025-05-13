import json

from img2table.document import Image
from img2table.ocr import TesseractOCR

from app.converter.stage.stage import Stage


class TesseractTablesExtractor(Stage):
    def process(self, data):
        file = Image(src=data['img'])
        ocr = TesseractOCR(lang="rus")
        try:
            tables = file.extract_tables(ocr=ocr,
                                         implicit_rows=True,
                                         borderless_tables=True)

            tables_str = json.dumps([table.to_json() for table in tables],
                                    ensure_ascii=False,
                                    indent=2)

        except Exception as e:
            print(f"error while extracting tables:{e}")
            tables_str = ""

        return tables_str
