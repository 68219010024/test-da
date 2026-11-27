"""Overview page: answers the 4 key questions first (total, peak, top area, where to check), details in tabs."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (ask, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.ui import note_high_vs_waste
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

banner("ภาพรวมการใช้ไฟฟ้าในสถานศึกษา",
       "โจทย์: ค่าไฟสูงขึ้น ต้องการลดต้นทุนพลังงานและตรวจสอบพฤติกรรมการใช้ไฟที่ผิดปกติ (ข้อมูลจำลองปี 2025 ใช้เฉพาะคอลัมน์ที่มีจริง)")
st.caption(f"ตัวกรองที่ใช้: {ctx['desc']['ช่วงวันที่']} | {len(ctx['desc']['อาคาร'].split(', '))} อาคาร | {N} ห้อง | {fmt(len(d))} แถวรายชั่วโมง | หน่วย kWh (ไม่มีอัตราค่าไฟ จึงรายงานเป็นเงินไม่ได้)")
K = key_answers(ctx, room, probs)
peak_hour, off_share, n_check = K["peak_hour"], K["off_share"], K["n_check"]

# ---- the 4 questions that matter, answered first ----
k = st.columns(4)
k[0].metric("1. ใช้ไฟทั้งหมดเท่าไร (kWh)", fmt(total), delta=f"เฉลี่ย {fmt(total / N)} kWh ต่อห้อง", delta_arrow="off", delta_color="off", help=f"รวมทุกห้องในช่วงที่เลือก n={fmt(len(d))} แถว")
k[1].metric("2. ใช้ไฟสูงสุดเมื่อไร", f"{peak_hour:02d}:00", delta=f"เดือน {MONTHS[K['peak_month'] - 1]} | วันที่ {thai_date(K['peak_day'])}", delta_arrow="off", delta_color="off",
            help="ชั่วโมงที่มีค่าเฉลี่ย kWh ต่อห้องสูงสุด (เป็น kWh รายชั่วโมง ไม่ใช่ kW)")
k[2].metric("3. พื้นที่ใดใช้ไฟสูงสุด", K["top_room"]["room_id"], delta=f"{K['top_b']} สูงสุดระดับอาคาร ({K['top_b_share']:.1f}%)", delta_arrow="off", delta_color="off",
            help=f"ห้อง {K['top_room']['room_id']} ({K['top_room']['room_type']}) ใช้ไฟ {fmt(K['top_room']['total_kwh'])} kWh")
k[3].metric("4. พื้นที่ใดควรตรวจสอบเพิ่มเติม", f"{n_check} จาก {N} ห้อง", delta=f"ไฟนอกเวลา {off_share:.1f}% ของทั้งหมด", delta_arrow="off", delta_color="off",
            help=f"สัดส่วนไฟนอกเวลาของห้องเกิน {thr['off_share_pct']:.0f}% (เกณฑ์คัดกรองเบื้องต้นที่ทีมตั้งเอง ปรับได้ที่ตัวกรองด้านบน)")

section("คำตอบสำคัญจากข้อมูล", "lightbulb", "คำนวณจากข้อมูลที่เลือกโดยอัตโนมัติ (ดูเวอร์ชันพร้อมพูดนำเสนอที่หน้า สรุปผลการวิเคราะห์)")
with st.container(border=True):
    for icon, q, a in K["qa"]:
        st.markdown(f":material/{icon}: **{q}**  \n:material/check_circle: {a}")
criteria_note(thr, detail=False)
note_high_vs_waste()

# ---- 4 simple charts, always visible ----
st.divider()
section("กราฟสำคัญ 4 ใบ", "bar_chart", "แต่ละใบตอบ 1 คำถาม อ่านได้จากความยาวของแท่ง")
g1, g2 = st.columns(2)
with g1:
    ask("ห้องไหนใช้ไฟมากที่สุด?", "meeting_room")
    t5 = K["rooms_sorted"].head(5)
    f = go.Figure(go.Bar(y=(t5["room_id"] + " " + t5["room_type"])[::-1], x=t5["total_kwh"][::-1], orientation="h", marker_color=BLUE, text=[fmt(v) for v in t5["total_kwh"][::-1]], textposition="outside"))
    style(f, 300, "5 ห้องที่ใช้ไฟมากที่สุด (kWh)", legend=False); f.update_xaxes(range=[0, t5["total_kwh"].max() * 1.2], title="kWh")
    show(f, "ov_top5")
    st.caption(f"อันดับ 1 คือ {t5.iloc[0]['room_id']} ({t5.iloc[0]['room_type']}) ใช้ไฟ {fmt(t5.iloc[0]['total_kwh'])} kWh")
with g2:
    ask("ประเภทห้องไหนใช้ไฟต่อห้องมากที่สุด?", "category")
    rt = room.groupby("room_type").agg(total=("total_kwh", "sum"), rooms=("room_id", "count"))
    rt["per_room"] = rt["total"] / rt["rooms"]
    rt = rt.sort_values("per_room", ascending=False)
    f = go.Figure(go.Bar(y=rt.index[::-1], x=rt["per_room"][::-1], orientation="h", marker_color=NAVY, text=[f"{fmt(v)} ({n} ห้อง)" for v, n in zip(rt["per_room"][::-1], rt["rooms"][::-1])], textposition="outside"))
    style(f, 300, "ไฟเฉลี่ยต่อห้อง แยกประเภทห้อง (kWh)", legend=False); f.update_xaxes(range=[0, rt["per_room"].max() * 1.3], title="kWh ต่อห้อง")
    show(f, "ov_type")
    st.caption(f"{rt.index[0]} ใช้ไฟต่อห้องมากที่สุด ({fmt(rt.iloc[0]['per_room'])} kWh) ตัวเลขในวงเล็บคือจำนวนห้อง")
g3, g4 = st.columns(2)
with g3:
    ask("วันหยุดใช้ไฟต่างจากวันทำการแค่ไหน?", "weekend")
    if K["we_delta"] is None:
        st.info("ตัวกรองที่เลือกไม่มีทั้งวันทำการและวันหยุด เลือกประเภทวันทั้งสองแบบเพื่อเปรียบเทียบ", icon=":material/info:")
    else:
        f = go.Figure(go.Bar(x=["วันทำการ", "วันหยุด"], y=[K["wd_mean"], K["we_mean"]], marker_color=[BLUE, AMBER], text=[f"{K['wd_mean']:.2f}", f"{K['we_mean']:.2f}"], textposition="outside"))
        style(f, 300, "ไฟเฉลี่ยต่อห้องต่อชั่วโมง (kWh)", legend=False); f.update_yaxes(range=[0, K["wd_mean"] * 1.25], title="kWh ต่อห้องต่อชั่วโมง")
        show(f, "ov_wk")
        st.caption(f"วันหยุดใช้ไฟเฉลี่ยต่ำกว่าวันทำการ {-K['we_delta']:.0f}%")
with g4:
    ask("ห้องไหนใช้ไฟนอกเวลามากที่สุด?", "dark_mode")
    ro = K["off_rank"].head(5)
    f = go.Figure(go.Bar(y=(ro["room_id"] + " " + ro["room_type"])[::-1], x=ro["off_share_pct"][::-1], orientation="h", marker_color=[RED if v > thr["off_share_pct"] else SKY for v in ro["off_share_pct"][::-1]],
                         text=[f"{v:.1f}%" for v in ro["off_share_pct"][::-1]], textposition="outside"))
    f.add_vline(x=thr["off_share_pct"], line_dash="dash", line_color=SLATE)
    style(f, 300, f"สัดส่วนไฟนอกเวลา (เส้นประ = เกณฑ์คัดกรองเบื้องต้น {thr['off_share_pct']:.0f}%)", legend=False)
    f.update_xaxes(range=[0, max(ro["off_share_pct"].max() * 1.25, thr["off_share_pct"] * 1.3)], title="% ของไฟทั้งหมดของห้อง")
    show(f, "ov_off5")
    st.caption(f"แท่งสีแดงคือห้องที่ควรตรวจสอบเพิ่มเติม (ใช้ไฟนอกเวลาเกินเกณฑ์) อันดับ 1 คือ {ro.iloc[0]['room_id']} {ro.iloc[0]['off_share_pct']:.1f}%")

# ---- details in tabs ----
st.divider()
section("ดูรายละเอียดเพิ่มเติม", "insights", "เริ่มจากเวลา แล้วไปดูว่าที่ไหน และปัญหาที่ควรทำต่อ")
tabs = st.tabs([":material/schedule: เมื่อไรใช้ไฟ", ":material/leaderboard: ที่ไหนใช้ไฟ", ":material/build_circle: ปัญหาที่ควรทำต่อ"])

with tabs[0]:
    mo = d.groupby("month")[E].sum()
    prof = d.groupby(["day_type_th", "hour"])[E].mean().unstack(0)
    c1, c2 = st.columns(2)
    with c1:
        ask("เดือนไหนใช้ไฟมากที่สุด?", "calendar_month")
        col = [AMBER if m == mo.idxmax() else BLUE for m in mo.index]
        f = go.Figure(go.Bar(x=[MONTHS[m - 1] for m in mo.index], y=mo.values, marker_color=col, hovertemplate="%{x}: %{y:,.0f} kWh<extra></extra>"))
        style(f, 330, "ใช้ไฟรายเดือน (แท่งสีเหลือง = เดือนสูงสุด)", legend=False); f.update_yaxes(title="kWh")
        show(f, "ov_month")
    with c2:
        ask("ชั่วโมงไหนใช้ไฟมาก และวันหยุดต่างจากวันทำการอย่างไร?", "schedule")
        f = go.Figure()
        for name, color in [("วันทำการ", BLUE), ("วันหยุด", AMBER)]:
            if name in prof.columns:
                f.add_scatter(x=prof.index, y=prof[name], name=name, line=dict(color=color, width=3))
        style(f, 330, "ชั่วโมงไหนใช้ไฟมาก (เฉลี่ยต่อห้อง)"); f.update_xaxes(title="ชั่วโมง", dtick=2); f.update_yaxes(title="kWh ต่อห้องต่อชั่วโมง")
        show(f, "ov_prof")
    pk = int(mo.idxmax()); lo = int(mo.idxmin()); two = len(mo) > 1
    sched = (d["day_type"] == "weekday") & d["hour"].between(8, 16)
    share_sched = 100 * d.loc[sched, E].sum() / total
    explain(
        short=f"ใช้ไฟสูงสุดเดือน {MONTHS[pk - 1]} ({fmt(mo.max())} kWh)" + (f" ต่ำสุดเดือน {MONTHS[lo - 1]} ({fmt(mo.min())} kWh)" if two else "") + f" และสูงสุดชั่วโมง {peak_hour:02d}:00 ข้อมูลมีปีเดียว",
        found=f"ช่วง 08:00-16:59 วันจันทร์-ศุกร์ใช้ไฟ {share_sched:.1f}% ของไฟที่เลือก" + (f" เดือนสูงสุดกับต่ำสุดต่างกัน {100 * (mo.max() / mo.min() - 1):.1f}%" if two else "") + f" ไฟนอกเวลา {off_share:.1f}% ของทั้งหมด",
        meaning="พบแนวโน้มที่เดือนอากาศร้อนใช้ไฟมากกว่า แต่ข้อมูลมีปีเดียว จึงยืนยันไม่ได้ว่า ค่าไฟสูงขึ้นเมื่อเทียบกับปีก่อน เวลาทำการกินไฟมากที่สุด แต่ช่วงนอกเวลาเป็นส่วนที่ลดได้โดยไม่กระทบการเรียนการสอน",
        action="ขอข้อมูลปีก่อนหน้าเพื่อเทียบแนวโน้มจริง (ดูหน้า ข้อมูลที่ไม่มี) และเริ่มตรวจไฟนอกเวลาโดยไม่ต้องรอฤดูกาล",
        use="ดูว่าใช้ไฟมากเมื่อไร", read="กราฟซ้ายคือยอดรวมรายเดือน กราฟขวาเส้นสีน้ำเงินคือวันทำการ เส้นสีเหลืองคือวันหยุด", method="รวม kWh รายเดือน และเฉลี่ย kWh ต่อห้องต่อชั่วโมง แยกวันทำการ/วันหยุด", n=len(d))

with tabs[1]:
    bld = room.groupby("building_name").agg(rooms=("room_id", "count"), total=("total_kwh", "sum")).sort_values("total", ascending=False)
    bld["share"] = 100 * bld["total"] / bld["total"].sum()
    ask("อาคารไหนใช้ไฟฟ้ามากที่สุด?", "apartment")
    f = go.Figure(go.Bar(y=bld.index[::-1], x=bld["total"][::-1], orientation="h", marker_color=NAVY,
                         text=[f"{fmt(v)} kWh ({s:.1f}%)" for v, s in zip(bld["total"][::-1], bld["share"][::-1])], textposition="outside"))
    style(f, 340, "อาคารที่ใช้ไฟมากที่สุด", legend=False); f.update_xaxes(range=[0, bld["total"].max() * 1.35], title="kWh")
    show(f, "ov_bld")
    explain(
        short=f"{bld.index[0]} ใช้ไฟมากสุด {fmt(bld.iloc[0]['total'])} kWh ({bld.iloc[0]['share']:.1f}%) อาคารสูงสุดต่างจากต่ำสุด {100 * (bld['total'].max() / bld['total'].min() - 1):.1f}%",
        found=f"แต่ละอาคารมีจำนวนห้องที่เลือก: {', '.join(str(x) for x in sorted(set(bld['rooms'])))} ห้อง การเปรียบเทียบอาคารจึงเทียบกันได้ตรง ๆ เมื่อเลือกทุกอาคาร",
        meaning="อาคารที่ใช้ไฟมากมักมีห้องที่มีเครื่องปรับอากาศหลายเครื่อง ไม่ได้แปลว่าผิดปกติเสมอไป ต้องดูควบคู่กับไฟนอกเวลา",
        action="ไปหน้า จัดอันดับ เพื่อดูห้อง Top 5 และเจาะลึกห้องในอาคาร แล้วไปหน้า นอกเวลาและวันหยุด เพื่อหาห้องที่ควรตรวจสอบเพิ่มเติม",
        use="ดูว่าอาคารไหนใช้ไฟมากที่สุด", read="แท่งยาวคือใช้ไฟมาก ตัวเลขท้ายแท่งคือ kWh และสัดส่วนของทั้งหมด", method="รวม kWh ทั้งปีตามอาคาร", n=N)

with tabs[2]:
    cnt = probs["severity"].value_counts()
    with st.container(border=True):
        st.markdown(":material/build_circle: **สรุปปัญหาที่พบ**")
        st.markdown(f"ประเด็นทั้งหมด {len(probs)}: สูง {cnt.get('สูง', 0)} | กลาง {cnt.get('กลาง', 0)} | ต่ำ {cnt.get('ต่ำ', 0)}")
        for _, r in probs.head(3).iterrows():
            st.markdown(f"- {r['id']} {r['problem']} ({r['severity']}) : {r['where']}")
        st.page_link("pages/problems.py", label="ดูปัญหาและแนวทางแก้ไขทั้งหมด", icon=":material/arrow_forward:")
        st.page_link("pages/summary.py", label="สรุปผลการวิเคราะห์ (สำหรับนำเสนอ)", icon=":material/target:")
        st.page_link("pages/stats.py", label="ผลวิเคราะห์สถิติเบื้องต้น", icon=":material/calculate:")
