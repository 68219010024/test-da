"""Dashboard page (generated from the former single main page)."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (ask, rank_cards, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.ui import note_high_vs_waste
from core.analysis import room_table, problems, within_corr, std_effects
from core.export import excel_report, prob_export, csv_bytes, room_export

E = "energy_clean"
MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

ctx = get_ctx()
d, thr = ctx["d"], ctx["thr"]
room = room_table(ctx)
probs = problems(ctx, room)
off = d["is_off_hours"]
total = float(d[E].sum())
N = len(room)

banner("ปัญหาที่พบและแนวทางแก้ไข", "เรียงตามความรุนแรง = ผลกระทบร่วมกับความแน่นอนว่าเป็นปัญหาจริง")
# ---------------- Problems and fixes (top of main page) ----------------
st.divider()
ask("ควรแก้อะไรก่อน และแก้อย่างไร?", "build_circle")
st.caption("เรียงตามความรุนแรง = ผลกระทบ (ส่วนเกินเทียบไฟที่เลือก) ร่วมกับความแน่นอนว่าเป็นปัญหาจริง")
criteria_note(thr)
note_high_vs_waste()
cnt = probs["severity"].value_counts()
st.markdown(f"พบ {len(probs)} ประเด็น: สูง {cnt.get('สูง', 0)} | กลาง {cnt.get('กลาง', 0)} | ต่ำ {cnt.get('ต่ำ', 0)}")
for _, r in probs.iterrows():
    with st.container(border=True):
        st.markdown(f"{SEV_BADGE[r['severity']]}  **{r['id']}  {r['problem']}**")
        a, b = st.columns(2)
        with a:
            st.markdown(f":material/location_on: **ที่ไหน:** {r['where']}")
            st.markdown(f":material/bolt: **ผลกระทบ:** ส่วนเกินที่ประมาณได้ {fmt(r['excess_kwh'])} kWh ({r['impact_pct']:.2f}% ของไฟที่เลือก)")
            st.markdown(f":material/verified: **ความแน่นอน:** {r['certainty']} ({r['certainty_reason']})")
        with b:
            st.markdown(f":material/build: **แนวทางแก้ไข:** {r['action']}")
            st.markdown(f":material/person: **ผู้รับผิดชอบ:** {r['owner']}  |  :material/schedule: **กรอบเวลา:** {r['timeframe']}")
st.caption("ส่วนเกินเป็นค่าประมาณเทียบกับค่าปกติของห้องอื่น ไม่ใช่ค่าที่วัดได้โดยตรง เกณฑ์เป็นค่าตั้งต้นที่ทีมตั้งเอง ข้อมูลไม่ระบุอุปกรณ์ จึงสรุปสาเหตุไม่ได้ ใช้คำว่า ควรตรวจสอบเพิ่มเติม")

ask("พื้นที่ไหนควรตรวจสอบก่อน?", "manage_search")
room["excess_kwh"] = room["evening_excess_kwh"] + room["baseline_excess_kwh"]
first = room[room["excess_kwh"] > 0].sort_values("excess_kwh", ascending=False).head(5)
if len(first) == 0:
    first = room.sort_values("off_share_pct", ascending=False).head(5)
rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"ส่วนเกินประมาณ {fmt(r['excess_kwh'])} kWh", "sub": f"{r['building_name']} | มิเตอร์ {r['meter_id']} | {r['pattern']}"} for _, r in first.head(3).iterrows()])
st.dataframe(first[["room_id", "meter_id", "building_name", "room_type", "pattern", "off_share_pct", "excess_kwh"]].rename(columns={
    "room_id": "ห้อง", "meter_id": "มิเตอร์", "building_name": "อาคาร", "room_type": "ประเภทห้อง", "pattern": "รูปแบบที่พบ",
    "off_share_pct": "ไฟนอกเวลา (% ของห้อง)", "excess_kwh": "ส่วนเกินประมาณ (kWh)"}),
    hide_index=True, width="stretch",
    column_config={"ไฟนอกเวลา (% ของห้อง)": st.column_config.NumberColumn(format="%.1f"), "ส่วนเกินประมาณ (kWh)": st.column_config.NumberColumn(format="%.0f")})


# ---------------- Export block ----------------
st.divider()
section("ส่งออกผลการวิเคราะห์", "download", "ไฟล์ตรงกับตัวกรองที่เลือกและบันทึกเงื่อนไขการกรองไว้ในไฟล์")
e1, e2, e3, e4 = st.columns(4)
e1.download_button("ปัญหาและแนวทางแก้ไข (CSV)", csv_bytes(prob_export(probs)), "problems_and_actions.csv", "text/csv", icon=":material/description:", width="stretch", key="dl_prob")
e2.download_button("จัดอันดับรายห้อง (CSV)", csv_bytes(room_export(room)), "room_ranking.csv", "text/csv", icon=":material/table_chart:", width="stretch", key="dl_room")
e3.download_button("รายงานสรุป (Excel หลายชีต)", excel_report(ctx), "electricity_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   icon=":material/summarize:", width="stretch", key="dl_xlsx")
e4.page_link("pages/export.py", label="ไฟล์อื่น ๆ ทั้งหมด", icon=":material/folder_open:", width="stretch")
