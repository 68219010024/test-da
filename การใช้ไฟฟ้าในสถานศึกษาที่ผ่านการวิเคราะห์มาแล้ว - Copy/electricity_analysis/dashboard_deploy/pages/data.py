"""Data table and data dictionary page."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (ask, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.analysis import room_table, problems, within_corr, std_effects, key_answers, thai_date
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

banner("ตารางข้อมูลและพจนานุกรมข้อมูล", "ดูข้อมูลที่ใช้วิเคราะห์ตามตัวกรอง และความหมายของทุกคอลัมน์ (ตรวจสอบย้อนกลับได้)")
A = ctx["all"]
st.caption(f"ข้อมูลที่เลือก {fmt(len(d))} แถว จากทั้งหมด {fmt(len(A['df']))} แถว (หลังทำความสะอาด) | ค่าเดิมก่อนทำความสะอาดอยู่ในคอลัมน์ energy_kwh และป้ายกำกับ flag_*")
tabs = st.tabs([":material/table_view: ตารางข้อมูล", ":material/menu_book: พจนานุกรมข้อมูล"])
with tabs[0]:
    ask("ข้อมูลที่ใช้วิเคราะห์หน้าตาเป็นอย่างไร?", "table_view")
    default_cols = ["timestamp", "building_name", "room_id", "room_type", "day_type_th", "is_off_hours", "occupancy_people", "air_conditioner_count", "energy_kwh", "energy_clean", "temperature_c", "relative_humidity_percent"]
    cols = st.multiselect("เลือกคอลัมน์ที่จะแสดง", list(d.columns), default=default_cols, key="dt_cols")
    mode = st.radio("แสดงแถว", ["1,000 แถวแรกตามเวลา", "1,000 แถวที่ใช้ไฟสูงสุด", "เฉพาะแถวที่ถูกติดป้าย (ว่าง ติดลบ ผิดปกติ)"], horizontal=True, key="dt_mode")
    if not cols:
        st.info("เลือกอย่างน้อย 1 คอลัมน์เพื่อแสดงตาราง", icon=":material/info:")
    else:
        if mode.startswith("1,000 แถวแรก"):
            view = d.sort_values("timestamp").head(1000)
        elif mode.startswith("1,000 แถวที่ใช้ไฟ"):
            view = d.nlargest(1000, "energy_clean")
        else:
            view = d[d["flag_missing"] | d["flag_negative"] | d["flag_outlier"]]
        if len(view) == 0:
            st.info("ไม่พบแถวที่ถูกติดป้ายในตัวกรองที่เลือก", icon=":material/info:")
        else:
            st.dataframe(view[cols], hide_index=True, width="stretch", height=420)
            st.caption(f"แสดง {fmt(len(view))} แถว จาก {fmt(len(d))} แถวที่เลือก ดาวน์โหลดข้อมูลทั้งหมดได้ที่เมนู ข้อมูลและส่งออก > ส่งออกข้อมูล")
with tabs[1]:
    ask("แต่ละคอลัมน์หมายถึงอะไร หน่วยอะไร?", "menu_book")
    dd = A["dd"].rename(columns={"column": "คอลัมน์", "description": "คำอธิบาย", "type": "ชนิด", "unit": "หน่วย", "example": "ตัวอย่างค่า"})
    st.dataframe(dd, hide_index=True, width="stretch", height=520)
    with st.expander("ดูที่มาและข้อจำกัดของข้อมูล", icon=":material/info:"):
        st.markdown("- ข้อมูลจำลองปี 2025: 5 อาคาร 40 ห้อง 40 มิเตอร์ บันทึกรายชั่วโมง ไม่มีข้อมูลบุคคลหรือสถานศึกษาจริง\n"
                    "- วันที่เป็นปี ค.ศ. เวลาไทย มิเตอร์วัดทั้งห้อง จึงแยกอุปกรณ์ไม่ได้\n"
                    "- ไม่มีอัตราค่าไฟ ข้อมูลปีก่อน ปฏิทินวันหยุด และตารางการใช้ห้อง (ดูหน้า ข้อมูลที่ไม่มี)")
