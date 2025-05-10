from abc import ABC, abstractmethod

class Stage(ABC):
    @abstractmethod
    def process(self, data):
        pass

    @abstractmethod
    def get_name(self):
        pass