from abc import ABC, abstractmethod

class OCRService(ABC):
    @abstractmethod
    def extract_text(self, image_data: bytes) -> str:
        pass 