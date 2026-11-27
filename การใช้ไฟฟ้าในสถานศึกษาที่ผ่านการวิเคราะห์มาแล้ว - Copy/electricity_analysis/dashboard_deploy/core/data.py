"""Data loading and shared filters. Only real columns of the dataset are used; nothing is invented."""
from pathlib import Path
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULTS = {"off_share_pct": 15.0, "evening_ratio": 3.0, "standby_x": 2.0, "small_rooms": 6, "impact_high": 2.0, "impact_mid": 0.5}


@st.cache_resource(show_spinner="กำลังโหลดข้อมูล...")
def load_all():
    """Load once per server process (read-only objects)."""
    df = pd.read_parquet(DATA / "electricity_clean.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["day"] = df["timestamp"].dt.normalize()
    for c in ["meter_id", "room_id", "building_id", "building_name", "room_type", "day_type", "day_type_th"]:
        df[c] = df[c].astype(str)
    out_log = pd.read_csv(DATA / "outliers_log.csv", encoding="utf-8-sig", parse_dates=["timestamp"])
    clean_log = pd.read_csv(DATA / "cleaning_log.csv", encoding="utf-8-sig")
    recon = pd.read_csv(DATA / "reconciliation.csv", encoding="utf-8-sig")
    dd = pd.read_csv(DATA / "data_dictionary_clean.csv", encoding="utf-8-sig")
    miss = pd.read_csv(DATA / "missing_data_table.csv", encoding="utf-8-sig")
    return {"df": df, "out_log": out_log, "clean_log": clean_log, "recon": recon, "dd": dd, "miss": miss}


@st.cache_resource(max_entries=8, show_spinner=False)
def filtered(buildings, types, d0, d1, daytypes):
    df = load_all()["df"]
    m = (df["building_name"].isin(buildings) & df["room_type"].isin(types) & df["day_type_th"].isin(daytypes)
         & (df["day"] >= pd.Timestamp(d0)) & (df["day"] <= pd.Timestamp(d1)))
    return df[m]


def _defaults():
    """Default value of every filter/setting (single source for first load and for the reset button)."""
    D = load_all()["df"]
    return {"f_building": sorted(D["building_name"].unique()), "f_type": sorted(D["room_type"].unique()),
            "f_dates": (D["day"].min().date(), D["day"].max().date()), "f_daytype": ["วันทำการ", "วันหยุด"],
            "mode": "เต็ม", "f_off_share": DEFAULTS["off_share_pct"], "f_evening": DEFAULTS["evening_ratio"]}


def _sync(store_key, widget_key):
    """on_change callback: copy what the user chose into the plain session value that every page reads."""
    st.session_state[store_key] = st.session_state[widget_key]


def _reset():
    """Reset button: restore the stored values and bump the version so all widgets are re-created from the defaults."""
    for k, v in _defaults().items():
        st.session_state[k] = v
    st.session_state["_flt_ver"] = st.session_state.get("_flt_ver", 0) + 1


def render_filters():
    """Filter panel drawn in app.py (main area, under the top menu).
    The values every page uses live in plain session keys (f_building, f_type, ...). The widgets are re-created from those values on every run
    (default=/value=/index= = stored value), so nothing depends on the widget's own state when the panel is collapsed or the page changes."""
    D = safe_load()["df"]
    b_all = sorted(D["building_name"].unique())
    t_all = sorted(D["room_type"].unique())
    d_min, d_max = D["day"].min().date(), D["day"].max().date()
    ss = st.session_state
    for k, v in _defaults().items():
        ss.setdefault(k, v)
    ver = ss.setdefault("_flt_ver", 0)
    wk = lambda name: f"w_{name}_{ver}"
    with st.expander("ตัวกรองข้อมูลและการตั้งค่า (ใช้กับทุกหน้า)", icon=":material/tune:"):
        a, b, c, e = st.columns([2, 2, 2, 1.4])
        a.multiselect("อาคาร", b_all, default=[x for x in ss["f_building"] if x in b_all], key=wk("building"), on_change=_sync, args=("f_building", wk("building")))
        b.multiselect("ประเภทห้อง", t_all, default=[x for x in ss["f_type"] if x in t_all], key=wk("type"), on_change=_sync, args=("f_type", wk("type")))
        c.date_input("ช่วงวันที่", value=ss["f_dates"], min_value=d_min, max_value=d_max, key=wk("dates"), on_change=_sync, args=("f_dates", wk("dates")))
        e.multiselect("ประเภทวัน", ["วันทำการ", "วันหยุด"], default=[x for x in ss["f_daytype"] if x in ("วันทำการ", "วันหยุด")], key=wk("daytype"), on_change=_sync, args=("f_daytype", wk("daytype")))
        g, h, i, j = st.columns([1.3, 2, 2, 1.3])
        g.radio("โหมดคำอธิบายใต้กราฟ", ["สั้น", "เต็ม"], index=["สั้น", "เต็ม"].index(ss["mode"]) if ss["mode"] in ("สั้น", "เต็ม") else 1, horizontal=True,
                key=wk("mode"), on_change=_sync, args=("mode", wk("mode")),
                help="สั้น = สรุปบรรทัดเดียว  เต็ม = มีรายละเอียด What / So What / Now What")
        h.slider("สัดส่วนไฟนอกเวลาที่ควรตรวจ (%) ค่าตั้งต้น", 5.0, 50.0, value=float(ss["f_off_share"]), step=1.0, key=wk("off"), on_change=_sync, args=("f_off_share", wk("off")),
                 help="ห้องที่ใช้ไฟนอกเวลามากกว่าเกณฑ์นี้ ถือว่าควรตรวจสอบเพิ่มเติม (ค่าตั้งต้น 15% ที่ทีมตั้งเอง ไม่ใช่มาตรฐานทางการ)")
        i.slider("ช่วงเย็นสูงกว่าช่วงอื่นนอกเวลา (เท่า) ค่าตั้งต้น", 1.5, 8.0, value=float(ss["f_evening"]), step=0.5, key=wk("eve"), on_change=_sync, args=("f_evening", wk("eve")),
                 help="ค่าเฉลี่ย 18:00-22:59 สูงกว่าชั่วโมงอื่นนอกเวลากี่เท่า (ค่าตั้งต้น 3 เท่า ที่ทีมตั้งเอง)")
        j.markdown("&nbsp;")
        j.button("ล้างตัวกรอง", icon=":material/restart_alt:", on_click=_reset, width="stretch")
        st.caption(f"ข้อมูลถึง: {D['timestamp'].max():%Y-%m-%d %H:%M} (ปี 2025, ข้อมูลจำลอง)")


def thresholds():
    return {"off_share_pct": float(st.session_state.get("f_off_share", DEFAULTS["off_share_pct"])),
            "evening_ratio": float(st.session_state.get("f_evening", DEFAULTS["evening_ratio"])),
            "standby_x": DEFAULTS["standby_x"], "small_rooms": DEFAULTS["small_rooms"],
            "impact_high": DEFAULTS["impact_high"], "impact_mid": DEFAULTS["impact_mid"]}


def get_ctx():
    """Return the filtered dataframe and filter description. Stops the page with a clear message when empty."""
    from core.ui import empty_state
    D = safe_load()
    df = D["df"]
    b = tuple(st.session_state.get("f_building", sorted(df["building_name"].unique())))
    t = tuple(st.session_state.get("f_type", sorted(df["room_type"].unique())))
    dr = st.session_state.get("f_dates", (df["day"].min().date(), df["day"].max().date()))
    if not isinstance(dr, (tuple, list)) or len(dr) == 0:
        dr = (df["day"].min().date(), df["day"].max().date())
    d0, d1 = (dr[0], dr[0]) if len(dr) == 1 else (dr[0], dr[1])
    dt = tuple(st.session_state.get("f_daytype", ["วันทำการ", "วันหยุด"]))
    d = filtered(b, t, d0, d1, dt)
    if len(d) == 0:
        empty_state()
    desc = {"อาคาร": ", ".join(b), "ประเภทห้อง": ", ".join(t), "ช่วงวันที่": f"{d0} ถึง {d1}", "ประเภทวัน": ", ".join(dt)}
    return {"d": d, "all": D, "desc": desc, "thr": thresholds(), "key": (b, t, d0, d1, dt)}



def safe_load():
    """Load the data; if the files are missing or unreadable show a plain-language message (never a code traceback) and stop."""
    try:
        return load_all()
    except Exception:
        st.error("ไม่สามารถโหลดไฟล์ข้อมูลได้ กรุณาตรวจสอบว่าโฟลเดอร์ data มีไฟล์ electricity_clean.parquet ครบ แล้วรีเฟรชหน้านี้ "
                 "ถ้ายังไม่ได้ ให้แจ้งผู้ดูแลระบบ", icon=":material/error:")
        st.stop()
