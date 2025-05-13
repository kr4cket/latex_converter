from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from app.converter.stage.stage import Stage


class MarkerPdfTextExtractor(Stage):

    def __init__(self, **config):
        parser = ConfigParser(config)
        self.converter = PdfConverter(
            config=parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=parser.get_processors(),
            renderer=parser.get_renderer(),
            llm_service=parser.get_llm_service()
        )

    def process(self, data):
        if data['pdf'] is None:
            raise ValueError("Text extractor needs PDF file!")

        rendered = self.converter(data['pdf'])
        text, metadata, images = text_from_rendered(rendered)
        return text
