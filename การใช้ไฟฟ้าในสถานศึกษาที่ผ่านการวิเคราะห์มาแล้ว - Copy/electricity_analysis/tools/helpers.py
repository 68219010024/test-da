"""Shared helpers for both notebooks (blue-white theme, Thai-safe fonts, chart explanation boxes)."""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from IPython.display import Markdown, display

BLUE, BLUE_L, BLUE_D, GREY, RED, ORANGE = "#1E6FD9", "#8DB9F2", "#0B3C8C", "#8A94A6", "#D64545", "#F29F3D"
SMALL_N_ROOMS = 6  # DEFAULT (self-set): groups with fewer rooms than this get a warning label


def setup_plot():
    # pick the first Thai-capable font installed on this machine
    avail = {f.name for f in fm.fontManager.ttflist}
    for name in ["Leelawadee UI", "Tahoma", "Loma", "Noto Sans Thai", "Sarabun", "Garuda", "DejaVu Sans"]:
        if name in avail:
            matplotlib.rcParams["font.family"] = name
            break
    matplotlib.rcParams.update({
        "axes.unicode_minus": False, "figure.dpi": 110, "axes.spines.top": False,
        "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
        "axes.prop_cycle": matplotlib.cycler(color=[BLUE, ORANGE, BLUE_D, GREY, RED, BLUE_L]),
        "axes.grid": True, "grid.color": "#E6ECF5", "figure.facecolor": "white"})


def explain(short, found, meaning, action, use, read, method, n=None):
    """Chart explanation: short line always visible, full detail in an expander."""
    nn = f" (n={n})" if n else ""
    txt = f"> **สรุปสั้น{nn}:** {short}\n\n"
    txt += ("<details><summary><b>▶ ดูรายละเอียดการวิเคราะห์ (กดเปิด/ปิด)</b></summary>\n\n"
            f"**🔍 สิ่งที่พบ:** {found}\n\n**💡 ความหมาย:** {meaning}\n\n**🎯 ข้อเสนอแนะ:** {action}\n\n"
            f"- ใช้ดูอะไร: {use}\n- อ่านอย่างไร: {read}\n- วิเคราะห์ด้วยวิธี: {method}\n\n</details>")
    display(Markdown(txt))


def md(text):
    display(Markdown(text))
