import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import io
from application.use_cases.image_processing_use_case import ImageProcessingUseCase
class MainWindow:
    def __init__(self, image_processing_use_case: ImageProcessingUseCase):
        self.use_case = image_processing_use_case
        self.setup_ui()

    def setup_ui(self):
        self.root = TkinterDnD.Tk()
        self.root.title("OCRツール")
        self.root.geometry("600x600")

        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        btn_open = tk.Button(frame, text="画像を開く", command=self.open_file)
        btn_open.pack(pady=5)

        btn_paste = tk.Button(frame, text="クリップボードから貼り付け", 
                            command=self.paste_from_clipboard)
        btn_paste.pack(pady=5)

        self.image_label = tk.Label(frame)
        self.image_label.pack(pady=10)

        self.text_box = tk.Text(frame, wrap=tk.WORD, height=10)
        self.text_box.pack(fill=tk.BOTH, expand=True)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_file_drop)

    def display_result(self, image: Image.Image, text: str):
        image.thumbnail((400, 400))
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, text)

    def handle_file_drop(self, event):
        file_path = event.data.strip()
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        self.process_image(file_path)

    def process_image(self, file_path):
        try:
            image, text = self.use_case.process_image_file(file_path)
            self.display_result(image, text)
        except Exception as e:
            messagebox.showerror("エラー", f"画像を処理できませんでした: {e}")

    def paste_from_clipboard(self):
        try:
            img_data = self.root.clipboard_get(type='image/png')
            img = Image.open(io.BytesIO(img_data))
            image, text = self.use_case.process_clipboard_image(img)
            self.display_result(image, text)
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"クリップボードの画像を読み取れませんでした: {e}")

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            self.process_image(file_path)

    def run(self):
        self.root.mainloop() 