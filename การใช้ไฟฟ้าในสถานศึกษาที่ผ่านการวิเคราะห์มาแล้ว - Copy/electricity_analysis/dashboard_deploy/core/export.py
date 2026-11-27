"""Exports: everything shown on the dashboard can be downloaded (CSV / Excel), with the filters recorded for traceability."""
import io
import pandas as pd
import streamlit as st
from core.data import filtered
from core.analysis import room_table, problems

E = "energy_clean"

ROOM_COLS = {"room_id": "รหัสห้อง", "meter_id": "รหัสมิเตอร์", "building_name": "อาคาร", "room_type": "ประเภทห้อง", "area_m2": "พื้นที่ (ตร.ม.)",
             "ac_count": "จำนวนแอร์", "total_kwh": "ใช้ไฟรวม (kWh)", "mean_kwh_h": "เฉลี่ย kWh/ชม.", "off_kwh": "ไฟนอกเวลา (kWh)",
             "off_share_pct": "สัดส่วนไฟนอกเวลา (%)", "other_off_mean_kwh_h": "ฐานไฟนอกเวลา (kWh/ชม.)", "evening_ratio": "ช่วงเย็นเทียบช่วงอื่นนอกเวลา (เท่า)",
             "weekend_mean_kwh_h": "เฉลี่ยวันหยุด (kWh/ชม.)", "peak_kwh_h": "สูงสุดรายชั่วโมง (kWh)", "outlier_count": "ค่าผิดปกติ (จุด)",
             "pattern": "รูปแบบ", "flag_off_share": "เกินเกณฑ์ไฟนอกเวลา"}
PROB_COLS = {"id": "รหัส", "problem": "ปัญหา", "where": "ที่ไหน", "excess_kwh": "ส่วนเกินประมาณ (kWh)", "impact_pct": "ผลกระทบ (% ของไฟที่เลือก)",
             "certainty": "ความแน่นอน", "certainty_reason": "เหตุผลความแน่นอน", "severity": "ความรุนแรง", "action": "แนวทางแก้ไข",
             "owner": "ผู้รับผิดชอบ", "timeframe": "กรอบเวลา"}


def room_export(room):
    return room[list(ROOM_COLS)].rename(columns=ROOM_COLS).round(3)


def prob_export(p):
    return p[list(PROB_COLS)].rename(columns=PROB_COLS).round(3)


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_resource(max_entries=6, show_spinner=False)
def _excel(key, thr_items):
    d = filtered(*key)
    ctx = {"d": d, "key": key, "thr": dict(thr_items), "all": st.session_state.get("_all")}
    from core.data import load_all
    ctx["all"] = load_all()
    room = room_table(ctx)
    probs = problems(ctx, room)
    b, t, d0, d1, dt = key
    filt = pd.DataFrame({"รายการ": ["อาคาร", "ประเภทห้อง", "ช่วงวันที่", "ประเภทวัน", "จำนวนแถวที่เลือก", "ใช้ไฟรวม (kWh)", "หมายเหตุ"],
                         "ค่า": [", ".join(b), ", ".join(t), f"{d0} ถึง {d1}", ", ".join(dt), len(d), round(d[E].sum(), 1),
                                 "ข้อมูลจำลองปี 2025 ไม่มีอัตราค่าไฟ เกณฑ์ที่ตั้งเองเป็นค่าตั้งต้น"]})
    thr = pd.DataFrame({"เกณฑ์": list(dict(thr_items).keys()), "ค่า (ค่าตั้งต้นที่ตั้งเอง)": list(dict(thr_items).values())})
    bld = room.groupby("building_name").agg(ห้อง=("room_id", "count"), ใช้ไฟรวมkWh=("total_kwh", "sum"), ไฟนอกเวลาkWh=("off_kwh", "sum")).reset_index()
    bld["สัดส่วนไฟนอกเวลา%"] = 100 * bld["ไฟนอกเวลาkWh"] / bld["ใช้ไฟรวมkWh"]
    mon = d.groupby("month").agg(ใช้ไฟรวมkWh=(E, "sum"), อุณหภูมิเฉลี่ย=("temperature_c", "mean")).reset_index()
    hr = d.groupby(["day_type_th", "hour"])[E].mean().unstack(0).reset_index()
    out = d[d["flag_outlier"]][["timestamp", "meter_id", "room_id", "building_name", "room_type", "energy_kwh", "cell_median", "occupancy_people"]]
    out = out.rename(columns={"energy_kwh": "ค่าเดิม kWh", "cell_median": "ค่าปกติของช่วงเวลาเดียวกัน kWh"})
    A = ctx["all"]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        filt.to_excel(xw, sheet_name="เงื่อนไขการกรอง", index=False)
        thr.to_excel(xw, sheet_name="เกณฑ์ค่าตั้งต้น", index=False)
        prob_export(probs).to_excel(xw, sheet_name="ปัญหาและแนวทางแก้ไข", index=False)
        room_export(room).sort_values("สัดส่วนไฟนอกเวลา (%)", ascending=False).to_excel(xw, sheet_name="จัดอันดับห้อง", index=False)
        bld.round(2).to_excel(xw, sheet_name="สรุปอาคาร", index=False)
        mon.round(2).to_excel(xw, sheet_name="รายเดือน", index=False)
        hr.round(4).to_excel(xw, sheet_name="รายชั่วโมง", index=False)
        out.to_excel(xw, sheet_name="ค่าผิดปกติ", index=False)
        A["miss"].to_excel(xw, sheet_name="ข้อมูลที่ไม่มี", index=False)
        A["dd"].to_excel(xw, sheet_name="พจนานุกรมข้อมูล", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:60])
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
            ws.freeze_panes = "A2"
    return buf.getvalue()


def excel_report(ctx):
    return _excel(ctx["key"], tuple(sorted(ctx["thr"].items())))


def hourly_csv(ctx):
    cols = ["timestamp", "meter_id", "room_id", "building_name", "room_type", "day_type_th", "is_off_hours", "occupancy_people",
            "energy_kwh", "energy_clean", "flag_missing", "flag_negative", "flag_outlier", "temperature_c", "relative_humidity_percent"]
    return csv_bytes(ctx["d"][cols])
