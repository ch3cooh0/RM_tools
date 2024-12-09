import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import requests
import pyperclip
import io
from dotenv import load_dotenv
import os

# .envファイルからAPIキーを取得
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = "https://api.ocr.space/parse/image"
print(API_KEY)

def ocr_image(file_path):
    """OCRSpace APIを利用して画像からテキストを抽出"""
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(
                API_URL,
                files={'file': file},
                data={
                    'apikey': API_KEY,
                    'language': 'jpn',  # 言語を日本語に変更
                    'isOverlayRequired': True  # オーバーレイを有効にする
                },
                timeout=30  # タイムアウトを30秒に設定
            )
        result = response.json()
        print(result)
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "テキストが抽出できませんでした。")
    except requests.exceptions.Timeout:
        print("リクエストがタイムアウトしました。")
        return "リクエストがタイムアウトしました。"
    except Exception as e:
        print(f"エラー: {e}")
        return f"エラー: {e}"


def handle_file_drop(event):
    """ドラッグアンドドロップでファイルを受け取る"""
    file_path = event.data.strip()
    if file_path.startswith("{") and file_path.endswith("}"):  # Windowsの場合
        file_path = file_path[1:-1]
    process_image(file_path)


def process_image(file_path):
    """画像を表示してOCR処理を実行"""
    try:
        img = Image.open(file_path)
        img.thumbnail((400, 400))  # サムネイルサイズに調整
        photo = ImageTk.PhotoImage(img)
        image_label.config(image=photo)
        image_label.image = photo

        # OCR処理
        text = ocr_image(file_path)
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, text)
    except Exception as e:
        messagebox.showerror("エラー", f"画像を処理できませんでした: {e}")


def paste_from_clipboard():
    """クリップボードから画像を貼り付けてOCR処理"""
    try:
        img_data = root.clipboard_get(type='image/png')
        img = Image.open(io.BytesIO(img_data))
        img.save("clipboard_image.png")  # 一時ファイルとして保存
        process_image("clipboard_image.png")
    except Exception as e:
        messagebox.showerror("エラー", f"クリップボードの画像を読み取れませんでした: {e}")


def open_file():
    """ファイル選択ダイアログを開く"""
    file_path = filedialog.askopenfilename(
        filetypes=[("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    if file_path:
        process_image(file_path)


# Tkinterウィンドウの設定
root = TkinterDnD.Tk()  # TkinterDnDを使用
root.title("OCRツール")
root.geometry("600x600")

# UI部品の配置
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

btn_open = tk.Button(frame, text="画像を開く", command=open_file)
btn_open.pack(pady=5)

btn_paste = tk.Button(frame, text="クリップボードから貼り付け", command=paste_from_clipboard)
btn_paste.pack(pady=5)

image_label = tk.Label(frame)
image_label.pack(pady=10)

text_box = tk.Text(frame, wrap=tk.WORD, height=10)
text_box.pack(fill=tk.BOTH, expand=True)

# ドラッグアンドドロップを有効化
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', handle_file_drop)

# メインループ
root.mainloop()
