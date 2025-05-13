from abc import ABC, abstractmethod


class Stage(ABC):
    @abstractmethod
    def process(self, data):
        pass

    def get_name(self):
        return self.__class__.__name__
