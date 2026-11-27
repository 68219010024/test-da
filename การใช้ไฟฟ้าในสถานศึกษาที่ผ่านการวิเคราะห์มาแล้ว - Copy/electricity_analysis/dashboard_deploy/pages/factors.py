"""Factors page: air conditioners, people, temperature, humidity (controlled comparison before concluding)."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (relationship_bars, ask, rank_cards, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
from core.analysis import room_table, problems, within_corr, std_effects, eta_squared, daily_temp_scatter
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

banner("คน แอร์ อากาศ กับการใช้ไฟ", "พบความสัมพันธ์หรือไม่ (ตรวจตัวแปรร่วมก่อนสรุป ไม่สรุปว่าเป็นสาเหตุ)")
occ = d[~off]
if len(occ) < 200:
    st.info("ข้อมูลช่วงมีคนในตัวกรองนี้น้อยเกินไปสำหรับวิเคราะห์ความสัมพันธ์ ลองขยายช่วงวันที่หรือเลือกประเภทวัน วันทำการ", icon=":material/info:")
    st.stop()
tabs = st.tabs([":material/ac_unit: แอร์และจำนวนคน", ":material/thermostat: อุณหภูมิและความชื้น", ":material/compare: ดูปัจจัยหลายอย่างร่วมกัน", ":material/hub: ทุกตัวแปรรวมกัน"])

cor = pd.DataFrame({
    "รวมทุกชั่วโมง": [d["occupancy_people"].corr(d[E]), d["temperature_c"].corr(d[E]), d["relative_humidity_percent"].corr(d[E])],
    "เฉพาะช่วงมีคน": [occ["occupancy_people"].corr(occ[E]), occ["temperature_c"].corr(occ[E]), occ["relative_humidity_percent"].corr(occ[E])],
    "ช่วงมีคน เทียบภายในห้องเดียวกัน": [within_corr(occ, E, "occupancy_people", "room_id"), within_corr(occ, E, "temperature_c", "room_id"), within_corr(occ, E, "relative_humidity_percent", "room_id")]},
    index=["จำนวนคน กับ ไฟ", "อุณหภูมิ กับ ไฟ", "ความชื้น กับ ไฟ"]).round(3)
res = std_effects(occ, ["occupancy_people", "air_conditioner_count", "temperature_c", "relative_humidity_percent", "area_m2"])
names = {"occupancy_people": "จำนวนคน", "air_conditioner_count": "จำนวนแอร์", "temperature_c": "อุณหภูมิ", "relative_humidity_percent": "ความชื้น", "area_m2": "พื้นที่ห้อง"}

with tabs[0]:
    ask("จำนวนแอร์และจำนวนคนสัมพันธ์กับการใช้ไฟอย่างไร?", "ac_unit")
    ac = occ.groupby("air_conditioner_count").agg(m=(E, "mean"), rooms=("room_id", "nunique"))
    c1, c2 = st.columns([2, 3])
    with c1:
        f = go.Figure(go.Bar(x=[f"{a} เครื่อง" for a in ac.index], y=ac["m"], marker_color=NAVY, text=[f"{v:.2f} kWh ({n} ห้อง)" for v, n in zip(ac["m"], ac["rooms"])], textposition="outside"))
        style(f, 340, "จำนวนแอร์ต่างกัน ใช้ไฟต่างกันแค่ไหน? (ช่วงมีคน)", legend=False); f.update_yaxes(range=[0, ac["m"].max() * 1.25], title="kWh ต่อห้องต่อชั่วโมง")
        show(f, "fx_ac")
    pp = occ[occ["occupancy_people"] > 0].groupby("room_id").agg(kwh=(E, "sum"), ph=("occupancy_people", "sum"))
    pp["kWh ต่อคน-ชั่วโมง"] = pp["kwh"] / pp["ph"]
    pp = pp.join(room.set_index("room_id")[["building_name", "room_type", "ac_count"]])
    pp["เทียบห้องแอร์เท่ากัน (เท่า)"] = pp["kWh ต่อคน-ชั่วโมง"] / pp.groupby("ac_count")["kWh ต่อคน-ชั่วโมง"].transform("median")
    top_pp = pp.sort_values("เทียบห้องแอร์เท่ากัน (เท่า)", ascending=False).head(5)
    with c2:
        st.markdown("**5 ห้องที่ใช้ไฟต่อคนสูงกว่าห้องที่มีแอร์เท่ากัน**")
        st.dataframe(top_pp.reset_index().rename(columns={"room_id": "ห้อง", "building_name": "อาคาร", "room_type": "ประเภทห้อง", "ac_count": "แอร์"})[
            ["ห้อง", "อาคาร", "ประเภทห้อง", "แอร์", "kWh ต่อคน-ชั่วโมง", "เทียบห้องแอร์เท่ากัน (เท่า)"]].round(3), hide_index=True, width="stretch")
        st.caption("เทียบกับค่ากลางของห้องที่มีเครื่องปรับอากาศจำนวนเท่ากัน เพื่อไม่ให้จำนวนแอร์ทำให้เปรียบเทียบผิด")
    b_ac = res[0].get("air_conditioner_count", float("nan")) if res is not None else float("nan")
    b_oc = res[0].get("occupancy_people", float("nan")) if res is not None else float("nan")
    explain(
        short=f"ห้องแอร์ 1/2/3 เครื่องใช้ไฟช่วงมีคน {' / '.join('%.2f' % v for v in ac['m'])} kWh ต่อชั่วโมง แอร์มีผลชัดกว่าจำนวนคน",
        found=f"ความสัมพันธ์กับจำนวนคน {cor.loc['จำนวนคน กับ ไฟ', 'รวมทุกชั่วโมง']:.2f} (รวมทุกชั่วโมง) เหลือ {cor.loc['จำนวนคน กับ ไฟ', 'เฉพาะช่วงมีคน']:.2f} เมื่อดูเฉพาะช่วงมีคน เพราะกลางคืนทั้งคนและไฟต่ำพร้อมกัน ห้องที่ใช้ไฟต่อคนสูงกว่าห้องแอร์เท่ากันมากสุดคือ {top_pp.index[0]} ({top_pp.iloc[0]['เทียบห้องแอร์เท่ากัน (เท่า)']:.2f} เท่า)",
        meaning="พบความสัมพันธ์ ไม่ได้พิสูจน์สาเหตุ การดูจำนวนคนอย่างเดียวประเมินเกินจริง เพราะต้องแยกผลของช่วงเวลาและจำนวนแอร์ออกก่อน",
        action="เวลาเทียบห้อง ให้เทียบกับห้องที่มีแอร์เท่ากัน ห้องใน 5 อันดับควรตรวจการตั้งค่าแอร์ (ฝ่ายอาคารสถานที่)",
        use="ดูว่าจำนวนแอร์และจำนวนคนสัมพันธ์กับไฟอย่างไร", read="แท่งสูงคือใช้ไฟมากเมื่อแอร์มากขึ้น ตัวเลขในวงเล็บคือจำนวนห้อง", method="เฉลี่ย kWh ช่วงมีคนตามจำนวนแอร์ และเทียบ kWh ต่อคน-ชั่วโมงกับค่ากลางของกลุ่มแอร์เท่ากัน", n=len(occ))

with tabs[1]:
    ask("อากาศร้อนขึ้น การใช้ไฟเปลี่ยนแปลงอย่างไร?", "thermostat")
    tb = occ.assign(tb=pd.cut(occ["temperature_c"], [0, 28, 30, 32, 34, 40], labels=["ไม่เกิน 28", "28-30", "30-32", "32-34", "เกิน 34"])) \
        .groupby(["tb", "air_conditioner_count"], observed=True)[E].agg(["mean", "size"]).reset_index()
    rc = pd.Series({rid: g[E].corr(g["temperature_c"]) for rid, g in occ.groupby("room_id")}).dropna()
    topc = rc.sort_values(ascending=False).head(5)
    c1, c2 = st.columns(2)
    with c1:
        f = go.Figure()
        for a, col in zip([1, 2, 3], [SKY, BLUE, NAVY]):
            s = tb[tb["air_conditioner_count"] == a]
            if len(s):
                f.add_scatter(x=s["tb"].astype(str), y=s["mean"], mode="lines+markers", name=f"แอร์ {a} เครื่อง", line=dict(color=col, width=3),
                              hovertemplate="%{x} องศา: %{y:.2f} kWh (n=%{customdata})<extra></extra>", customdata=s["size"])
        style(f, 340, "อากาศร้อนขึ้น ใช้ไฟช่วงมีคนเปลี่ยนไปอย่างไร?"); f.update_xaxes(title="อุณหภูมิภายนอก (องศา)"); f.update_yaxes(title="kWh ต่อห้องต่อชั่วโมง")
        show(f, "fx_temp")
    with c2:
        lab = [f"{i} {room.set_index('room_id').loc[i, 'room_type']}" for i in topc.index]
        f = go.Figure(go.Bar(y=lab[::-1], x=topc.values[::-1], orientation="h", marker_color=AMBER, text=[f"{v:.2f}" for v in topc.values[::-1]], textposition="outside"))
        style(f, 340, "ห้องไหนใช้ไฟสัมพันธ์กับอุณหภูมิชัดที่สุด? (Top 5)", legend=False); f.update_xaxes(range=[0, 1.1], title="ค่าความสัมพันธ์ r")
        show(f, "fx_roomr")
    explain(
        short=f"พบความสัมพันธ์: อากาศร้อนขึ้น ใช้ไฟช่วงมีคนสูงขึ้นในทุกกลุ่มแอร์ (ความสัมพันธ์ในห้องเดียวกัน {cor.loc['อุณหภูมิ กับ ไฟ', 'ช่วงมีคน เทียบภายในห้องเดียวกัน']:.2f})",
        found=f"ความชื้นกับไฟ {cor.loc['ความชื้น กับ ไฟ', 'รวมทุกชั่วโมง']:.2f} (ค่าลบ) แต่ความชื้นสวนทางกับอุณหภูมิมาก เมื่อควบคุมพร้อมกัน ผลของความชื้นเหลือใกล้ศูนย์ ห้องที่สัมพันธ์กับอุณหภูมิชัดสุดคือ {topc.index[0]} (r={topc.iloc[0]:.2f})",
        meaning="พบแนวโน้มที่อากาศร้อนสัมพันธ์กับการใช้ไฟมากขึ้น แต่ข้อมูลนี้บอกสาเหตุไม่ได้ ความชื้นที่ดูเหมือนสัมพันธ์กับไฟน่าจะสะท้อนอุณหภูมิ อากาศมีชุดเดียวทุกอาคาร จึงเทียบความต่างระหว่างอาคารด้านอากาศไม่ได้",
        action="วางแผนตั้งอุณหภูมิแอร์และตรวจฟิลเตอร์ก่อนช่วงอากาศร้อน (ฝ่ายอาคารสถานที่) และเก็บข้อมูลหลายปีเพื่อยืนยัน",
        use="ดูว่าอากาศร้อนหรือชื้นสัมพันธ์กับไฟหรือไม่", read="เส้นชันขึ้นคือร้อนขึ้นไฟเพิ่ม แยกสีตามจำนวนแอร์ กราฟขวาแท่งยาวคือสัมพันธ์ชัด", method="เฉลี่ย kWh ตามช่วงอุณหภูมิ และความสัมพันธ์รายห้อง", n=len(occ))

with tabs[2]:
    ask("เมื่อดูปัจจัยหลายอย่างร่วมกัน การใช้ไฟเปลี่ยนแปลงอย่างไร?", "compare")
    st.markdown("**ความสัมพันธ์ก่อนและหลังแยกช่วงเวลา/ห้อง (ตรวจก่อนสรุป)**")
    st.dataframe(cor, width="stretch")
    st.caption("ถ้าค่าเปลี่ยนมากเมื่อดูเฉพาะช่วงมีคน แปลว่าความสัมพันธ์แรกเห็นมาจากช่วงเวลา ไม่ใช่ตัวแปรนั้นเอง")
with tabs[3]:
    ask("อุณหภูมิกับการใช้ไฟสัมพันธ์กันอย่างไร?", "thermostat")
    sc = daily_temp_scatter(occ)
    fig = go.Figure()
    info = []
    for k_, col_ in zip([1, 2, 3], [SKY, BLUE, NAVY]):
        if k_ not in sc.columns:
            continue
        z = sc[["temp", k_]].dropna()
        if len(z) < 10:
            continue
        r_ = z["temp"].corr(z[k_]); slope, icpt = np.polyfit(z["temp"], z[k_], 1)
        info.append((k_, len(z), r_, slope))
        fig.add_scatter(x=z["temp"], y=z[k_], mode="markers", name=f"แอร์ {k_} เครื่อง ({len(z)} วัน)", marker=dict(color=col_, size=7, opacity=0.75),
                        hovertemplate="อุณหภูมิ %{x:.1f} องศา: %{y:.2f} kWh<extra></extra>")
        xs = np.array([z["temp"].min(), z["temp"].max()])
        fig.add_scatter(x=xs, y=slope * xs + icpt, mode="lines", showlegend=False, line=dict(color=col_, width=2, dash="dash"), hoverinfo="skip")
    style(fig, 400, "อากาศร้อนขึ้น ใช้ไฟช่วงมีคนเปลี่ยนไปอย่างไร? (1 จุด = 1 วัน เส้นประ = แนวโน้ม)")
    fig.update_xaxes(title="อุณหภูมิภายนอกเฉลี่ยของวัน (องศา)"); fig.update_yaxes(title="kWh ต่อห้องต่อชั่วโมง (เฉลี่ยของวัน ช่วงมีคน)")
    show(fig, "fx_scatter")
    st.caption(":material/warning: ข้อควรระวัง: ค่า r ใกล้ 1.00 สูงผิดปกติสำหรับข้อมูลจริง เพราะข้อมูลนี้เป็นข้อมูลจำลอง และเฉลี่ยรายวันตัดความผันผวนรายชั่วโมงออก อีกทั้งมีข้อมูลปีเดียว อุณหภูมิกับฤดูกาลจึงเปลี่ยนไปพร้อมกัน ใช้ดูทิศทางความสัมพันธ์ ไม่ใช้สรุปว่าอุณหภูมิเป็นสาเหตุ")
    if info:
        explain(
            short=f"พบความสัมพันธ์ทางเดียวกัน: วันที่อากาศร้อนขึ้น ไฟช่วงมีคนสูงขึ้นในทุกกลุ่มแอร์ (r ตั้งแต่ {min(i[2] for i in info):.2f} ถึง {max(i[2] for i in info):.2f})",
            found=f"อุณหภูมิเพิ่ม 1 องศา ไฟเฉลี่ยต่อห้องต่อชั่วโมงเพิ่มประมาณ " + ", ".join(f"{i[3]:.3f} kWh (แอร์ {i[0]} เครื่อง)" for i in info) + f" จากข้อมูลรายวัน {max(i[1] for i in info)} วัน (เฉพาะวันที่มีช่วงมีคน)",
            meaning="ความสัมพันธ์ไม่ได้หมายความว่าอุณหภูมิเป็นสาเหตุโดยตรง ข้อมูลมีปีเดียว อุณหภูมิกับฤดูกาลเปลี่ยนไปพร้อมกัน และค่า r รายวันดูแรงเพราะเฉลี่ยรายวันตัดความผันผวนรายชั่วโมงออก (เป็นข้อมูลจำลอง)",
            action="เก็บข้อมูลหลายปีเพื่อยืนยัน และเตรียมตั้งอุณหภูมิแอร์/ตรวจฟิลเตอร์ก่อนช่วงอากาศร้อนในห้องที่ใช้ไฟสูง",
            use="ดูว่าอุณหภูมิกับไฟสัมพันธ์กันอย่างไร", read="จุดแต่ละจุดคือหนึ่งวัน สีแยกตามจำนวนแอร์ เส้นประคือแนวโน้มเชิงเส้น", method="เฉลี่ยรายวันเฉพาะช่วงมีคน ค่า r แบบเพียร์สัน และเส้นแนวโน้มกำลังสองน้อยที่สุด", n=len(sc))
    else:
        st.info("จำนวนวันในตัวกรองนี้น้อยเกินไปสำหรับวาดกราฟความสัมพันธ์ ขยายช่วงวันที่", icon=":material/info:")

    ask("ตัวแปรใดมีความสัมพันธ์กับการใช้ไฟ? (ดูพร้อมกันทุกตัว)", "grid_on")
    relationship_bars(occ, E, "fx_rbars")
