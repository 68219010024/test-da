"""Summary page for presenting to judges: six key findings, every number computed from the selected data."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (ask, rank_cards, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.ui import note_high_vs_waste
from core.analysis import room_table, problems, within_corr, std_effects, key_answers, MONTHS as _M, thai_date
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

banner("สรุปผลการวิเคราะห์", "สำหรับนำเสนอกรรมการ: 6 เรื่องสำคัญจากข้อมูลจริง ตัวเลขทุกตัวคำนวณจากข้อมูลที่เลือกโดยอัตโนมัติ (เปลี่ยนตามตัวกรองด้านบน)")
K = key_answers(ctx, room, probs)
O = K["out"]
st.caption(f"อ่านจากข้อมูล {fmt(len(d))} แถวรายชั่วโมง | {N} ห้อง | {ctx['desc']['ช่วงวันที่']} | หน่วย kWh")

section("คำตอบสำคัญจากข้อมูล", "lightbulb", "คำตอบสั้นสำหรับตอบกรรมการ")
with st.container(border=True):
    for icon, q, a in K["qa"]:
        st.markdown(f":material/{icon}: **{q}**  \n:material/check_circle: {a}")

# ---------------- 1. where ----------------
st.divider()
with st.container(border=True):
    ask("ใช้ไฟมากที่สุดที่ไหน?", "leaderboard")
    top5 = K["rooms_sorted"].head(5)
    ac_top = top5["ac_count"].value_counts().to_dict()
    same_ac = len(ac_top) == 1
    st.markdown(f"> :material/record_voice_over: **พูดนำเสนอ:** “จากข้อมูลทั้งหมด พบว่าพื้นที่ที่มีการใช้ไฟฟ้าสูงที่สุดคือ {K['top_b']} ใช้ไฟ {fmt(K['top_b_kwh'])} kWh คิดเป็น {K['top_b_share']:.1f}% ของไฟที่เลือก "
                f"และห้องที่ใช้ไฟมากที่สุดคือ {K['top_room']['room_id']} ({K['top_room']['room_type']}) {fmt(K['top_room']['total_kwh'])} kWh” "
                + (f"5 ห้องที่ใช้ไฟมากที่สุดล้วนมีแอร์ {list(ac_top)[0]} เครื่อง จึงไม่ได้แปลว่าผิดปกติเสมอไป" if same_ac else f"(5 ห้องสูงสุดมีแอร์ (เครื่อง:ห้อง) {ac_top})"))
    a, b = st.columns(2)
    with a:
        st.markdown("**อาคาร Top 3**")
        rank_cards([{"label": n, "value": f"{fmt(v)} kWh", "sub": f"{100 * v / total:.1f}% ของไฟที่เลือก | {int((room['building_name'] == n).sum())} ห้อง"} for n, v in K["bld"].head(3).items()])
    with b:
        st.markdown("**ห้อง Top 3**")
        rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"{fmt(r['total_kwh'])} kWh", "sub": f"{r['building_name']} | แอร์ {int(r['ac_count'])} เครื่อง"} for _, r in K["rooms_sorted"].head(3).iterrows()])
    note_high_vs_waste()
    with st.expander("ดูวิธีวิเคราะห์", icon=":material/functions:"):
        st.markdown("รวมพลังงาน (kWh) ที่ผ่านการทำความสะอาดแล้วของทุกชั่วโมงในช่วงที่เลือก แยกตามอาคารและห้อง แล้วเรียงจากมากไปน้อย (ค่าผิดปกติถูกแทนด้วยค่าปกติของช่วงเวลาเดียวกัน ค่าเดิมเก็บไว้ในตารางค่าผิดปกติ) "
                    "ข้อมูลเป็นพลังงานรายชั่วโมง (kWh) ไม่ใช่ค่ากำลังไฟ (kW) และไม่มีอัตราค่าไฟ จึงรายงานเป็นเงินบาทไม่ได้")

# ---------------- 2. when ----------------
with st.container(border=True):
    ask("ช่วงเวลาใดใช้ไฟสูงที่สุด?", "schedule")
    sched = (d["day_type"] == "weekday") & d["hour"].between(8, 16)
    share_sched = 100 * d.loc[sched, E].sum() / total
    st.markdown(f"> :material/record_voice_over: **พูดนำเสนอ:** “จากการวิเคราะห์ พบว่าช่วงเวลาที่มีการใช้ไฟฟ้าสูงที่สุดคือชั่วโมง {K['peak_hour']:02d}:00 เดือนที่ใช้ไฟสูงสุดคือ {_M[K['peak_month'] - 1]} "
                f"และวันที่ใช้ไฟรวมสูงสุดคือ {thai_date(K['peak_day'])} ({fmt(K['peak_day_kwh'])} kWh)” ช่วง 08:00-16:59 วันจันทร์-ศุกร์ใช้ไฟ {share_sched:.1f}% ของไฟที่เลือก")
    m = st.columns(3)
    m[0].metric("ชั่วโมงสูงสุด", f"{K['peak_hour']:02d}:00", delta=f"เฉลี่ย {K['peak_hour_val']:.2f} kWh ต่อห้อง", delta_arrow="off", delta_color="off")
    m[1].metric("เดือนสูงสุด", _M[K["peak_month"] - 1], delta=f"{fmt(K['peak_month_kwh'])} kWh", delta_arrow="off", delta_color="off")
    m[2].metric("วันสูงสุด", thai_date(K["peak_day"]), delta=f"{fmt(K['peak_day_kwh'])} kWh", delta_arrow="off", delta_color="off")
    hm = K["hour_mean"]
    f = go.Figure(go.Bar(x=hm.index, y=hm.values, marker_color=[AMBER if h == K["peak_hour"] else BLUE for h in hm.index], hovertemplate="%{x}:00 = %{y:.2f} kWh<extra></extra>"))
    style(f, 300, "ชั่วโมงไหนใช้ไฟมากที่สุด? (แท่งสีเหลือง = สูงสุด)", legend=False); f.update_xaxes(title="ชั่วโมง", dtick=2); f.update_yaxes(title="kWh ต่อห้องต่อชั่วโมง")
    show(f, "sm_hour")
    with st.expander("ดูวิธีวิเคราะห์", icon=":material/functions:"):
        st.markdown("เฉลี่ย kWh ต่อห้องต่อชั่วโมง แยกตามชั่วโมงของวัน หาชั่วโมงที่สูงสุด รวม kWh รายวัน/รายเดือนเพื่อหาวันและเดือนสูงสุด ข้อมูลเป็น kWh รายชั่วโมง จึงบอกค่ากำลังไฟสูงสุด (kW) ไม่ได้ "
                    "ข้อมูลมีปีเดียว จึงยืนยันไม่ได้ว่าเดือนที่สูงเป็นฤดูกาลหรือการเพิ่มขึ้นจริง")

# ---------------- 3. off-hours ----------------
with st.container(border=True):
    ask("พื้นที่ไหนควรตรวจสอบเรื่องการใช้ไฟนอกเวลา?", "dark_mode")
    ro = K["off_rank"].head(5)
    best = ro.iloc[0]
    st.markdown(f"> :material/record_voice_over: **พูดนำเสนอ:** “พื้นที่ที่ควรตรวจสอบเพิ่มเติมเป็นอันดับแรกคือ {best['room_id']} ({best['room_type']}, {best['building_name']}) "
                f"ใช้ไฟนอกเวลา {best['off_share_pct']:.1f}% ของไฟทั้งหมดของห้อง พื้นที่นี้มีการใช้ไฟฟ้าสูงในช่วงนอกเวลาการใช้งาน จึงควรตรวจสอบรูปแบบการใช้งานและอุปกรณ์เพิ่มเติม” "
                f"มี {K['n_check']} จาก {N} ห้องที่เกินเกณฑ์คัดกรอง")
    rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"ไฟนอกเวลา {r['off_share_pct']:.1f}% ของไฟห้อง", "sub": f"{r['building_name']} | {r['pattern']}"} for _, r in ro.head(3).iterrows()])
    f = go.Figure(go.Bar(y=(ro["room_id"] + " " + ro["room_type"])[::-1], x=ro["off_share_pct"][::-1], orientation="h", marker_color=[RED if v > thr["off_share_pct"] else SKY for v in ro["off_share_pct"][::-1]],
                         text=[f"{v:.1f}%" for v in ro["off_share_pct"][::-1]], textposition="outside"))
    f.add_vline(x=thr["off_share_pct"], line_dash="dash", line_color=SLATE)
    style(f, 300, f"5 ห้องที่ใช้ไฟนอกเวลาสูงที่สุด (เส้นประ = เกณฑ์คัดกรองเบื้องต้น {thr['off_share_pct']:.0f}%)", legend=False)
    f.update_xaxes(range=[0, max(ro["off_share_pct"].max() * 1.25, thr["off_share_pct"] * 1.3)], title="% ของไฟทั้งหมดของห้อง")
    show(f, "sm_off")
    criteria_note(thr, detail=False)
    note_high_vs_waste()
    with st.expander("ดูวิธีวิเคราะห์", icon=":material/functions:"):
        st.markdown("นอกเวลา = ชั่วโมงที่จำนวนคนในห้องเป็น 0 (ตรงกับ 08:00-16:59 วันจันทร์-ศุกร์ในข้อมูล) สัดส่วนไฟนอกเวลา = kWh นอกเวลา / kWh ทั้งหมดของห้องนั้น ใช้นิยามเดียวกันทุกห้อง ข้อมูลไม่ระบุอุปกรณ์ จึงสรุปสาเหตุไม่ได้ ควรตรวจสอบเพิ่มเติม")

# ---------------- 4. weekday vs weekend ----------------
with st.container(border=True):
    ask("วันทำการกับวันหยุดต่างกันอย่างไร และวันหยุดพื้นที่ไหนยังใช้ไฟสูง?", "weekend")
    if K["we_delta"] is None:
        st.info("ตัวกรองที่เลือกไม่มีทั้งวันทำการและวันหยุด เลือกประเภทวัน วันทำการ และวันหยุด ที่ตัวกรองด้านบน เพื่อเปรียบเทียบ", icon=":material/info:")
    else:
        wr = K["we_rank"]
        st.markdown(f"> :material/record_voice_over: **พูดนำเสนอ:** “เมื่อนำข้อมูลมาเปรียบเทียบ พบว่าวันทำการใช้ไฟเฉลี่ย {K['wd_mean']:.2f} kWh ต่อห้องต่อชั่วโมง ส่วนวันหยุด {K['we_mean']:.2f} kWh ต่ำกว่า {-K['we_delta']:.0f}% "
                    f"แต่ในวันหยุดห้อง {wr.iloc[0]['room_id']} ({wr.iloc[0]['room_type']}) ยังใช้ไฟสูงสุด {wr.iloc[0]['weekend_mean_kwh_h']:.2f} kWh ต่อชั่วโมง” (วันหยุดในข้อมูลคือเสาร์-อาทิตย์ ไม่มีปฏิทินนักขัตฤกษ์)")
        a, b = st.columns([2, 3])
        with a:
            f = go.Figure(go.Bar(x=["วันทำการ", "วันหยุด"], y=[K["wd_mean"], K["we_mean"]], marker_color=[BLUE, AMBER], text=[f"{K['wd_mean']:.2f}", f"{K['we_mean']:.2f}"], textposition="outside"))
            style(f, 300, "วันหยุดใช้ไฟต่างจากวันทำการเท่าไร?", legend=False); f.update_yaxes(range=[0, K["wd_mean"] * 1.25], title="kWh ต่อห้องต่อชั่วโมง")
            show(f, "sm_wk")
        with b:
            st.markdown("**วันหยุด ห้องที่ยังใช้ไฟสูง Top 3**")
            rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"{r['weekend_mean_kwh_h']:.2f} kWh ต่อชั่วโมง", "sub": r["building_name"]} for _, r in wr.head(3).iterrows()])
        with st.expander("ดูวิธีวิเคราะห์", icon=":material/functions:"):
            st.markdown(f"เฉลี่ย kWh ต่อห้องต่อชั่วโมง แยกวันทำการ (จันทร์-ศุกร์) กับวันหยุด (เสาร์-อาทิตย์) ส่วนต่าง = (วันหยุด / วันทำการ - 1) x 100 วันหยุดคิดเป็น {K['we_share']:.1f}% ของไฟที่เลือก")

# ---------------- 5. factors ----------------
with st.container(border=True):
    ask("ปัจจัยไหนมีความสัมพันธ์กับการใช้ไฟมากที่สุด?", "thermostat")
    occ = d[~off]
    tb_ = occ.assign(tb=pd.cut(occ["temperature_c"], [0, 28, 30, 32, 34, 40], labels=["ไม่เกิน 28", "28-30", "30-32", "32-34", "เกิน 34"])).groupby("tb", observed=True)[E].agg(["mean", "size"])
    ac_ = occ.groupby("air_conditioner_count").agg(m=(E, "mean"), rooms=("room_id", "nunique"))
    if len(occ) < 200 or len(ac_) < 2 or len(tb_) < 2:
        st.info("ข้อมูลช่วงมีคนในตัวกรองนี้น้อยเกินไปสำหรับเปรียบเทียบ ขยายช่วงวันที่หรือเลือกประเภทวัน วันทำการ", icon=":material/info:")
    else:
        ratio = float(ac_["m"].iloc[-1] / ac_["m"].iloc[0]); pct = 100 * float(tb_["mean"].iloc[-1] / tb_["mean"].iloc[0] - 1)
        bigger = "จำนวนแอร์" if (ratio - 1) > pct / 100 else "อากาศร้อน"
        st.markdown(f"> :material/record_voice_over: **พูดนำเสนอ:** “จากข้อมูลพบว่า ห้องที่มีแอร์ {int(ac_.index[-1])} เครื่องใช้ไฟมากกว่าห้องที่มีแอร์ {int(ac_.index[0])} เครื่องประมาณ {ratio:.1f} เท่า "
                    f"และช่วงที่อากาศ{tb_.index[-1]}องศาใช้ไฟมากกว่าช่วงที่อากาศ{tb_.index[0]}องศาประมาณ {pct:.0f}% ในสองอย่างนี้ {bigger}มีความสัมพันธ์กับการใช้ไฟมากกว่า” "
                    "ผลนี้เป็นความสัมพันธ์ ยังไม่ได้พิสูจน์ว่าเป็นสาเหตุโดยตรง")
        a1, a2 = st.columns(2)
        with a1:
            f = go.Figure(go.Bar(x=[f"แอร์ {int(k)} เครื่อง" for k in ac_.index], y=ac_["m"], marker_color=NAVY, text=[f"{v:.2f} ({int(n)} ห้อง)" for v, n in zip(ac_["m"], ac_["rooms"])], textposition="outside"))
            style(f, 300, "จำนวนแอร์ต่างกัน ใช้ไฟต่างกันแค่ไหน? (ช่วงมีคน)", legend=False); f.update_yaxes(range=[0, ac_["m"].max() * 1.25], title="kWh ต่อห้องต่อชั่วโมง")
            show(f, "sm_ac")
        with a2:
            f = go.Figure(go.Bar(x=list(tb_.index.astype(str)), y=tb_["mean"], marker_color=AMBER, text=[f"{v:.2f}" for v in tb_["mean"]], textposition="outside"))
            style(f, 300, "อากาศร้อนขึ้น ใช้ไฟต่างกันแค่ไหน? (ช่วงมีคน)", legend=False); f.update_xaxes(title="อุณหภูมิภายนอก (องศา)"); f.update_yaxes(range=[0, tb_["mean"].max() * 1.25], title="kWh ต่อห้องต่อชั่วโมง")
            show(f, "sm_tb")
        with st.expander("ดูวิธีวิเคราะห์", icon=":material/functions:"):
            st.markdown(f"เฉลี่ย kWh ต่อห้องต่อชั่วโมงเฉพาะช่วงที่มีคน (n={fmt(len(occ))} ชั่วโมง) แยกตามจำนวนแอร์ และตามช่วงอุณหภูมิ แล้วเทียบกลุ่มแรกกับกลุ่มสุดท้าย "
                        "ข้อมูลมีปีเดียว อุณหภูมิกับฤดูกาลเปลี่ยนพร้อมกัน อากาศมีชุดเดียวทุกอาคาร และความต่างของแอร์ปนกับความต่างของประเภทห้อง จึงสรุปสาเหตุไม่ได้")

# ---------------- 6. data quality ----------------
with st.container(border=True):
    ask("ข้อมูลมีปัญหาอะไร และจัดการอย่างไร?", "fact_check")
    A = ctx["all"]
    dup_n = int(A["clean_log"].loc[A["clean_log"]["issue"].str.contains("duplicate"), "rows_affected"].sum())
    st.markdown("> :material/record_voice_over: **พูดนำเสนอ:** “ก่อนวิเคราะห์ เราตรวจและจัดการข้อมูลแล้ว ค่าที่ผิดปกติไม่ได้ถูกลบทิ้งทั้งหมดโดยอัตโนมัติ เนื่องจากอาจเป็นเหตุการณ์จริง จึงแยกไว้เพื่อตรวจสอบเพิ่มเติม”")
    m = st.columns(4)
    m[0].metric("ข้อมูลซ้ำ (ตัดแล้ว)", fmt(dup_n), help="นับจากข้อมูลดิบทั้งชุด ไม่ขึ้นกับตัวกรอง")
    m[1].metric("ค่าว่าง (เติมแล้ว)", fmt(O["missing"]), help=f"ในข้อมูลที่เลือก n={fmt(len(d))} แถว")
    m[2].metric("ค่าติดลบ (ถือเป็นค่าเสีย)", fmt(O["negative"]))
    m[3].metric("ค่าสูงผิดปกติ", fmt(O["n"]), delta=f"{O['pct']:.4f}% ของข้อมูล", delta_arrow="off", delta_color="off")
    if O["has"]:
        where = "กระจายใกล้เคียงกันทุกอาคาร" if O["b_spread"] <= 1 else f"มากที่สุดที่{O['top_b']} ({O['top_b_n']} จุด)"
        st.markdown(f":material/report: **สรุปค่าที่ผิดปกติ:** พบ {O['n']} รายการ ({O['pct']:.4f}%) ใน {O['rooms']} ห้อง ห้องละไม่เกิน {O['max_per_room']} จุด {where} เกิดบ่อยสุดช่วง {O['top_h']:02d}:00 และเดือน {_M[O['top_m'] - 1]} "
                    f"แต่ละจุดเป็นชั่วโมงเดียวโดดๆ สูงกว่าปกติ {O['ratio_min']:.0f}-{O['ratio_max']:.0f} เท่า")
    else:
        st.info("ไม่พบค่าสูงผิดปกติในตัวกรองที่เลือก", icon=":material/info:")
    with st.expander("ดูวิธีจัดการและเหตุผล", icon=":material/functions:"):
        st.markdown("- **ข้อมูลซ้ำ:** เป็นสำเนาเหมือนกันทุกประการ จึงตัดออกและเก็บชุดเดียว\n"
                    "- **ค่าว่าง:** เติมด้วยค่ากลางของมิเตอร์เดียวกัน ชั่วโมงเดียวกัน ประเภทวันเดียวกัน ยอดรวมเปลี่ยนน้อยมาก\n"
                    "- **ค่าติดลบ:** เท่ากับ -0.5 ทุกแถว น่าจะเป็นรหัสแทนค่าเสียของมิเตอร์ ไม่ใช่ค่าจริง\n"
                    "- **ค่าสูงผิดปกติ:** ไม่ลบทิ้ง เก็บค่าเดิมไว้ในคอลัมน์ energy_kwh และตารางค่าผิดปกติ ใช้ค่าปกติของช่วงเวลาเดียวกันแทนเฉพาะในการคำนวณกราฟ เพราะแต่ละจุดสูงผิดปกติหลายสิบเท่าในชั่วโมงเดียว ถ้าไม่แทนจะดึงค่าเฉลี่ยและอันดับให้เพี้ยน "
                    "แต่ข้อมูลยืนยันไม่ได้ว่าเป็นความผิดพลาดหรือเหตุการณ์จริง ถ้ายืนยันได้ว่าเป็นเหตุการณ์จริง ให้ใส่ค่าเดิมกลับ")
        if O["has"]:
            st.markdown(f"ถ้าไม่แทนค่า จะมีไฟส่วนเกินราว {fmt(O['excess_kwh'])} kWh ({100 * O['excess_kwh'] / total:.2f}% ของไฟที่เลือก) จากค่าผิดปกติเหล่านี้")
        st.caption("เกณฑ์ตรวจค่าสูงผิดปกติ: สูงกว่า Q3 + 3 x IQR ของมิเตอร์เดียวกัน ชั่วโมงเดียวกัน ประเภทวันเดียวกัน และเกิน 3 เท่าของค่ากลาง (หลักสถิติทั่วไป ผสมค่าที่ทีมเลือก ไม่ใช่มาตรฐานทางการ)")

st.divider()
st.markdown(":material/arrow_forward: **เจาะลึกต่อ:**")
l = st.columns(4)
l[0].page_link("pages/ranking.py", label="จัดอันดับ", icon=":material/leaderboard:")
l[1].page_link("pages/offhours.py", label="นอกเวลาและวันหยุด", icon=":material/dark_mode:")
l[2].page_link("pages/factors.py", label="คน แอร์ อากาศ", icon=":material/thermostat:")
l[3].page_link("pages/problems.py", label="ปัญหาและแนวทางแก้ไข", icon=":material/build_circle:")
