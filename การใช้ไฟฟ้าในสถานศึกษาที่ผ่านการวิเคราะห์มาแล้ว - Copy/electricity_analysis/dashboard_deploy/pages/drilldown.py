"""Drill-down: all rooms -> building -> room -> period."""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from core.ui import banner, section, explain, show, style, fmt, NAVY, BLUE, SKY, AMBER, SLATE
from core.data import get_ctx
from core.analysis import room_table

E = "energy_clean"
DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

ctx = get_ctx()
d, thr = ctx["d"], ctx["thr"]
room = room_table(ctx)
banner("เจาะลึกอาคาร ห้อง ช่วงเวลา", "เลือกอาคาร แล้วเลือกห้อง แล้วเลือกช่วงเวลา เพื่อตอบคำถามต่อจากกราฟภาพรวม")

c1, c2, c3, c4 = st.columns(4)
bld_list = list(room.groupby("building_name")["total_kwh"].sum().sort_values(ascending=False).index)
b = c1.selectbox("1. อาคาร", bld_list, key="dd_b")
rr = room[room["building_name"] == b].sort_values("total_kwh", ascending=False)
rid = c2.selectbox("2. ห้อง (เรียงตามใช้ไฟมากไปน้อย)", list(rr["room_id"]), key="dd_r",
                   format_func=lambda x: f"{x}  {rr.set_index('room_id').loc[x, 'room_type']}")
months = sorted(d["month"].unique())
mo = c3.selectbox("3. ช่วงเวลา", ["ทั้งช่วงที่เลือก"] + [MONTHS[m - 1] for m in months], key="dd_m")
gran = c4.radio("ความละเอียด", ["รายชั่วโมง", "รายวัน", "รายสัปดาห์"], index=1, horizontal=True, key="dd_g")

st.markdown(f":material/home: ภาพรวมทั้งหมด  >  :material/apartment: {b}  >  :material/meeting_room: {rid}  >  :material/event: {mo}")

r = rr[rr["room_id"] == rid].iloc[0]
st.caption(f"ประเภทห้อง: {r['room_type']} | มิเตอร์ {r['meter_id']} | ความจุ {int(r['capacity_people'])} คน")
x = d[d["room_id"] == rid]
if mo != "ทั้งช่วงที่เลือก":
    x = x[x["month"] == MONTHS.index(mo) + 1]
if len(x) == 0:
    st.info("ไม่มีข้อมูลของห้องนี้ในช่วงเวลาที่เลือก", icon=":material/info:")
    st.stop()

k = st.columns(5)
k[0].metric("ห้อง", rid, help=f"{r['room_type']} | มิเตอร์ {r['meter_id']} | ความจุ {int(r['capacity_people'])} คน")
k[1].metric("พื้นที่ (ตร.ม.)", fmt(r["area_m2"]))
k[2].metric("เครื่องปรับอากาศ", f"{int(r['ac_count'])} เครื่อง")
k[3].metric("ใช้ไฟรวม (kWh)", fmt(x[E].sum()), help=f"n={fmt(len(x))} แถว")
off = x["is_off_hours"]
k[4].metric("สัดส่วนไฟนอกเวลา", f"{100 * x.loc[off, E].sum() / x[E].sum():.1f}%", help="kWh นอกเวลา / kWh ทั้งหมดของห้องในช่วงที่เลือก")

rule = {"รายชั่วโมง": None, "รายวัน": "D", "รายสัปดาห์": "W"}[gran]
s = x.set_index("timestamp")[E]
s = s if rule is None else s.resample(rule).sum()
f = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color=BLUE, width=1.5 if rule is None else 2.5), fill="tozeroy", fillcolor="rgba(30,111,217,0.12)"))
style(f, 320, f"ห้อง {rid} ใช้ไฟอย่างไรตามเวลา? ({gran})", legend=False); f.update_yaxes(title="kWh")
show(f, "dd_series")

c1, c2 = st.columns(2)
with c1:
    heat = x.groupby(["dow", "hour"])[E].mean().unstack()
    f = go.Figure(go.Heatmap(z=heat.values, x=heat.columns, y=[DAYS[i] for i in heat.index], colorscale=[[0, "#F3F7FC"], [0.5, SKY], [1, NAVY]], colorbar=dict(title="kWh")))
    style(f, 320, "ห้องนี้ใช้ไฟมากวันไหน ชั่วโมงไหน?", legend=False); f.update_yaxes(autorange="reversed"); f.update_xaxes(title="ชั่วโมง", dtick=2)
    show(f, "dd_heat")
with c2:
    peers = d[(d["air_conditioner_count"] == r["ac_count"]) & (d["room_id"] != rid)]
    mine = x.groupby("hour")[E].mean()
    ref = peers.groupby("hour")[E].median() if len(peers) else None
    f = go.Figure()
    f.add_scatter(x=mine.index, y=mine.values, name=rid, line=dict(color=BLUE, width=3))
    if ref is not None:
        f.add_scatter(x=ref.index, y=ref.values, name=f"ห้องอื่นที่มีแอร์ {int(r['ac_count'])} เครื่อง (ค่ากลาง)", line=dict(color=AMBER, width=3, dash="dash"))
    style(f, 320, "ห้องนี้ใช้ไฟสูงกว่าห้องอื่นที่มีแอร์เท่ากันหรือไม่?"); f.update_xaxes(title="ชั่วโมง", dtick=2); f.update_yaxes(title="kWh ต่อชั่วโมง")
    show(f, "dd_cmp")

diff = (mine - ref).dropna() if ref is not None else pd.Series(dtype=float)
hi = diff.idxmax() if len(diff) else None
explain(
    short=f"ห้อง {rid} ({r['room_type']}, {b}) ใช้ไฟ {fmt(x[E].sum())} kWh ในช่วงที่เลือก สัดส่วนนอกเวลา {100 * x.loc[off, E].sum() / x[E].sum():.1f}%",
    found=(f"ชั่วโมงที่ห้องนี้ต่างจากห้องที่มีแอร์เท่ากันมากที่สุดคือ {hi:02d}:00 (ต่าง {diff.max():+.2f} kWh ต่อชั่วโมง)" if hi is not None and diff.abs().max() > 0.05 else "รูปแบบรายชั่วโมงใกล้เคียงกับห้องที่มีแอร์เท่ากัน") + f" (ห้องเทียบ n={peers['room_id'].nunique() if len(peers) else 0} ห้อง)",
    meaning="ถ้าห้องต่างจากกลุ่มเฉพาะช่วงนอกเวลา เป็นพื้นที่ที่ควรตรวจสอบเพิ่มเติม ข้อมูลไม่ระบุอุปกรณ์ จึงสรุปสาเหตุไม่ได้",
    action="เทียบรูปแบบรายชั่วโมงกับตารางการใช้ห้องจริง แล้วตรวจการตั้งเวลาอุปกรณ์ในช่วงที่ต่างกัน",
    use="เจาะดูห้องเดียวตามช่วงเวลา", read="กราฟบนคือการใช้ไฟตามเวลา กราฟล่างซ้ายยิ่งเข้มยิ่งใช้ไฟมาก กราฟล่างขวาเส้นสีน้ำเงินสูงกว่าเส้นประคือสูงกว่าห้องอื่น", method="รวม/เฉลี่ย kWh ตามเวลาและเทียบกับค่ากลางของห้องที่มีแอร์เท่ากัน", n=len(x))

section("ตัวชี้วัดห้องนี้เทียบทั้งสถานศึกษา", "compare_arrows")
cmp = pd.DataFrame({"ห้องนี้": [r["total_kwh"], r["off_share_pct"], r["other_off_mean_kwh_h"], r["weekend_mean_kwh_h"]],
                    "ค่ากลางทุกห้อง": [room["total_kwh"].median(), room["off_share_pct"].median(), room["other_off_mean_kwh_h"].median(), room["weekend_mean_kwh_h"].median()]},
                   index=["ใช้ไฟรวม (kWh, ช่วงที่กรอง)", "สัดส่วนไฟนอกเวลา (%)", "ฐานไฟนอกเวลา (kWh/ชม.)", "ไฟวันหยุดเฉลี่ย (kWh/ชม.)"]).round(3)
st.dataframe(cmp, width="stretch")
st.caption("ตัวชี้วัดในตารางนี้คำนวณจากตัวกรองด้านซ้าย (ไม่ขึ้นกับตัวเลือกช่วงเวลาด้านบน)")
