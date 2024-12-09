from dotenv import load_dotenv
from infrastructure.repositories.ocr_space_service import OCRSpaceService
from infrastructure.repositories.local_image_repository import LocalImageRepository
from application.use_cases.image_processing_use_case import ImageProcessingUseCase
from presentation.gui.main_window import MainWindow

def main():
    load_dotenv()
    
    # 依存性の注入
    ocr_service = OCRSpaceService()
    image_repository = LocalImageRepository()
    use_case = ImageProcessingUseCase(ocr_service, image_repository)
    
    # GUIの起動
    app = MainWindow(use_case)
    app.run()

if __name__ == "__main__":
    main() 