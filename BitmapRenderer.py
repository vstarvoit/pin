from abc import ABC, abstractmethod

class BitmapRenderer(ABC):
    @abstractmethod
    def process(self, bytearray:bytearray) -> None:
        pass