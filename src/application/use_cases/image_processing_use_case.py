from domain.interfaces.ocr_service import OCRService
from domain.interfaces.image_repository import ImageRepository
from PIL import Image

class ImageProcessingUseCase:
    def __init__(self, ocr_service: OCRService, image_repository: ImageRepository):
        self.ocr_service = ocr_service
        self.image_repository = image_repository

    def process_image_file(self, file_path: str) -> tuple[Image.Image, str]:
        image = self.image_repository.get_image_from_path(file_path)
        with open(file_path, 'rb') as f:
            text = self.ocr_service.extract_text(f)
        return image, text

    def process_clipboard_image(self, image: Image.Image) -> tuple[Image.Image, str]:
        temp_path = self.image_repository.save_temporary_image(image)
        with open(temp_path, 'rb') as f:
            text = self.ocr_service.extract_text(f)
        return image, text 