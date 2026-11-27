"""Basic statistics page: summary statistics, distributions, group comparison, correlation, time pattern."""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.ui import (relationship_bars, ask, rank_cards, criteria_note, banner, section, explain, show, style, fmt, SEV_BADGE, SEV_COLOR, NAVY, BLUE, SKY, AMBER, RED, ORANGE, SLATE, MUTED)
from core.data import get_ctx
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

banner("ผลวิเคราะห์สถิติเบื้องต้น", "ค่ากลาง การกระจาย การเปรียบเทียบกลุ่ม และความสัมพันธ์ ของข้อมูลที่เลือก (ทุกตัวเลขมี n กำกับ)")
occ = d[~off]
offd = d[off]
SMALL = thr["small_rooms"]


def summ(s):
    s = s.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    return pd.Series({"n": len(s), "ค่าเฉลี่ย": s.mean(), "ค่ากลาง": s.median(), "ส่วนเบี่ยงเบนมาตรฐาน": s.std(), "ช่วงกลาง 50% (IQR)": q3 - q1,
                      "ต่ำสุด": s.min(), "สูงสุด": s.max(), "ความแปรผัน (%)": 100 * s.std() / s.mean() if s.mean() else np.nan})


rows = {"kWh ต่อห้องต่อชั่วโมง (ทุกชั่วโมง)": d[E], "kWh ต่อห้องต่อชั่วโมง (ช่วงมีคน)": occ[E], "kWh ต่อห้องต่อชั่วโมง (นอกเวลา)": offd[E],
        "จำนวนคน (ช่วงมีคน)": occ["occupancy_people"], "อุณหภูมิ (องศา)": d["temperature_c"], "ความชื้นสัมพัทธ์ (%)": d["relative_humidity_percent"]}
stat = pd.DataFrame({k: summ(v) for k, v in rows.items() if len(v.dropna())}).T
stat["n"] = stat["n"].astype(int)

# quick reading strip (all numbers computed from the selected data)
m_all, md_all = d[E].mean(), d[E].median()
wk = d[d["day_type"] == "weekday"][E]
we = d[d["day_type"] == "weekend"][E]
st.markdown(f":material/lightbulb: **ข้อสังเกตจากสถิติ (n={fmt(len(d))} แถว):** ค่าเฉลี่ย {m_all:.2f} สูงกว่าค่ากลาง {md_all:.2f} kWh แปลว่าการกระจายเบ้ขวา (มีชั่วโมงที่ใช้ไฟสูงดึงค่าเฉลี่ยขึ้น)"
            + (f" | ช่วงมีคนค่ากลาง {occ[E].median():.2f} เทียบนอกเวลา {offd[E].median():.3f} kWh" if len(occ) and len(offd) else "")
            + (f" | วันหยุดต่ำกว่าวันทำการ {100 * (1 - we.mean() / wk.mean()):.0f}%" if len(wk) and len(we) else ""))

tabs = st.tabs([":material/calculate: สรุปค่าสถิติ", ":material/bar_chart: การกระจาย", ":material/groups: เปรียบเทียบกลุ่ม",
                ":material/grid_on: ความสัมพันธ์ของตัวแปร", ":material/calendar_month: รูปแบบตามเวลา"])

# ---------- tab 0: summary table ----------
with tabs[0]:
    ask("ข้อมูลโดยรวมมีค่าเฉลี่ยและการกระจายเป็นอย่างไร?", "calculate")
    st.markdown("**ตารางสถิติสรุป (ค่าเฉลี่ย ค่ากลาง ส่วนเบี่ยงเบนมาตรฐาน IQR ต่ำสุด-สูงสุด)**")
    st.dataframe(stat.round(3), width="stretch",
                 column_config={"n": st.column_config.NumberColumn("n", format="%d")})
    cmp_ = d.groupby("day_type_th").agg(n=(E, "size"), mean=(E, "mean"), median=(E, "median"), std=(E, "std"), total=(E, "sum"))
    cmp_["สัดส่วนไฟทั้งหมด (%)"] = 100 * cmp_["total"] / total
    st.markdown("**วันทำการเทียบวันหยุด**")
    st.dataframe(cmp_.rename(columns={"n": "n (แถว)", "mean": "เฉลี่ย kWh/ชม.", "median": "ค่ากลาง", "std": "SD", "total": "รวม kWh"}).round(3), width="stretch")
    delta = (100 * (cmp_.loc["วันหยุด", "mean"] / cmp_.loc["วันทำการ", "mean"] - 1)) if {"วันหยุด", "วันทำการ"} <= set(cmp_.index) else None
    cv_all = stat.loc["kWh ต่อห้องต่อชั่วโมง (ทุกชั่วโมง)", "ความแปรผัน (%)"]
    explain(
        short=f"ใช้ไฟเฉลี่ย {m_all:.2f} kWh ต่อห้องต่อชั่วโมง (ค่ากลาง {md_all:.2f}, SD {d[E].std():.2f}) สูงสุด {d[E].max():.2f}",
        found=f"ความแปรผันของ kWh ทุกชั่วโมงสูง ({cv_all:.0f}%) เพราะปนกันระหว่างช่วงมีคนกับนอกเวลา เมื่อแยกช่วงแล้ว ช่วงมีคนความแปรผัน {stat.loc['kWh ต่อห้องต่อชั่วโมง (ช่วงมีคน)', 'ความแปรผัน (%)'] if 'kWh ต่อห้องต่อชั่วโมง (ช่วงมีคน)' in stat.index else float('nan'):.0f}%" + (f" วันหยุดต่างจากวันทำการ {delta:+.0f}% (n วันหยุด={fmt(cmp_.loc['วันหยุด', 'n'])}, n วันทำการ={fmt(cmp_.loc['วันทำการ', 'n'])})" if delta is not None else ""),
        meaning="ค่าเฉลี่ยรวมทุกชั่วโมงอย่างเดียวบอกพฤติกรรมไม่ได้ ต้องแยกช่วงมีคนกับนอกเวลา ค่าสูงสุดนี้เป็นค่าหลังจัดการค่าผิดปกติแล้ว (ค่าเดิมเก็บไว้ในตารางค่าผิดปกติ)",
        action="ใช้ค่ากลางและ IQR เมื่อต้องการค่าตัวแทนที่ไม่ถูกดึงด้วยค่าสูง และรายงานแยกช่วงมีคนกับนอกเวลาเสมอ",
        use="ดูภาพรวมสถิติของข้อมูลที่เลือก", read="ตารางบนแยกตามตัวแปร ตารางล่างเทียบวันทำการกับวันหยุด ความแปรผัน = SD / ค่าเฉลี่ย", method="สถิติเชิงพรรณนา (ค่าเฉลี่ย ค่ากลาง SD IQR ต่ำสุด สูงสุด) จากข้อมูลที่ผ่านการทำความสะอาด", n=len(d))

# ---------- tab 1: distributions ----------
with tabs[1]:
    ask("การใช้ไฟกระจายตัวอย่างไร และมีช่วงที่สูงผิดปกติหรือไม่?", "bar_chart")
    if len(occ) == 0 or len(offd) == 0:
        st.info("ต้องมีทั้งช่วงมีคนและนอกเวลาในตัวกรองเพื่อเทียบการกระจาย เลือกประเภทวัน วันทำการ และวันหยุด ที่ตัวกรองด้านบน", icon=":material/info:")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            f = go.Figure()
            f.add_box(y=offd[E], name="นอกเวลา", marker_color=SKY, boxmean=True)
            f.add_box(y=occ[E], name="ช่วงมีคน", marker_color=BLUE, boxmean=True)
            style(f, 360, "ช่วงมีคนกับนอกเวลา ใช้ไฟต่างกันแค่ไหน?", legend=False); f.update_yaxes(title="kWh ต่อห้องต่อชั่วโมง")
            show(f, "st_box")
        with c2:
            f = go.Figure(go.Histogram(x=occ[E], nbinsx=40, marker_color=BLUE))
            f.add_vline(x=occ[E].median(), line_dash="dash", line_color=AMBER, line_width=3)
            style(f, 360, f"ช่วงมีคน ส่วนใหญ่ใช้ไฟเท่าไร? (เส้นประ = ค่ากลาง {occ[E].median():.2f})", legend=False); f.update_xaxes(title="kWh ต่อห้องต่อชั่วโมง"); f.update_yaxes(title="จำนวนชั่วโมง")
            show(f, "st_hist_e")
        with c3:
            f = go.Figure(go.Histogram(x=occ["occupancy_people"], nbinsx=20, marker_color=NAVY))
            style(f, 360, "ช่วงมีคน มักมีกี่คนในห้อง?", legend=False); f.update_xaxes(title="คน"); f.update_yaxes(title="จำนวนชั่วโมง")
            show(f, "st_hist_p")
        q = offd[E].quantile([0.5, 0.99])
        explain(
            short=f"ช่วงมีคนค่ากลาง {occ[E].median():.2f} kWh เทียบนอกเวลา {offd[E].median():.3f} kWh ({occ[E].median() / offd[E].median():.0f} เท่า)",
            found=f"นอกเวลาส่วนใหญ่ใช้ไฟน้อย (ค่ากลาง {q.iloc[0]:.3f}) แต่ 1% บนสุดสูงถึง {q.iloc[1]:.2f} kWh ซึ่งมาจากห้องที่ใช้ไฟนอกเวลาสูง ช่วงมีคนกระจายกว้าง (ต่ำสุด {occ[E].min():.2f}, สูงสุด {occ[E].max():.2f}) จำนวนคนค่ากลาง {occ['occupancy_people'].median():.0f} คน",
            meaning="การใช้ไฟมี 2 ระดับชัดเจน การรวมสองช่วงเข้าด้วยกันจะซ่อนความต่าง ส่วนหางขวาของนอกเวลาคือพื้นที่ที่ควรตรวจสอบเพิ่มเติม",
            action="ดูห้องที่อยู่ในหางขวาของนอกเวลาในหน้า นอกเวลาและวันหยุด",
            use="ดูรูปร่างการกระจายของ kWh และจำนวนคน", read="กล่อง: เส้นกลางคือค่ากลาง จุดข้างในคือค่าเฉลี่ย ฮิสโทแกรม: แท่งสูงคือมีชั่วโมงเหล่านั้นมาก", method="บ็อกซ์พล็อตและฮิสโทแกรมแยกช่วงมีคน/นอกเวลา", n=len(d))

# ---------- tab 2: group comparison ----------
with tabs[2]:
    ask("ประเภทห้องและอาคารไหนใช้ไฟต่างกัน?", "groups")
    if len(occ) == 0:
        st.info("ต้องมีข้อมูลช่วงมีคนเพื่อเปรียบเทียบกลุ่ม เลือกประเภทวัน วันทำการ ที่ตัวกรองด้านบน", icon=":material/info:")
    else:
        def grp(col, label):
            g = occ.groupby(col).agg(rooms=("room_id", "nunique"), hours=(E, "size"), mean=(E, "mean"), median=(E, "median"), std=(E, "std"))
            t = d.groupby(col)[E].sum()
            g["total_kwh"] = t
            g["share"] = 100 * t / total
            g["note"] = np.where(g["rooms"] < SMALL, "กลุ่มเล็ก (ห้องน้อยกว่า %d)" % SMALL, "")
            g.index.name = label
            return g.sort_values("mean", ascending=False)
        by_type, by_bld = grp("room_type", "ประเภทห้อง"), grp("building_name", "อาคาร")
        c1, c2 = st.columns(2)
        for col_, g, key, ttl in [(c1, by_type, "st_type", "ประเภทห้อง"), (c2, by_bld, "st_bld", "อาคาร")]:
            with col_:
                f = go.Figure(go.Bar(y=g.index[::-1], x=g["mean"][::-1], orientation="h", marker_color=BLUE if ttl == "อาคาร" else NAVY,
                                     text=[f"{v:.2f} ({n} ห้อง{', กลุ่มเล็ก' if n < SMALL else ''})" for v, n in zip(g["mean"][::-1], g["rooms"][::-1])], textposition="outside"))
                style(f, 340, f"{ttl}ไหนใช้ไฟช่วงมีคนมากที่สุด?", legend=False); f.update_xaxes(range=[0, g["mean"].max() * 1.6], title="kWh ต่อห้องต่อชั่วโมง")
                show(f, key)
        show_cols = {"rooms": "ห้อง (n)", "hours": "ชั่วโมง (n)", "mean": "เฉลี่ย", "median": "ค่ากลาง", "std": "SD", "total_kwh": "รวม kWh", "share": "สัดส่วน (%)", "note": "หมายเหตุ"}
        t1, t2 = st.columns(2)
        t1.dataframe(by_type.rename(columns=show_cols).round(2), width="stretch")
        t2.dataframe(by_bld.rename(columns=show_cols).round(2), width="stretch")
        spread = 100 * (by_type["mean"].max() / by_type["mean"].min() - 1)
        explain(
            short=f"ประเภทห้องที่ใช้ไฟช่วงมีคนสูงสุดคือ {by_type.index[0]} ({by_type.iloc[0]['mean']:.2f} kWh) ต่ำสุด {by_type.index[-1]} ({by_type.iloc[-1]['mean']:.2f}) ต่างกัน {spread:.0f}%",
            found=f"อาคารสูงสุดคือ {by_bld.index[0]} ({by_bld.iloc[0]['mean']:.2f} kWh ต่อห้องต่อชั่วโมง) ต่ำสุด {by_bld.index[-1]} ({by_bld.iloc[-1]['mean']:.2f}) ประเภทห้องที่มีน้อยกว่า {SMALL} ห้องถูกติดป้ายกลุ่มเล็ก",
            meaning="ความต่างระหว่างกลุ่มส่วนใหญ่มาจากจำนวนเครื่องปรับอากาศของห้องในกลุ่ม ไม่ใช่ชนิดห้องโดยตรง ดูหน้า คน แอร์ อากาศ เพื่อควบคุมก่อนสรุป กลุ่มเล็กตีความด้วยความระวัง",
            action="เวลาเทียบกลุ่ม ให้เทียบกลุ่มที่มีแอร์ใกล้เคียงกัน และอ่านตัวเลขกลุ่มเล็กควบคู่กับรายห้อง",
            use="เทียบการใช้ไฟระหว่างประเภทห้องและอาคาร", read="แท่งยาวคือใช้ไฟเฉลี่ยสูง ตัวเลขท้ายแท่งคือค่าเฉลี่ยและจำนวนห้อง", method="ค่าเฉลี่ย kWh ต่อห้องต่อชั่วโมงเฉพาะช่วงมีคน แยกกลุ่ม", n=len(occ))

# ---------- tab 3: correlation matrix ----------
with tabs[3]:
    ask("ตัวแปรใดมีความสัมพันธ์กับการใช้ไฟ?", "grid_on")
    if len(occ) < 200:
        st.info("ข้อมูลช่วงมีคนน้อยเกินไปสำหรับคำนวณความสัมพันธ์ ขยายช่วงวันที่หรือเลือกวันทำการ", icon=":material/info:")
    else:
        relationship_bars(occ, E, "st_rbars")

# ---------- tab 4: time pattern ----------
with tabs[4]:
    ask("ใช้ไฟมากในเดือนไหน วันไหน ชั่วโมงไหน?", "calendar_month")
    mon = d.groupby("month").agg(n=(E, "size"), mean=(E, "mean"), median=(E, "median"), std=(E, "std"), total=(E, "sum"), temp=("temperature_c", "mean"))
    mon.index = [MONTHS[m - 1] for m in mon.index]
    st.markdown("**สถิติรายเดือน**")
    st.dataframe(mon.rename(columns={"n": "n (แถว)", "mean": "เฉลี่ย kWh/ชม.", "median": "ค่ากลาง", "std": "SD", "total": "รวม kWh", "temp": "อุณหภูมิเฉลี่ย"}).round(2), width="stretch")
    heat = d.groupby(["dow", "hour"])[E].mean().unstack()
    f = go.Figure(go.Heatmap(z=heat.values, x=heat.columns, y=[DAYS[i] for i in heat.index], colorscale=[[0, "#F3F7FC"], [0.5, SKY], [1, NAVY]],
                             colorbar=dict(title="kWh"), hovertemplate="%{y} %{x}:00 = %{z:.2f} kWh<extra></extra>"))
    style(f, 340, "วันไหน ชั่วโมงไหน ใช้ไฟมาก? (ยิ่งเข้มยิ่งมาก)", legend=False); f.update_xaxes(title="ชั่วโมง", dtick=2); f.update_yaxes(autorange="reversed")
    show(f, "st_heat")
    days_top = d.groupby("day").agg(total=(E, "sum"), temp=("temperature_c", "mean")).nlargest(5, "total")
    st.markdown("**5 วันที่ใช้ไฟรวมสูงสุด**")
    st.dataframe(days_top.reset_index().rename(columns={"day": "วันที่", "total": "ใช้ไฟรวม (kWh)", "temp": "อุณหภูมิเฉลี่ย (องศา)"}).assign(วันที่=lambda x: x["วันที่"].dt.strftime("%Y-%m-%d")).round(1), hide_index=True, width="stretch")
    pm, lm = mon["mean"].idxmax(), mon["mean"].idxmin()
    explain(
        short=f"เดือน {pm} เฉลี่ยสูงสุด ({mon.loc[pm, 'mean']:.2f} kWh/ชม.) เดือน {lm} ต่ำสุด ({mon.loc[lm, 'mean']:.2f}) ชั่วโมงเร่งด่วนอยู่ช่วงกลางวันวันจันทร์-ศุกร์",
        found=f"วันที่ใช้ไฟรวมสูงสุดคือ {days_top.index[0]:%Y-%m-%d} ({fmt(days_top.iloc[0]['total'])} kWh อุณหภูมิเฉลี่ย {days_top.iloc[0]['temp']:.1f} องศา) ทั้ง 5 วันสูงสุดอยู่ในเดือน {', '.join(sorted({MONTHS[x.month - 1] for x in days_top.index}))}",
        meaning="พบแนวโน้มที่ช่วงอากาศร้อนใช้ไฟสูงกว่า แต่ข้อมูลมีปีเดียว จึงแยกฤดูกาลกับการเพิ่มขึ้นจริงไม่ได้ และข้อมูลเป็น kWh รายชั่วโมง บอกค่ากำลังไฟสูงสุด (kW) ไม่ได้",
        action="ขอข้อมูลหลายปีเพื่อยืนยันแนวโน้ม และใช้แผนที่ความร้อนเพื่อวางเวลาตรวจ",
        use="ดูรูปแบบการใช้ไฟตามเดือน วัน และชั่วโมง", read="ยิ่งเข้มยิ่งใช้ไฟมาก แถวคือวันในสัปดาห์ คอลัมน์คือชั่วโมง", method="เฉลี่ยและรวม kWh ตามเดือน วัน ชั่วโมง", n=len(d))
