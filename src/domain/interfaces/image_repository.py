from abc import ABC, abstractmethod
from PIL import Image

class ImageRepository(ABC):
    @abstractmethod
    def save_temporary_image(self, image: Image.Image) -> str:
        pass

    @abstractmethod
    def get_image_from_path(self, file_path: str) -> Image.Image:
        pass 