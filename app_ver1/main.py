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
    
    # 設備別状態時間グラフで使用
    STATUS_ITEMS = [
        {
            "summary_label": "稼働時間[分]",
            "display_label": "自動中",
            "color": (50, 205, 50),
        },
        {
            "summary_label": "単純停止[分]",
            "display_label": "停止中",
            "color": (128, 128, 128),
        },
        {
            "summary_label": "故障ロス[分]",
            "display_label": "故障中",
            "color": (255, 0, 0),
        },
        {
            "summary_label": "段取ロス[分]",
            "display_label": "段替え",
            "color": (0, 0, 255),
        },
        {
            "summary_label": "刃具交換ロス[分]",
            "display_label": "刃具交換",
            "color": (135, 206, 235),
        },
        {
            "summary_label": "アラーム発生[分]",
            "display_label": "異常中",
            "color": (255, 20, 147),
        },
        {
            "summary_label": "材料切れ[分]",
            "display_label": "材料切れ",
            "color": (255, 255, 0),
        },
        {
            "summary_label": "不明[分]",
            "display_label": "不明",
            "color": (0, 0, 0),
        },
    ]


    def get_detail_graph_images(self, machine_no: str="", production_date: str="") -> dict:
        """設備別詳細ページ用の画像をBase64文字列で返す。
        """
        # SQLiteよりデータ取得 & データフォーマット変換
        ope_data_1500 = db.get_all_data_or_zeros(machine_no, production_date)    # 本社稼働データ(1500個)
        ope_data_3330 = data_convert_to_sine(ope_data_1500)             # 新江工場用へ変換(3330個)

        # 状態タイムライン取得
        img_timeline = cog.get_ope_graph(ope_data_3330, title=f"MC{machine_no} / {production_date}")
        img64_timeline = self._image_to_base64(img_timeline)


        # 稼働データ サマリー取得
        ope_summary = opg.get_opdata_list(ope_data_3330)
        # for item in ope_summary:
        #     print(item)

        # 状態時間グラフ作成
        img64_barchart = self._create_state_bar_chart_base64(ope_summary,)

        return {
            "state_timeline": img64_timeline,
            "state_bar_chart": img64_barchart,
        }
    

    def _create_state_bar_chart_base64(
            self,
            ope_summary: list[list]
    ) -> str:
        """ope_summaryから稼働状態別の棒グラフ画像を作成し、Base64文字列で返す。"""

        summary_dict = dict(ope_summary)

        labels = [
            item["display_label"]
            for item in self.STATUS_ITEMS
        ]

        minutes = [
            summary_dict.get(item["summary_label"], 0)
            for item in self.STATUS_ITEMS
        ]

        # 棒グラフの色（0～255 → 0.0～1.0へ変換）
        colors = [
            tuple(c / 255 for c in item["color"])
            for item in self.STATUS_ITEMS
        ]

        fig, ax = plt.subplots(figsize=(16, 3), dpi=100)
        # <グラフサイズ> 横: 16inch x 100dpi = 1600px / 縦: 3inch x 100dpi = 300px

        bars = ax.bar(
            labels,
            minutes,
            color=colors,
            edgecolor="black",
            linewidth=1
        )

        # 各要素の値表示
        for bar, value in zip(bars, minutes):
            ax.text(
                bar.get_x() + bar.get_width() / 2,  # 棒の中央
                value + 5,                          # 棒より少し上
                f"{value}",                         # 表示する値
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold"
            )

        ax.set_ylabel("分")
        ax.grid(axis="y", alpha=0.3)

        ax.tick_params(axis="x", labelrotation=0)

        ax.set_ylim(0, 540)

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
    

    def get_machine_no_list(self) -> list[int]:
        """設備番号一覧を返す"""
        return db.get_machine_no_list()


    def export_each_machine_timeline_png_to_desktop(self, production_date: str) -> dict:
        """
        指定日の設備別タイムライン画像を、デスクトップ上のフォルダに保存する
        """
        desktop_dir = Path.home() / "Desktop"
        output_dir = desktop_dir / f"設備タイムライン_{production_date}"

        output_dir.mkdir(exist_ok=True)

        machine_no_list = db.get_machine_no_list()

        saved_files = []

        for machine_no in machine_no_list:
            try:
                ope_data_1500 = db.get_all_data(machine_no, production_date)
                ope_data_3330 = data_convert_to_sine(ope_data_1500)
                
                img_timeline = cog.get_ope_graph(
                    ope_data_3330,
                    title=f"MC{machine_no} / {production_date}"
                )

                file_path = output_dir / f"MC{machine_no}_timeline_{production_date}.png"

                img_timeline.save(file_path)

                saved_files.append(str(file_path))

            except ValueError:
                # 指定日にデータがない場合はスキップ
                continue

        if not saved_files:
            raise ValueError(
                f"出力できるデータがありません。production_date={production_date}"
            )

        return {
            "output_dir": str(output_dir),
            "file_count": len(saved_files),
        }


    def get_machine_trend_graph_images(
            self,
            machine_no: str,
            base_date: str,
            display_days: str
    ) -> dict:
        """
        設備別推移ページ用のグラフ画像をBase64文字列で返す
        """
        machine_no_int = int(machine_no)
        display_days_int = int(display_days)

        trend_data = db.get_daily_trend_data(machine_no_int, base_date, display_days_int)

        img64_actual_count = self._create_trend_bar_chart_base64(
            trend_data=trend_data,
            machine_no=machine_no_int,
            base_date=base_date,
            title="日別生産数",
            value_key="actual_count",
            y_label="生産数",
            bar_color=(50, 205, 50),
            target_line=True,
        )

        img64_alarm_count = self._create_trend_bar_chart_base64(
            trend_data=trend_data,
            machine_no=machine_no_int,
            base_date=base_date,
            title="日別アラーム数",
            value_key="alarm_count",
            y_label="アラーム数",
            bar_color=(255, 105, 180),
            target_line=False,  
        )

        return {
            "actual_count": img64_actual_count,
            "alarm_count": img64_alarm_count
        }


    def _create_trend_bar_chart_base64(
            self,
            trend_data: list[dict],
            machine_no: int,
            base_date: str,
            title: str,
            value_key: str,
            y_label: str,
            bar_color: tuple[int, int, int],
            target_line: bool = False
    ) -> str:
        """
        設備別推移用の棒グラフ画像をBase64文字列で返す
        """
        date_labels = [
            item["production_date"][5:]
            for item in trend_data
        ]

        values = [
            item[value_key]
            for item in trend_data
        ]

        colors = [
            (0.6, 0.6, 0.6)
            if self._is_weekend(item["production_date"])
            else tuple(c / 255 for c in bar_color)
            for item in trend_data
        ]

        fig, ax = plt.subplots(figsize=(16, 3.5), dpi=100,constrained_layout=True)

        bars = ax.bar(
            date_labels,
            [
                0 if value is None else value
                for value in values
            ],
            color=colors,
            edgecolor="black",
            linewidth=1
        )

        for bar, value in zip(bars, values):
            if value is None:
                continue

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{int(value)}",
                ha="center",
                va="bottom",
                fontsize=8
            )

        if target_line:
            target_values = [
                item["target_count"]
                for item in trend_data
                if item["target_count"] is not None
            ]

            if target_values:
                target = target_values[-1]

                ax.axhline(
                    y=target,
                    color="red",
                    linestyle="--",
                    linewidth=2,
                    label=f"目標: {target}"
                )

                ax.legend()

        ax.set_title(f"MC{machine_no} {title} / 基準日={base_date}")
        ax.set_ylabel(y_label)
        ax.grid(axis="y", alpha=0.3)
        ax.tick_params(axis="x", labelrotation=90)

        # fig.tight_layout()

        buffer = BytesIO()
        fig.savefig(buffer, format="png")

        # 確認用にそのままPNG保存
        # with open("debug_trend_graph.png", "wb") as f:
        #     f.write(buffer.getvalue())

        plt.close(fig)
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")


    def _is_weekend(self, date_text: str) -> bool:
        """
        YYYY-MM-DD文字列が土日かどうか判定する
        """
        from datetime import datetime

        d = datetime.strptime(date_text, "%Y-%m-%d").date()

        return d.weekday() >= 5




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