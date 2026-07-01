import base64
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import webview
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"


class AppAPI:
    """後からSQLite取得処理などを実装するためのAPI置き場。"""
    
    def get_detail_graph_images(self, machine_no: str="", production_date: str="") -> dict:
        """設備別詳細ページ用の仮画像をBase64文字列で返す。

        現段階ではダミーデータです。
        後でSQLite(main_factory_production_data.db)から取得した実データで作成します。
        """
        return {
            "state_diagram": self._create_state_diagram_base64(machine_no, production_date),
            "state_bar_chart": self._create_state_bar_chart_base64(machine_no, production_date),
        }
    
    def _create_state_diagram_base64(self, machine_no: str, production_date: str) -> str:
        """Pillowで稼働状態図のダミー画像を作成する。"""
        width = 1500
        height = 300

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        try:
            font_title = ImageFont.truetype("DejaVuSans.ttf", 28)
            font = ImageFont.truetype("DejaVuSans.ttf", 20)
        except OSError:
            font_title = ImageFont.load_default()
            font = ImageFont.load_default()

        title = f"Machine detail state diagram / MC:{machine_no or '-'} / Date:{production_date or '-'}"
        draw.text((30, 20), title, fill=(40, 40, 40), font=font_title)

        # ダミーのタイムライン。後でSQLiteの実績データに置き換える想定。
        timeline_top = 110
        timeline_height = 80
        timeline_left = 40
        timeline_width = 1420

        draw.rectangle(
            (timeline_left, timeline_top, timeline_left + timeline_width, timeline_top + timeline_height),
            outline=(80, 80, 80),
            width=2,
        )

        states = [
            (0.00, 0.18, "Auto", (120, 210, 140)),
            (0.18, 0.25, "Stop", (220, 220, 220)),
            (0.25, 0.52, "Auto", (120, 210, 140)),
            (0.52, 0.60, "Change", (250, 220, 120)),
            (0.60, 0.78, "Auto", (120, 210, 140)),
            (0.78, 0.86, "Alarm", (245, 140, 160)),
            (0.86, 1.00, "Auto", (120, 210, 140)),
        ]

        for start_rate, end_rate, label, color in states:
            x1 = timeline_left + int(timeline_width * start_rate)
            x2 = timeline_left + int(timeline_width * end_rate)
            draw.rectangle((x1, timeline_top, x2, timeline_top + timeline_height), fill=color, outline=(255, 255, 255))
            draw.text((x1 + 8, timeline_top + 25), label, fill=(30, 30, 30), font=font)

        # 時刻目盛りのダミー表示
        for hour in range(0, 25, 4):
            x = timeline_left + int(timeline_width * hour / 24)
            draw.line((x, timeline_top + timeline_height, x, timeline_top + timeline_height + 12), fill=(80, 80, 80), width=2)
            draw.text((x - 18, timeline_top + timeline_height + 18), f"{hour:02d}:00", fill=(60, 60, 60), font=font)

        return self._image_to_base64(image)

    def _create_state_bar_chart_base64(self, machine_no: str, production_date: str) -> str:
        """matplotlibで稼働状態別の棒グラフのダミー画像を作成する。"""
        labels = ["Auto", "Stop", "Change", "Alarm"]
        minutes = [920, 210, 180, 130]

        fig, ax = plt.subplots(figsize=(10, 3.5), dpi=120)
        ax.bar(labels, minutes)
        ax.set_title(f"State summary / MC:{machine_no or '-'} / Date:{production_date or '-'}")
        ax.set_ylabel("Minutes")
        ax.set_ylim(0, 1000)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()

        buffer = BytesIO()
        fig.savefig(buffer, format="png")
        plt.close(fig)
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Pillow画像をPNGのBase64文字列に変換する。"""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


if __name__ == "__main__":
    api = AppAPI()
    window = webview.create_window(
        title="本社工場見える化アプリ",
        url = str(HTML_FILE),
        js_api=api,
        width=1920,
        height=1080,
    )
    webview.start(gui="edgechromium", debug=True)