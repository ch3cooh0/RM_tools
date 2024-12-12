from io import BufferedReader
import requests
import os
from domain.interfaces.ocr_service import OCRService
from domain.entity.戦闘結果詳細 import 戦闘結果詳細
from pathlib import Path
from dotenv import load_dotenv
import sys

# 実行ファイルと同じディレクトリの.envを読み込む
env_path = Path(sys.executable).parent / '.env'
load_dotenv(env_path)

class OCRSpaceLine:
    def __init__(self):
        self.text = None
        self.min_top = None
        self.base_left = None

    def add_text(self, text: str):
        self.text = text

    def add_min_top(self, min_top: int):
        self.min_top = min_top

    def add_base_left(self, base_left: int):
        self.base_left = base_left


class OCRSpaceResult:
    def __init__(self):
        self.text = None
        self.lines = []

    def add_line(self, line: OCRSpaceLine):
        self.lines.append(line)

    def add_text(self, text: str):
        self.text = text

    def get_text(self):
        return self.text


class OCRSpaceRow:
    def __init__(self):
        self.lines = []
        self.base_min_top = None

    def add_line(self, line: OCRSpaceLine):
        self.lines.append(line)
        total_min_top = sum(line.min_top for line in self.lines)
        average_min_top = int(total_min_top / len(self.lines)) if self.lines else 0
        self.set_base_min_top(average_min_top)

    def set_base_min_top(self, min_top: int):
        self.base_min_top = min_top

    def get_base_min_top(self):
        return self.base_min_top

    def sort_lines(self):
        self.lines.sort(key=lambda x: x.base_left)

def convert(攻撃側戦闘結果詳細: 戦闘結果詳細, 守備側戦闘結果詳細: 戦闘結果詳細) -> str:
    攻撃側 = 攻撃側戦闘結果詳細.参戦数_to_tsv_str() + "\t攻\t\n" + 攻撃側戦闘結果詳細.被害数_to_tsv_str()
    守備側 = 守備側戦闘結果詳細.参戦数_to_tsv_str() + "\t守\t\n" + 守備側戦闘結果詳細.被害数_to_tsv_str()
    return f"{攻撃側}\n{守備側}"

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
            ocr_space_result = self.parse_ocr_space_result(result)
            攻撃側戦闘結果詳細, 守備側戦闘結果詳細 = self.parse_ocr_space_result_to_戦闘結果詳細(ocr_space_result)
            return convert(攻撃側戦闘結果詳細, 守備側戦闘結果詳細)
        except Exception as e:
            return f"エラー: {e}"

    def parse_ocr_space_result(self, result: dict) -> OCRSpaceResult:
        ocr_space_result = OCRSpaceResult()
        lines = result.get("ParsedResults", [{}])[0].get(
            "TextOverlay", {}).get("Lines", [{}])
        parsed_text = result.get("ParsedResults", [{}])[
            0].get("ParsedText", "")
        ocr_space_result.add_text(parsed_text)

        for line in lines:
            ocr_space_line = OCRSpaceLine()
            ocr_space_line.add_text(line.get("LineText", ""))
            ocr_space_line.add_min_top(line.get("MinTop", 0))
            words = line.get("Words", "")
            mean_left = sum(word.get("Left", 0) for word in words) / len(words)
            ocr_space_line.add_base_left(mean_left)
            ocr_space_result.add_line(ocr_space_line)
        return ocr_space_result

    def parse_ocr_space_result_to_戦闘結果詳細(self, ocr_space_result: OCRSpaceResult) -> tuple[戦闘結果詳細, 戦闘結果詳細]:
        # 戦闘結果を行単位にまとめたもの
        group = None
        for line in ocr_space_result.lines:
            print("lineInfo", line.text, line.min_top, line.base_left)
            if group is None:
                group = []
                row = OCRSpaceRow()
                row.add_line(line)
                group.append(row)
            else:
                is_added = False
                for row in group:
                    if abs(line.min_top - row.get_base_min_top()) <= 25:
                        row.add_line(line)
                        is_added = True
                        break
                if not is_added:
                    group.append(OCRSpaceRow())
                    group[-1].add_line(line)
        return self.create_戦闘結果詳細(group)

    def create_戦闘結果詳細(self, group: list[OCRSpaceRow]) -> tuple[戦闘結果詳細, 戦闘結果詳細]:
        def get_header_攻撃側兵士人数(group: list[OCRSpaceRow], 攻撃側Line: OCRSpaceLine, 守備側Line: OCRSpaceLine) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "兵士".lower() in line.text.lower():
                        if is_攻撃側(line, 攻撃側Line, 守備側Line):
                            return line
            return None

        def get_header_守備側兵士人数(group: list[OCRSpaceRow], 攻撃側Line: OCRSpaceLine, 守備側Line: OCRSpaceLine) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "兵士".lower() in line.text.lower():
                        if is_守備側(line, 攻撃側Line, 守備側Line):
                            return line
            return None

        def get_header_攻撃側損失人数(group: list[OCRSpaceRow], 攻撃側Line: OCRSpaceLine, 守備側Line: OCRSpaceLine) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "損失".lower() in line.text.lower():
                        if is_攻撃側(line, 攻撃側Line, 守備側Line):
                            return line
            return None

        def get_header_守備側損失人数(group: list[OCRSpaceRow], 攻撃側Line: OCRSpaceLine, 守備側Line: OCRSpaceLine) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "損失".lower() in line.text.lower():
                        if is_守備側(line, 攻撃側Line, 守備側Line):
                            return line
            return None

        def get_攻撃側OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "攻撃".lower() in line.text.lower():
                        return line
            return None

        def get_守備側OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "守備".lower() in line.text.lower():
                        return line
            return None

        def is_me(line: OCRSpaceLine) -> bool:
            if "あなた".lower() in line.text.lower():
                return True
            return False

        def is_攻撃側(line: OCRSpaceLine, 攻撃側座標: OCRSpaceLine, 守備側座標: OCRSpaceLine) -> bool:
            distance_to_攻撃側座標 = abs(line.base_left - 攻撃側座標.base_left)
            distance_to_守備側座標 = abs(line.base_left - 守備側座標.base_left)
            if distance_to_攻撃側座標 < distance_to_守備側座標:
                return True
            return False

        def is_守備側(line: OCRSpaceLine, 攻撃側座標: OCRSpaceLine, 守備側座標: OCRSpaceLine) -> bool:
            distance_to_攻撃側座標 = abs(line.base_left - 攻撃側座標.base_left)
            distance_to_守備側座標 = abs(line.base_left - 守備側座標.base_left)
            if distance_to_攻撃側座標 > distance_to_守備側座標:
                return True
            return False

        def get_T4_歩兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "レジェンドファイター".lower() in line.text.lower() or "ファイタ".lower() in line.text.lower():
                        return line
            return None

        def get_T4_弓兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "レジェンドガンナー".lower() in line.text.lower() or "ガンナー".lower() in line.text.lower():
                        return line
            return None

        def get_T4_騎兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "レジェンドドラグーン".lower() in line.text.lower() or "ドラグ".lower() in line.text.lower():
                        return line
            return None

        def get_T4_攻城OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "デストロイヤー".lower() in line.text.lower() or "デスト".lower() in line.text.lower():
                        return line
            return None

        def get_T3_歩兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "ロイヤルガーディアン".lower() in line.text.lower() or "ディアン".lower() in line.text.lower():
                        return line
            return None

        def get_T3_弓兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "ステルススナイパー".lower() in line.text.lower() or "ステルス".lower() in line.text.lower():
                        return line
            return None

        def get_T3_騎兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "ロイヤルライダー".lower() in line.text.lower() or "ライダ".lower() in line.text.lower():
                        return line
            return None

        def get_T3_攻城OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "フレイムランチャー".lower() in line.text.lower() or "ランチャ".lower() in line.text.lower() or "フレイム".lower() in line.text.lower():
                        return line
            return None

        def get_T2_歩兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "グラディエーター".lower() in line.text.lower() or "グラデ".lower() in line.text.lower():
                        return line
            return None

        def get_T2_弓兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "スナイパー".lower() in line.text.lower() or "スナイパ".lower() in line.text.lower() or "スナイバ".lower() in line.text.lower():
                        return line
            return None

        def get_T2_騎兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "リザードライダー".lower() in line.text.lower() or "ライダ".lower() in line.text.lower():
                        return line
            return None

        def get_T2_攻城OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "カタパルト".lower() in line.text.lower() or "カタバルト".lower() in line.text.lower() or "カタハルト".lower() in line.text.lower():
                        return line
            return None

        def get_T1_歩兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "ソルジャー".lower() in line.text.lower() or "ソルジャ".lower() in line.text.lower():
                        return line
            return None

        def get_T1_弓兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "アーチャー".lower() in line.text.lower() or "アーチャ".lower() in line.text.lower():
                        return line
            return None

        def get_T1_騎兵OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "ランサー".lower() in line.text.lower() or "ランサ".lower() in line.text.lower():
                        return line
            return None

        def get_T1_攻城OCRSpaceLine(group: list[OCRSpaceRow]) -> OCRSpaceLine:
            for row in group:
                for line in row.lines:
                    if "バリスタ".lower() in line.text.lower() or "バリスタ".lower() in line.text.lower():
                        return line
            return None

        def get_兵数(line: OCRSpaceLine) -> int:
            try:
                return int(line.text)
            except:
                return 0

        def create_戦闘結果詳細(group: list[OCRSpaceRow], header_兵士人数: OCRSpaceLine, header_損失人数: OCRSpaceLine) -> 戦闘結果詳細:
            result = 戦闘結果詳細()
            T4_歩兵OCRSpaceLine = get_T4_歩兵OCRSpaceLine(group)
            T4_弓兵OCRSpaceLine = get_T4_弓兵OCRSpaceLine(group)
            T4_騎兵OCRSpaceLine = get_T4_騎兵OCRSpaceLine(group)
            T4_攻城OCRSpaceLine = get_T4_攻城OCRSpaceLine(group)
            T3_歩兵OCRSpaceLine = get_T3_歩兵OCRSpaceLine(group)
            T3_弓兵OCRSpaceLine = get_T3_弓兵OCRSpaceLine(group)
            T3_騎兵OCRSpaceLine = get_T3_騎兵OCRSpaceLine(group)
            T3_攻城OCRSpaceLine = get_T3_攻城OCRSpaceLine(group)
            T2_歩兵OCRSpaceLine = get_T2_歩兵OCRSpaceLine(group)
            T2_弓兵OCRSpaceLine = get_T2_弓兵OCRSpaceLine(group)
            T2_騎兵OCRSpaceLine = get_T2_騎兵OCRSpaceLine(group)
            T2_攻城OCRSpaceLine = get_T2_攻城OCRSpaceLine(group)
            T1_歩兵OCRSpaceLine = get_T1_歩兵OCRSpaceLine(group)
            T1_弓兵OCRSpaceLine = get_T1_弓兵OCRSpaceLine(group)
            T1_騎兵OCRSpaceLine = get_T1_騎兵OCRSpaceLine(group)
            T1_攻城OCRSpaceLine = get_T1_攻城OCRSpaceLine(group)

            def is_同行(line1: OCRSpaceLine, base_min_top: int) -> bool:
                if line1 is None or base_min_top is None:
                    return False
                if abs(line1.min_top - base_min_top) <= 10:
                    return True
                return False

            def is_兵士列(line: OCRSpaceLine, 兵士列: OCRSpaceLine, 損失列: OCRSpaceLine) -> bool:
                if line is None or 兵士列 is None or 損失列 is None:
                    return False
                distance_to_兵士列 = abs(line.base_left - 兵士列.base_left)
                distance_to_損失列 = abs(line.base_left - 損失列.base_left)
                if distance_to_兵士列 <= distance_to_損失列:
                    return True
                return False

            def is_損失列(line: OCRSpaceLine, 兵士列: OCRSpaceLine, 損失列: OCRSpaceLine) -> bool:
                if line is None or 損失列 is None:
                    return False
                distance_to_兵士列 = abs(line.base_left - 兵士列.base_left)
                distance_to_損失列 = abs(line.base_left - 損失列.base_left)
                if distance_to_損失列 <= distance_to_兵士列:
                    return True
                return False

            for row in group:
                if is_同行(T4_歩兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T4_歩兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T4_歩兵被害数 = get_兵数(line)
                if is_同行(T4_弓兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T4_弓兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T4_弓兵被害数 = get_兵数(line)
                if is_同行(T4_騎兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T4_騎兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T4_騎兵被害数 = get_兵数(line)
                if is_同行(T4_攻城OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T4_攻城数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T4_攻城被害数 = get_兵数(line)
                if is_同行(T3_歩兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T3_歩兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T3_歩兵被害数 = get_兵数(line)
                if is_同行(T3_弓兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T3_弓兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T3_弓兵被害数 = get_兵数(line)
                if is_同行(T3_騎兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T3_騎兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T3_騎兵被害数 = get_兵数(line)
                if is_同行(T3_攻城OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T3_攻城数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T3_攻城被害数 = get_兵数(line)
                if is_同行(T2_歩兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T2_歩兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T2_歩兵被害数 = get_兵数(line)
                if is_同行(T2_弓兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T2_弓兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T2_弓兵被害数 = get_兵数(line)
                if is_同行(T2_騎兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T2_騎兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T2_騎兵被害数 = get_兵数(line)
                if is_同行(T2_攻城OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T2_攻城数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T2_攻城被害数 = get_兵数(line)
                if is_同行(T1_歩兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T1_歩兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T1_歩兵被害数 = get_兵数(line)
                if is_同行(T1_弓兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T1_弓兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T1_弓兵被害数 = get_兵数(line)
                if is_同行(T1_騎兵OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T1_騎兵数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T1_騎兵被害数 = get_兵数(line)
                if is_同行(T1_攻城OCRSpaceLine, row.get_base_min_top()):
                    for line in row.lines:
                        if is_兵士列(line, header_兵士人数, header_損失人数):
                            result.T1_攻城数 = get_兵数(line)
                        if is_損失列(line, header_兵士人数, header_損失人数):
                            result.T1_攻城被害数 = get_兵数(line)
            return result

        def get_攻撃側被害詳細(group: list[OCRSpaceRow]) -> 戦闘結果詳細:
            攻撃側OCRSpaceLine = get_攻撃側OCRSpaceLine(group)
            守備側OCRSpaceLine = get_守備側OCRSpaceLine(group)
            header_攻撃側兵士人数 = get_header_攻撃側兵士人数(
                group, 攻撃側OCRSpaceLine, 守備側OCRSpaceLine)
            header_攻撃側損失人数 = get_header_攻撃側損失人数(
                group, 攻撃側OCRSpaceLine, 守備側OCRSpaceLine)
            if 攻撃側OCRSpaceLine is None or header_攻撃側兵士人数 is None or header_攻撃側損失人数 is None:
                result = 戦闘結果詳細()
                return result
            result = create_戦闘結果詳細(group, header_攻撃側兵士人数, header_攻撃側損失人数)
            result.set_is_me(is_me(攻撃側OCRSpaceLine))
            return result

        def get_守備側被害詳細(group: list[OCRSpaceRow]) -> 戦闘結果詳細:
            攻撃側OCRSpaceLine = get_攻撃側OCRSpaceLine(group)
            守備側OCRSpaceLine = get_守備側OCRSpaceLine(group)
            header_守備側兵士人数 = get_header_守備側兵士人数(
                group, 攻撃側OCRSpaceLine, 守備側OCRSpaceLine)
            header_守備側損失人数 = get_header_守備側損失人数(
                group, 攻撃側OCRSpaceLine, 守備側OCRSpaceLine)
            if 守備側OCRSpaceLine is None or header_守備側兵士人数 is None or header_守備側損失人数 is None:
                result = 戦闘結果詳細() 
                return result
            result = create_戦闘結果詳細(group, header_守備側兵士人数, header_守備側損失人数)
            result.set_is_me(is_me(守備側OCRSpaceLine))
            return result

        attack_result = get_攻撃側被害詳細(group)
        defense_result = get_守備側被害詳細(group)
        return attack_result, defense_result


