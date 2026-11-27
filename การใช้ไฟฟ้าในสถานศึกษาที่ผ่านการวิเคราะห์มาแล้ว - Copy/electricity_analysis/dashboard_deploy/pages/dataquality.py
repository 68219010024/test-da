"""Dashboard page (generated from the former single main page)."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (ask, rank_cards, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.analysis import room_table, problems, within_corr, std_effects, outlier_summary, quality_summary
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

banner("ค่าผิดปกติและคุณภาพข้อมูล", "ข้อมูลมีปัญหาอะไร จัดการอย่างไร และตัวเลขเปลี่ยนเพราะอะไร (ตรวจย้อนกลับได้ทุกขั้น)")
A = ctx["all"]
tabs = st.tabs([":material/fact_check: สรุปคุณภาพข้อมูล", ":material/report: ค่าผิดปกติ", ":material/scatter_plot: ค่าว่างและติดลบ", ":material/balance: ขั้นตอนและกระทบยอด"])
with tabs[0]:
    Q = quality_summary()
    ask("ข้อมูลชุดนี้พร้อมใช้งานแค่ไหน ตรวจพบอะไรและจัดการอย่างไร?", "fact_check")
    st.caption("ตารางและตัวเลขในแท็บนี้สรุปทั้งชุดข้อมูล (ไม่ขึ้นกับตัวกรอง) เพราะการทำความสะอาดทำกับข้อมูลทั้งชุดครั้งเดียว")
    r1 = st.columns(4)
    r1[0].metric("แถวก่อนทำความสะอาด", fmt(Q["rows_before"]))
    r1[1].metric("แถวหลังทำความสะอาด", fmt(Q["rows_after"]), delta=f"-{Q['dup']} แถวซ้ำ", delta_arrow="off", delta_color="off", help="เท่ากับ 40 มิเตอร์ x 8,760 ชั่วโมง")
    r1[2].metric("ข้อมูลซ้ำ", fmt(Q["dup"]))
    r1[3].metric("ค่าว่าง", fmt(Q["missing"]))
    r2 = st.columns(4)
    r2[0].metric("ค่าติดลบ", fmt(Q["negative"]), help="เท่ากับ -0.5 ทุกแถว")
    r2[1].metric("ค่าสูงผิดปกติ (Outlier)", fmt(Q["outliers"]))
    r2[2].metric("จุดกระโดดเฉพาะชั่วโมง", fmt(Q["spike_logged"]), help="ชั่วโมงเดียวที่โดดขึ้นสูงผิดปกติแล้วกลับ เป็นชุดเดียวกับค่าสูงผิดปกติ")
    r2[3].metric("การเปลี่ยนระดับถาวร", fmt(Q["shifted"]), delta=f"ตรวจ {fmt(Q['shift_cells'])} กลุ่ม", delta_arrow="off", delta_color="off",
                 help="เทียบค่ากลางของมิเตอร์/ชั่วโมง/ประเภทวันเดียวกัน ครึ่งปีแรกกับครึ่งปีหลัง ถือว่าเปลี่ยนระดับถ้าต่างกันเกิน 1.5 เท่า")
    pct = lambda v: 100 * v / Q["raw_total_with_dups"]
    st.markdown("**ปัญหาข้อมูล จำนวนที่พบ วิธีจัดการ และผลกระทบต่อยอดรวม**")
    st.dataframe(pd.DataFrame({
        "ปัญหาข้อมูล": ["ข้อมูลซ้ำ", "ค่าว่าง", "ค่าติดลบ", "ค่าสูงผิดปกติ (Outlier)", "การเปลี่ยนระดับถาวร"],
        "จำนวนที่พบ": [f"{Q['dup']} แถว", f"{Q['missing']} แถว", f"{Q['negative']} แถว", f"{Q['outliers']} จุด", f"{Q['shifted']} จาก {fmt(Q['shift_cells'])} กลุ่ม"],
        "วิธีจัดการ": ["ตัดสำเนา เก็บแถวเดียว", "เติมด้วยค่ากลางของมิเตอร์ ชั่วโมง ประเภทวันเดียวกัน", "ถือเป็นค่าเสีย แทนด้วยค่ากลางแบบเดียวกัน",
                       "ไม่ลบทิ้ง เก็บค่าเดิมและติดป้าย ใช้ค่าปกติแทนในการคำนวณกราฟ", "ตรวจแล้วไม่พบ จึงไม่ต้องจัดการ" if Q["shifted"] == 0 else "ต้องตรวจสอบเพิ่มเติม"],
        "ผลต่อยอดรวม (kWh)": [f"{Q['delta_dup']:+,.1f} ({pct(Q['delta_dup']):+.3f}%)", f"{Q['delta_missing']:+,.1f} ({pct(Q['delta_missing']):+.3f}%)",
                              f"{Q['delta_neg']:+,.1f} ({pct(Q['delta_neg']):+.3f}%)", f"{Q['delta_out']:+,.1f} ({pct(Q['delta_out']):+.3f}%)", "0"]}), hide_index=True, width="stretch")
    # before -> process -> after
    st.markdown("**ก่อน → กระบวนการ → หลัง**")
    b, a_ = Q["before"], Q["after"]
    c1, c2, c3 = st.columns([3, 2, 3])
    with c1:
        with st.container(border=True):
            st.markdown(":material/folder_open: **ข้อมูลก่อนทำความสะอาด**")
            st.markdown(f"แถว {fmt(Q['rows_before'])} | ใช้ได้ {fmt(b['n'])} ค่า  \nยอดรวม {fmt(b['total'])} kWh  \nเฉลี่ย {b['mean']:.3f} | ค่าสูงสุด {b['max']:.1f} kWh")
    with c2:
        with st.container(border=True):
            st.markdown(":material/cleaning_services: **กระบวนการ**")
            st.markdown("1 ตัดข้อมูลซ้ำ  \n2 เติมค่าว่าง  \n3 แทนค่าติดลบ  \n4 แทนค่าสูงผิดปกติ")
    with c3:
        with st.container(border=True):
            st.markdown(":material/verified: **ข้อมูลหลังทำความสะอาด**")
            st.markdown(f"แถว {fmt(Q['rows_after'])} | ใช้ได้ {fmt(a_['n'])} ค่า  \nยอดรวม {fmt(a_['total'])} kWh  \nเฉลี่ย {a_['mean']:.3f} | ค่าสูงสุด {a_['max']:.1f} kWh")
    f = go.Figure(go.Bar(x=["ก่อนจัดการ", "หลังจัดการ"], y=[b["max"], a_["max"]], marker_color=[ORANGE, BLUE], text=[f"{b['max']:.1f}", f"{a_['max']:.1f}"], textposition="outside"))
    style(f, 340, "ก่อนและหลังจัดการ ค่าสูงสุดของ kWh ต่อชั่วโมงลดลงเท่าไร?", legend=False)
    f.update_yaxes(title="ค่าสูงสุด kWh ต่อห้องต่อชั่วโมง", range=[0, b["max"] * 1.2])
    show(f, "dq_ba")
    explain(
        short=f"แถว {fmt(Q['rows_before'])} เหลือ {fmt(Q['rows_after'])} (ตัดซ้ำ {Q['dup']}) ค่าสูงสุดลดจาก {b['max']:.1f} เหลือ {a_['max']:.1f} kWh ยอดรวมเปลี่ยน {100 * (Q['after']['total'] / Q['raw_total_with_dups'] - 1):+.2f}%",
        found=f"พบข้อมูลซ้ำ {Q['dup']} แถว ค่าว่าง {Q['missing']} ค่าติดลบ {Q['negative']} (เท่ากับ -0.5 ทุกแถว) และค่าสูงผิดปกติ {Q['outliers']} จุด ตรวจการเปลี่ยนระดับถาวรใน {fmt(Q['shift_cells'])} กลุ่ม พบ {Q['shifted']} กลุ่ม (อัตราส่วนครึ่งปีแรก-หลังอยู่ระหว่าง {Q['ratio_min']:.2f}-{Q['ratio_max']:.2f})",
        meaning="ข้อมูลพร้อมใช้งานหลังจัดการ ผลต่อยอดรวมเล็กน้อย ค่าสูงผิดปกติเป็นการโดดชั่วโมงเดียวไม่ใช่การเปลี่ยนระดับ ไม่ลบทิ้งเพราะอาจเป็นเหตุการณ์จริง ค่าเดิมเก็บไว้ตรวจสอบย้อนกลับได้",
        action="ให้ผู้ดูแลมิเตอร์ตรวจ 21 จุดตามตารางค่าผิดปกติ และแก้ระบบบันทึกไม่ให้ซ้ำ ไม่ส่งค่า -0.5 และแจ้งเตือนเมื่อข้อมูลขาด",
        use="ดูภาพรวมคุณภาพข้อมูลและผลของการทำความสะอาดในที่เดียว", read="การ์ดบนคือจำนวนปัญหา ตารางคือวิธีจัดการและผลต่อยอดรวม กล่องกราฟเทียบข้อมูลก่อนกับหลัง จุดแดงคือค่าสูงผิดปกติเดิม",
        method="นับจากข้อมูลทั้งชุด และกระทบยอดทีละขั้น การเปลี่ยนระดับถาวรตรวจโดยเทียบค่ากลางของกลุ่มเดียวกันครึ่งปีแรกกับครึ่งปีหลัง (เกณฑ์ 1.5 เท่าเป็นค่าที่ทีมเลือก ไม่ใช่มาตรฐานทางการ)", n=Q["rows_after"])

with tabs[1]:
    O = outlier_summary(d)
    ask("มีช่วงไหนหรือพื้นที่ไหนที่ใช้ไฟผิดปกติ?", "report")
    with st.container(border=True):
        st.markdown(":material/report: **สรุปค่าที่ผิดปกติ**")
        if not O["has"]:
            st.markdown("ไม่พบค่าสูงผิดปกติในตัวกรองที่เลือก")
        else:
            mm = st.columns(4)
            mm[0].metric("พบค่าผิดปกติ (รายการ)", fmt(O["n"]), help=f"จากข้อมูลที่เลือก n={fmt(O['N'])} แถว")
            mm[1].metric("คิดเป็น", f"{O['pct']:.4f}%")
            mm[2].metric("กระจายใน (ห้อง)", fmt(O["rooms"]), delta=f"ห้องละไม่เกิน {O['max_per_room']} จุด", delta_arrow="off", delta_color="off")
            mm[3].metric("เกิดบ่อยสุดช่วง", f"{O['top_h']:02d}:00", delta=f"เดือน {MONTHS[O['top_m'] - 1]}", delta_arrow="off", delta_color="off")
            where = "กระจายใกล้เคียงกันทุกอาคาร จึงจัดอันดับว่าพื้นที่ไหนมากที่สุดไม่ได้ชัดเจน" if O["b_spread"] <= 1 else f"พบมากที่สุดที่{O['top_b']} ({O['top_b_n']} จุด)"
            st.markdown(f":material/location_on: **ที่ไหน:** {where}  \n:material/schedule: **เมื่อไร:** บ่อยสุดช่วง {O['top_h']:02d}:00 ({O['top_h_n']} จุด) และเดือน {MONTHS[O['top_m'] - 1]} ({O['top_m_n']} จุด)  \n"
                        f":material/straighten: **ขนาด:** สูงกว่าปกติของช่วงเวลาเดียวกัน {O['ratio_min']:.0f}-{O['ratio_max']:.0f} เท่า แต่ละจุดเป็นชั่วโมงเดียวโดดๆ")
            st.markdown(":material/verified: **การจัดการ:** ข้อมูลที่มีค่าผิดปกติไม่ได้ถูกลบทิ้งโดยอัตโนมัติ เนื่องจากอาจเป็นเหตุการณ์จริง จึงเก็บค่าเดิมไว้ในคอลัมน์ energy_kwh และตารางด้านล่าง เพื่อใช้ตรวจสอบเพิ่มเติม")
            st.markdown(f":material/swap_horiz: **เหตุผลที่ใช้ค่าปกติแทนในกราฟ:** แต่ละจุดสูงผิดปกติหลายสิบเท่าในชั่วโมงเดียว ถ้าไม่แทนจะมีไฟส่วนเกินราว {fmt(O['excess_kwh'])} kWh ({100 * O['excess_kwh'] / total:.2f}% ของไฟที่เลือก) ดึงค่าเฉลี่ยและอันดับให้เพี้ยน ถ้ายืนยันได้ว่าเป็นเหตุการณ์จริง ให้ใส่ค่าเดิมกลับ")
            rank_cards([{"label": n, "value": f"{int(c)} จุด", "sub": "อันดับตามจำนวนค่าผิดปกติ (ใกล้เคียงกัน)" if O["b_spread"] <= 1 else "อันดับตามจำนวนค่าผิดปกติ"} for n, c in O["by_b"].head(3).items()])
            with st.expander("ดูวิธีตรวจค่าผิดปกติและเกณฑ์", icon=":material/functions:"):
                st.markdown("เทียบแต่ละค่ากับกลุ่มของตัวเอง (มิเตอร์เดียวกัน ชั่วโมงเดียวกัน ประเภทวันเดียวกัน) ต้องสูงกว่า Q3 + 3 x IQR และเกิน 3 เท่าของค่ากลาง เหตุผลที่ไม่ใช้เกณฑ์รวมทั้งชุด: การใช้ไฟมี 2 ระดับ (ช่วงมีคนกับนอกเวลา) เกณฑ์รวมจะติดป้ายชั่วโมงปกติผิดจำนวนมาก")
                st.caption("เกณฑ์นี้ใช้สำหรับคัดกรองเบื้องต้น ไม่ใช่มาตรฐานทางการ และสามารถปรับเปลี่ยนได้ตามบริบทหรือข้อมูลจริง")
    out = d[d["flag_outlier"]].copy()
    if len(out) == 0:
        st.info("ไม่พบค่าผิดปกติในตัวกรองที่เลือก", icon=":material/info:")
    else:
        out["ratio"] = out["energy_kwh"] / out["cell_median"]
        c1, c2 = st.columns([3, 2])
        with c1:
            f = go.Figure(go.Scatter(x=out["timestamp"], y=out["energy_kwh"], mode="markers", marker=dict(size=12, color=RED, line=dict(width=1, color="#FFFFFF")),
                                     text=out["room_id"] + " " + out["room_type"], customdata=out["ratio"], hovertemplate="%{text}<br>%{x|%Y-%m-%d %H:%M}<br>%{y:.1f} kWh (%{customdata:.0f} เท่าของปกติ)<extra></extra>"))
            style(f, 330, "ค่าผิดปกติเกิดเมื่อไร ที่ห้องไหน?", legend=False); f.update_yaxes(type="log", title="kWh (แกนล็อก)")
            show(f, "ov_out")
        with c2:
            by_m = out.groupby("month").size().reindex(range(1, 13), fill_value=0)
            f = go.Figure(go.Bar(x=MONTHS, y=by_m.values, marker_color=RED))
            style(f, 330, "ค่าผิดปกติเกิดเดือนไหนบ่อยที่สุด?", legend=False); f.update_yaxes(title="จุด")
            show(f, "ov_outm")
        iso_note = f"เกิดเป็นชั่วโมงเดียวโดดๆ สูงกว่าปกติ {out['ratio'].min():.0f}-{out['ratio'].max():.0f} เท่า"
        explain(
            short=f"พบ {len(out)} จุด กระจายใน {out['room_id'].nunique()} ห้อง ห้องละไม่เกิน {out.groupby('room_id').size().max()} จุด ({100 * len(out) / len(d):.4f}% ของข้อมูลที่เลือก)",
            found=f"{iso_note} กระจายหลายเดือนและหลายชั่วโมง ไม่กระจุกที่ห้องเดียว จึงจัดอันดับพื้นที่ที่พบมากที่สุดไม่ได้ ผลรวมที่เกินปกติ {fmt((out['energy_kwh'] - out['cell_median']).sum())} kWh ({100 * (out['energy_kwh'] - out['cell_median']).sum() / total:.2f}% ของไฟที่เลือก)",
            meaning="ลักษณะเข้าได้กับการอ่านค่าผิดพลาดมากกว่าพฤติกรรมการใช้ไฟ แต่ข้อมูลยืนยันไม่ได้ จึงไม่ลบทิ้ง ค่าเดิมเก็บไว้ในคอลัมน์ energy_kwh และกราฟอื่นใช้ค่าปกติแทน",
            action="ให้ผู้ดูแลมิเตอร์ตรวจตามวันเวลาในตาราง ถ้าเป็นเหตุการณ์จริงให้ใส่ค่าเดิมกลับ (ภายใน 2 สัปดาห์)",
            use="ดูว่าค่าผิดปกติเกิดที่ไหน เมื่อไร บ่อยแค่ไหน", read="แต่ละจุดคือค่าผิดปกติหนึ่งจุด วางเมาส์เพื่อดูห้องและเวลา", method="เทียบกับกลุ่มของตัวเอง (มิเตอร์ x ชั่วโมง x ประเภทวัน) ต้องสูงกว่า Q3+3xIQR และเกิน 3 เท่าของค่ากลาง", n=len(out))
        st.dataframe(out.sort_values("energy_kwh", ascending=False)[["timestamp", "room_id", "building_name", "room_type", "energy_kwh", "cell_median", "ratio", "occupancy_people"]].rename(columns={
            "timestamp": "เวลา", "room_id": "ห้อง", "building_name": "อาคาร", "room_type": "ประเภทห้อง", "energy_kwh": "ค่าเดิม (kWh)", "cell_median": "ค่าปกติช่วงเวลาเดียวกัน (kWh)",
            "ratio": "เท่าของปกติ", "occupancy_people": "จำนวนคน"}).round({"ค่าเดิม (kWh)": 2, "ค่าปกติช่วงเวลาเดียวกัน (kWh)": 2, "เท่าของปกติ": 1}), hide_index=True, width="stretch")

with tabs[2]:
    section("ดูข้อมูลดิบเทียบข้อมูลสะอาดรายห้อง", "compare")
    rooms = sorted(d["room_id"].unique())
    sel = st.selectbox("เลือกห้อง", rooms, key="q_room")
    view = st.radio("แสดง", ["ข้อมูลสะอาด", "ข้อมูลดิบ", "เทียบทั้งสอง"], horizontal=True, key="q_view")
    x = d[d["room_id"] == sel].set_index("timestamp").sort_index()
    daily_clean = x[E].resample("D").sum()
    daily_raw = x["energy_kwh"].resample("D").sum(min_count=1)
    f = go.Figure()
    if view in ("ข้อมูลดิบ", "เทียบทั้งสอง"):
        f.add_scatter(x=daily_raw.index, y=daily_raw.values, name="ดิบ (รวมค่าผิดปกติ)", line=dict(color=AMBER, width=2))
    if view in ("ข้อมูลสะอาด", "เทียบทั้งสอง"):
        f.add_scatter(x=daily_clean.index, y=daily_clean.values, name="สะอาด", line=dict(color=BLUE, width=2))
    style(f, 320, f"ข้อมูลดิบกับข้อมูลสะอาดต่างกันอย่างไร? ({sel})"); f.update_yaxes(title="kWh ต่อวัน")
    show(f, "q_cmp")
    flags = x[["flag_missing", "flag_negative", "flag_outlier"]].sum()
    st.caption(f"ห้อง {sel} ในช่วงที่เลือก: ค่าว่าง {int(flags['flag_missing'])} | ติดลบ {int(flags['flag_negative'])} | ผิดปกติสูง {int(flags['flag_outlier'])} (n={fmt(len(x))} แถว) วันที่มีค่าผิดปกติจะเห็นเส้นดิบพุ่งขึ้น")

    section("ค่าว่างและค่าติดลบที่พบในช่วงที่เลือก", "scatter_plot")
    na = d[d["flag_missing"] | d["flag_negative"]]
    if len(na) == 0:
        st.info("ไม่พบค่าว่างหรือค่าติดลบในตัวกรองที่เลือก", icon=":material/info:")
    else:
        f = go.Figure()
        for flag, name, col in [("flag_missing", "ค่าว่าง", AMBER), ("flag_negative", "ค่าติดลบ (-0.5)", RED)]:
            s = na[na[flag]]
            f.add_scatter(x=s["timestamp"], y=s["meter_id"], mode="markers", name=name, marker=dict(size=9, color=col))
        style(f, 380, "ค่าว่างและค่าติดลบเกิดที่มิเตอร์ไหน เมื่อไร?"); f.update_yaxes(tickfont=dict(size=9))
        show(f, "q_miss")
        explain(short=f"ค่าว่าง {int(d['flag_missing'].sum())} จุด ค่าติดลบ {int(d['flag_negative'].sum())} จุด กระจายหลายมิเตอร์ ไม่ขาดต่อเนื่อง",
                found="ค่าติดลบเท่ากับ -0.5 ทุกแถว จึงน่าจะเป็นรหัสแทนค่าเสียของมิเตอร์ ไม่ใช่ค่าจริง ค่าว่างแต่ละมิเตอร์ไม่เกิน 1 ชั่วโมงและไม่มีชั่วโมงที่หลายมิเตอร์ขาดพร้อมกัน",
                meaning="ไม่ใช่ระบบรวมล่ม แต่เป็นการบันทึกขาดเป็นครั้งคราว เติมค่าแล้วกระทบยอดรวมน้อยมาก",
                action="ตรวจระบบบันทึกของมิเตอร์ที่ขาด และไม่ส่งค่า -0.5 (ผู้ดูแลระบบมิเตอร์ ภายใน 1 เดือน)", use="ดูรูปแบบการขาดหาย", read="แต่ละจุดคือ 1 ชั่วโมงของมิเตอร์นั้น", method="นับค่าว่างและติดลบตามมิเตอร์และเวลา", n=len(na))

with tabs[3]:
    section("ขั้นตอนทำความสะอาดที่ทำไปแล้ว", "cleaning_services")
    log = A["clean_log"].rename(columns={"step": "ขั้น", "issue": "ปัญหาที่พบ", "rows_affected": "จำนวนแถว", "action": "วิธีจัดการ"})
    st.dataframe(log, hide_index=True, width="stretch")
    st.caption("ไม่ลบค่าผิดปกติทิ้ง: ค่าเดิมเก็บไว้ในคอลัมน์ energy_kwh และมีป้ายกำกับ ใช้ค่าปกติของมิเตอร์ ชั่วโมง ประเภทวันเดียวกันแทนเฉพาะในคอลัมน์ energy_clean")

    section("กระทบยอด: ยอดรวมเปลี่ยนเพราะอะไร", "balance")
    rec = A["recon"].copy()
    c1, c2 = st.columns([2, 3])
    with c1:
        st.dataframe(rec.rename(columns={"stage": "ขั้น", "delta_kWh": "เปลี่ยน (kWh)", "running_total_kWh": "ยอดสะสม (kWh)"}).round(2), hide_index=True, width="stretch")
    with c2:
        dl = rec.iloc[1:5]
        f = go.Figure(go.Bar(x=["ตัดข้อมูลซ้ำ", "แทนค่าติดลบ", "เติมค่าว่าง", "แทนค่าสูงผิดปกติ"], y=dl["delta_kWh"], marker_color=[RED if v < 0 else BLUE for v in dl["delta_kWh"]],
                             text=[f"{v:+.1f}" for v in dl["delta_kWh"]], textposition="outside"))
        style(f, 300, "การทำความสะอาดข้อมูลเปลี่ยนยอดรวมเท่าไร? (kWh)", legend=False)
        show(f, "q_recon")
    tot0, tot1 = rec["running_total_kWh"].iloc[0], rec["running_total_kWh"].iloc[-1]
    explain(short=f"ยอดรวมจาก {fmt(tot0)} เป็น {fmt(tot1)} kWh (เปลี่ยน {100 * (tot1 / tot0 - 1):.2f}%) ทุกการเปลี่ยนอธิบายได้", found="ขั้นที่เปลี่ยนยอดมากที่สุดคือการแทนค่าสูงผิดปกติ รองลงมาคือตัดข้อมูลซ้ำ",
            meaning="การทำความสะอาดไม่ทำให้ยอดรวมผิดเพี้ยนโดยไร้เหตุผล และตรวจย้อนกลับได้ทีละขั้น (ตารางนี้เป็นข้อมูลทั้งชุด ไม่ขึ้นกับตัวกรอง)",
            action="ใช้ตารางนี้ตอบกรรมการว่าตัวเลขเปลี่ยนเพราะอะไร", use="ตรวจว่ายอดหลังทำความสะอาดอธิบายได้", read="แท่งแดงลดลง แท่งน้ำเงินเพิ่มขึ้น", method="กระทบยอดทีละขั้นด้วยผลรวม kWh", n=350400)

    with st.expander("พจนานุกรมข้อมูล (ข้อมูลสะอาด)", icon=":material/menu_book:"):
        st.dataframe(A["dd"].rename(columns={"column": "คอลัมน์", "description": "คำอธิบาย", "type": "ชนิด", "unit": "หน่วย", "example": "ตัวอย่าง"}), hide_index=True, width="stretch")
