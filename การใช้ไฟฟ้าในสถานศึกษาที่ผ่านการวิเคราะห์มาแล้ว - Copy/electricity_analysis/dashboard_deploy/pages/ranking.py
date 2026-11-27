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

banner("จัดอันดับการใช้ไฟ", "ใช้ไฟมากที่สุดที่ไหน: อาคาร ห้อง และเจาะลึกห้องในอาคารที่เลือก")
note_high_vs_waste()
tabs = st.tabs([":material/apartment: อาคารและห้อง"])
with tabs[0]:
    bld = room.groupby("building_name").agg(rooms=("room_id", "count"), total=("total_kwh", "sum")).sort_values("total", ascending=False)
    bld["share"] = 100 * bld["total"] / bld["total"].sum()
    top5 = room.nlargest(5, "total_kwh")
    ask("ห้องไหนใช้ไฟฟ้ามากที่สุด? (Top 3)", "leaderboard")
    rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"{fmt(r['total_kwh'])} kWh", "sub": f"{r['building_name']} | แอร์ {int(r['ac_count'])} เครื่อง"} for _, r in top5.head(3).iterrows()])
    c1, c2 = st.columns(2)
    with c1:
        ask("อาคารไหนใช้ไฟฟ้ามากที่สุด?", "apartment")
        f = go.Figure(go.Bar(y=bld.index[::-1], x=bld["total"][::-1], orientation="h", marker_color=NAVY,
                             text=[f"{fmt(v)} kWh ({s:.1f}%)" for v, s in zip(bld["total"][::-1], bld["share"][::-1])], textposition="outside"))
        style(f, 330, "kWh รวมในช่วงที่เลือก แยกตามอาคาร", legend=False); f.update_xaxes(range=[0, bld["total"].max() * 1.35], title="kWh")
        show(f, "ov_bld")
    with c2:
        ask("ห้องไหนใช้ไฟฟ้ามากที่สุด? (Top 5)", "meeting_room")
        f = go.Figure(go.Bar(y=(top5["room_id"] + " " + top5["room_type"])[::-1], x=top5["total_kwh"][::-1], orientation="h", marker_color=BLUE,
                             text=[fmt(v) for v in top5["total_kwh"][::-1]], textposition="outside"))
        style(f, 330, "kWh รวมในช่วงที่เลือก 5 ห้องสูงสุด", legend=False); f.update_xaxes(range=[0, top5["total_kwh"].max() * 1.2], title="kWh")
        show(f, "ov_top5")
    ask("เมื่อเลือกอาคาร ห้องไหนในอาคารนั้นใช้ไฟมากที่สุด?", "account_tree")
    sel = st.selectbox("เจาะลึก: เลือกอาคารเพื่อดูห้อง", list(bld.index), key="ov_drill_b")
    rr = room[room["building_name"] == sel].sort_values("total_kwh", ascending=False)
    f = go.Figure(go.Bar(x=rr["room_id"] + " " + rr["room_type"], y=rr["total_kwh"], marker_color=[AMBER if a == 3 else SKY for a in rr["ac_count"]],
                         text=[f"แอร์ {a}" for a in rr["ac_count"]], textposition="outside"))
    style(f, 330, f"ใน{sel} ห้องไหนใช้ไฟมากที่สุด? (สีเหลือง = แอร์ 3 เครื่อง)", legend=False); f.update_yaxes(title="kWh")
    show(f, "ov_drill")
    ac_top = top5["ac_count"].value_counts().to_dict()
    explain(
        short=f"{bld.index[0]} ใช้ไฟมากสุด {fmt(bld.iloc[0]['total'])} kWh ({bld.iloc[0]['share']:.1f}%) ห้องมากสุดคือ {top5.iloc[0]['room_id']} ({fmt(top5.iloc[0]['total_kwh'])} kWh)",
        found=f"อาคารสูงสุดกับต่ำสุดต่างกัน {100 * (bld['total'].max() / bld['total'].min() - 1):.1f}% (แต่ละอาคารจำนวนห้องที่เลือก: {', '.join(str(x) for x in sorted(set(bld['rooms'])))}) 5 ห้องสูงสุดมีเครื่องปรับอากาศ (เครื่อง:ห้อง) {ac_top} ในอาคาร{sel} ห้องสูงสุดคือ {rr.iloc[0]['room_id']}",
        meaning="ห้องที่ใช้ไฟมากมักมีเครื่องปรับอากาศหลายเครื่อง ไม่ได้แปลว่าผิดปกติเสมอไป ต้องดูควบคู่กับไฟนอกเวลา",
        action="ใช้อันดับนี้เป็นจุดเริ่ม แล้วดูแท็บ นอกเวลาและวันหยุด เพื่อหาห้องที่ควรตรวจสอบ",
        use="ตอบว่าใช้ไฟมากที่สุดที่ไหน", read="กราฟซ้ายอาคาร กราฟขวาห้อง กราฟล่างเจาะลึกห้องในอาคารที่เลือก", method="รวม kWh ตามอาคารและห้อง จัดอันดับ", n=N)

