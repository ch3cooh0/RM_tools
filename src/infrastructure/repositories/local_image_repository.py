from PIL import Image
import io
from domain.interfaces.image_repository import ImageRepository

class LocalImageRepository(ImageRepository):
    def save_temporary_image(self, image: Image.Image) -> str:
        temp_path = "clipboard_image.png"
        image.save(temp_path)
        return temp_path

    def get_image_from_path(self, file_path: str) -> Image.Image:
        return Image.open(file_path) 