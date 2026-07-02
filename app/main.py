import base64
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Yu Gothic"   # 日本語対応
import webview
from PIL import Image, ImageDraw, ImageFont
#独自モジュール
from common_lib_mw import create_ope_graph as cog
from common_lib_mw import opdata_generator as opg
#(注意: opdata_generatorは新江工場用であり稼働データ3330個が前提)
import db


# ----- CONSTANTS ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"


# ----- FUNCTIONS ---------------------------------------------------
def data_convert_to_sine(data_1500:list[int]) -> list[int]:
    """本社工場用データから新江工場用データへ変換

           本社工場     新江工場
    data数: 1500個   →  3330個
    生産数: data[2]  →  data[4]
    異常数: data[3]  →  data[5]
    目標数: data[4]  →  data[7]
    """
    data_3330 = data_1500 + [0] * 1830      # 要素数変更(3330個)

    # 生産数格納
    data_3330[4] = data_1500[2]
    # 異常数格納
    data_3330[5] = data_1500[3]
    # 目標数格納
    data_3330[7] = data_1500[4] 

    return data_3330


# ----- CLASS(API) --------------------------------------------------
class AppAPI:
    
    def get_detail_graph_images(self, machine_no: str="", production_date: str="") -> dict:
        """設備別詳細ページ用の画像をBase64文字列で返す。
        """
        # SQLiteよりデータ取得 & データフォーマット変換
        ope_data_1500 = db.get_all_data(machine_no, production_date)    # 本社稼働データ(1500個)
        ope_data_3330 = data_convert_to_sine(ope_data_1500)             # 新江工場用へ変換(3330個)

        # ステータス図(稼働状態図)取得
        img = cog.get_ope_graph(ope_data_3330, title=f"MC{machine_no} / {production_date}")
        img64 = self._image_to_base64(img)


        # 稼働データ サマリー取得
        ope_summary = opg.get_opdata_list(ope_data_3330)
        for item in ope_summary:
            print(item)

        # 上のサマリーデータを使って棒グラフ描画＆Base64変換
        # (作成予定)

        return {
            "state_diagram": img64,
            "state_bar_chart": self._create_state_bar_chart_base64(machine_no, production_date, ope_summary,),
        }
    

    def _create_state_bar_chart_base64(
            self,
            machine_no: str,
            production_date: str,
            ope_summary: list[list]
    ) -> str:
        """ope_summaryから稼働状態別の棒グラフ画像を作成し、Base64文字列で返す。"""

        target_labels = [
            "稼働時間[分]",
            "単純停止[分]",
            "故障ロス[分]",
            "段取ロス[分]",
            "刃具交換ロス[分]",
            "アラーム発生[分]",
            "材料切れ[分]",
            "不明[分]",
        ]

        summary_dict = dict(ope_summary)

        labels = target_labels
        minutes = [
            summary_dict.get(label, 0)
            for label in target_labels
        ]

        fig, ax = plt.subplots(figsize=(10, 3.5), dpi=120)
        ax.bar(labels, minutes)

        ax.set_title(f"状態別時間 / MC:{machine_no or '-'} / Date:{production_date or '-'}")
        ax.set_ylabel("分")
        ax.grid(axis="y", alpha=0.3)

        ax.tick_params(axis="x", labelrotation=30)

        max_minutes = max(minutes) if minutes else 0
        ax.set_ylim(0, max_minutes * 1.2 if max_minutes > 0 else 10)

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