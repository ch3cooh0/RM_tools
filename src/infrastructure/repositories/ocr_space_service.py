from io import BufferedReader
import requests
import os
from domain.interfaces.ocr_service import OCRService

class OCRSpaceService(OCRService):
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        print(self.api_key)
        self.api_url = "https://api.ocr.space/parse/image"

    def extract_text(self, image_file: BufferedReader) -> str:
        try:
            response = requests.post(
                self.api_url,
                files={'file': image_file},
                data={
                    'apikey': self.api_key,
                    'language': 'jpn',
                    'isOverlayRequired': True
                },
                timeout=30
            )
            result = response.json()
            lines = result.get("ParsedResults", [{}])[0].get("TextOverlay", {}).get("Lines", [{}])
            grouped_lines = []
            current_group = []

            for line in lines:
                if not current_group:
                    current_group.append(line)
                else:
                    last_line = current_group[-1]
                    last_info = last_line.get("LineText") + ":" + str(last_line.get("MinTop"))
                    current_info = line.get("LineText") + ":" + str(line.get("MinTop"))
                    print(last_info)
                    print(current_info)
                    print(abs(line.get("MinTop", 0) - last_line.get("MinTop", 0)))
                    if abs(line.get("MinTop", 0) - last_line.get("MinTop", 0)) <= 25:
                        current_group.append(line)
                    else:
                        grouped_lines.append(current_group)
                        current_group = [line]

            if current_group:
                grouped_lines.append(current_group)

            for group in grouped_lines:
                print("group")
                for line in group:
                    print(line.get("LineText", ""), line.get("MinTop"))
            return "\n".join([line.get("LineText", "") for line in lines])
        except Exception as e:
            return f"エラー: {e}" 