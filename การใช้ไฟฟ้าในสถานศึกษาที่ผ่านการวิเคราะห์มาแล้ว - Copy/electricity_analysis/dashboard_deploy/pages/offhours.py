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

banner("นอกเวลา วันหยุด และห้องคอมพิวเตอร์", "พื้นที่ที่ใช้ไฟสูงผิดปกติเมื่อไม่มีคนใช้งาน (ควรตรวจสอบเพิ่มเติม ข้อมูลไม่ระบุสาเหตุ)")
criteria_note(thr)
note_high_vs_waste()
tabs = st.tabs([":material/dark_mode: นอกเวลา", ":material/weekend: วันหยุด", ":material/computer: ห้องคอมพิวเตอร์"])
with tabs[0]:
    check = room[room["flag_off_share"]].sort_values("off_share_pct", ascending=False)
    top_off = room.dropna(subset=["off_share_pct"]).nlargest(5, "off_share_pct")
    ask("พื้นที่ไหนใช้ไฟนอกเวลาสูงที่สุด?", "dark_mode")
    rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"ไฟนอกเวลา {r['off_share_pct']:.1f}% ของไฟห้อง", "sub": f"{r['building_name']} | {r['pattern']} | พื้นที่ที่ควรตรวจสอบเพิ่มเติม"} for _, r in top_off.head(3).iterrows()])
    c1, c2 = st.columns(2)
    with c1:
        f = go.Figure(go.Bar(y=(top_off["room_id"] + " " + top_off["room_type"])[::-1], x=top_off["off_share_pct"][::-1], orientation="h",
                             marker_color=[RED if v > thr["off_share_pct"] else SKY for v in top_off["off_share_pct"][::-1]],
                             text=[f"{v:.1f}%" for v in top_off["off_share_pct"][::-1]], textposition="outside"))
        f.add_vline(x=thr["off_share_pct"], line_dash="dash", line_color=SLATE)
        style(f, 340, f"สัดส่วนไฟนอกเวลา (เส้นประ = เกณฑ์คัดกรองเบื้องต้น {thr['off_share_pct']:.0f}%)", legend=False); f.update_xaxes(range=[0, max(top_off["off_share_pct"].max() * 1.25, thr["off_share_pct"] * 1.3)], title="% ของไฟทั้งหมดของห้อง")
        show(f, "ov_off5")
    with c2:
        hp = d[off].groupby(["room_id", "hour"])[E].mean().unstack()
        f = go.Figure()
        palette = [RED, AMBER, NAVY, BLUE, SLATE]
        for i, rid in enumerate(check["room_id"].head(5)):
            f.add_scatter(x=hp.columns, y=hp.loc[rid], name=rid, line=dict(width=2.5, color=palette[i % 5]))
        typ = room.loc[~room["flag_off_share"], "room_id"]
        if len(typ):
            f.add_scatter(x=hp.columns, y=hp.loc[hp.index.isin(typ)].median(), name="ห้องปกติ (ค่ากลาง)", line=dict(width=3, dash="dash", color="#8A94A6"))
        style(f, 340, "ห้องที่ควรตรวจ ใช้ไฟสูงช่วงชั่วโมงไหนของนอกเวลา?"); f.update_xaxes(title="ชั่วโมง (เฉพาะชั่วโมงที่ไม่มีคน)", dtick=2); f.update_yaxes(title="kWh ต่อชั่วโมง")
        show(f, "ov_offhp")
    best = top_off.iloc[0]
    n_eve = int(room["flag_evening_block"].sum())
    typ_share = room.loc[~room["flag_off_share"], "off_share_pct"].median()
    explain(
        short=f"{len(check)} จาก {N} ห้องมีสัดส่วนไฟนอกเวลาเกิน {thr['off_share_pct']:.0f}% (เกณฑ์ตั้งต้น) สูงสุดคือ {best['room_id']} {best['off_share_pct']:.1f}%",
        found=f"ห้อง {best['room_id']} ใช้ไฟนอกเวลา {best['off_share_pct']:.1f}% ของไฟทั้งหมดของห้อง (ห้องทั่วไปประมาณ {typ_share:.1f}%) มี {n_eve} ห้องที่ใช้ไฟสูงช่วง 18:00-22:59 ในชั่วโมงที่จำนวนคนเป็น 0 สม่ำเสมอในช่วงข้อมูลที่เลือก",
        meaning="เป็นการใช้ไฟฟ้าสูงผิดปกตินอกเวลาการใช้งาน ข้อมูลบอกไม่ได้ว่ามาจากอุปกรณ์ใด จึงเป็นพื้นที่ที่ควรตรวจสอบเพิ่มเติม เกณฑ์นี้เป็นค่าตั้งต้น ไม่ใช่มาตรฐานทางการ",
        action="ให้ฝ่ายอาคารสถานที่ตรวจห้องตามรายชื่อภายใน 1 สัปดาห์ ดูการตั้งเวลาเปิด-ปิดและสถานะอุปกรณ์หลัง 18:00 น. แล้วเทียบผลหลังตรวจ",
        use="หาห้องที่ใช้ไฟนอกเวลาสูง", read="กราฟซ้ายแท่งแดงเกินเกณฑ์ เส้นประคือเกณฑ์ กราฟขวาเส้นที่พุ่งขึ้นช่วงเย็นคือห้องที่ควรตรวจ", method="นอกเวลา = ชั่วโมงที่จำนวนคนเป็น 0  สัดส่วน = kWh นอกเวลา / kWh ทั้งหมดของห้อง", n=N)

    ask("ประเภทห้องและอาคารไหนมีห้องที่ควรตรวจสอบมากที่สุด?", "groups")
    def group_tbl(col, label):
        t = room.groupby(col).agg(ห้อง=("room_id", "count"), ห้องที่ควรตรวจ=("flag_off_share", "sum"), ไฟนอกเวลาเฉลี่ย=("off_share_pct", "mean"))
        t["สัดส่วนห้องที่ควรตรวจ (%)"] = 100 * t["ห้องที่ควรตรวจ"] / t["ห้อง"]
        t["หมายเหตุ"] = np.where(t["ห้อง"] < thr["small_rooms"], "กลุ่มเล็ก (ห้องน้อยกว่า %d) ตีความด้วยความระวัง" % thr["small_rooms"], "")
        t.index.name = label
        return t.sort_values(["สัดส่วนห้องที่ควรตรวจ (%)", "ไฟนอกเวลาเฉลี่ย"], ascending=False).round(1).reset_index()
    g1, g2 = st.columns(2)
    g1.dataframe(group_tbl("room_type", "ประเภทห้อง"), hide_index=True, width="stretch")
    g2.dataframe(group_tbl("building_name", "อาคาร"), hide_index=True, width="stretch")

with tabs[1]:
    ask("วันหยุด พื้นที่ไหนยังใช้ไฟสูง?", "weekend")
    wk = room.dropna(subset=["weekend_mean_kwh_h"])
    if len(wk) == 0:
        st.info("ไม่มีข้อมูลวันหยุดในตัวกรองที่เลือก เลือกประเภทวัน วันหยุด ที่แถบด้านซ้าย", icon=":material/info:")
    else:
        top_we = wk.nlargest(5, "weekend_mean_kwh_h")
        bw = wk.groupby("building_name")["weekend_mean_kwh_h"].mean().sort_values(ascending=False)
        rank_cards([{"label": f"{r['room_id']} ({r['room_type']})", "value": f"{r['weekend_mean_kwh_h']:.2f} kWh ต่อชั่วโมง", "sub": r["building_name"]} for _, r in top_we.head(3).iterrows()])
        c1, c2 = st.columns(2)
        with c1:
            f = go.Figure(go.Bar(y=(top_we["room_id"] + " " + top_we["room_type"])[::-1], x=top_we["weekend_mean_kwh_h"][::-1], orientation="h", marker_color=AMBER,
                                 text=[f"{v:.2f}" for v in top_we["weekend_mean_kwh_h"][::-1]], textposition="outside"))
            style(f, 300, "ห้องไหนยังใช้ไฟสูงในวันหยุด? (Top 5)", legend=False); f.update_xaxes(range=[0, top_we["weekend_mean_kwh_h"].max() * 1.25], title="kWh ต่อชั่วโมง")
            show(f, "ov_we5")
        with c2:
            f = go.Figure(go.Bar(y=bw.index[::-1], x=bw.values[::-1], orientation="h", marker_color=SKY, text=[f"{v:.2f}" for v in bw.values[::-1]], textposition="outside"))
            style(f, 300, "อาคารไหนยังใช้ไฟสูงในวันหยุด? (เฉลี่ยต่อห้อง)", legend=False); f.update_xaxes(range=[0, bw.max() * 1.25], title="kWh ต่อชั่วโมง")
            show(f, "ov_webld")
        wd_all = d.loc[d["day_type"] == "weekday", E].mean()
        we_all = d.loc[d["day_type"] == "weekend", E].mean()
        med_we = wk["weekend_mean_kwh_h"].median()
        explain(
            short=f"วันหยุดใช้ไฟเฉลี่ย {we_all:.2f} kWh/ห้อง/ชม." + (f" ต่ำกว่าวันทำการ {100 * (1 - we_all / wd_all):.0f}%" if pd.notna(wd_all) else "") + f" ห้องที่ยังสูงสุดคือ {top_we.iloc[0]['room_id']} ({top_we.iloc[0]['weekend_mean_kwh_h']:.2f})",
            found=f"ห้องทั่วไปใช้ไฟวันหยุดค่ากลาง {med_we:.3f} kWh/ชม. ห้องใน 5 อันดับสูงกว่า {top_we['weekend_mean_kwh_h'].min() / med_we:.1f}-{top_we['weekend_mean_kwh_h'].max() / med_we:.1f} เท่า อาคารสูงสุดคือ {bw.index[0]}",
            meaning="วันหยุดในข้อมูลคือเสาร์-อาทิตย์เท่านั้น (ไม่มีปฏิทินนักขัตฤกษ์) ห้องที่ยังใช้ไฟสูงทั้งที่ไม่มีคน ควรตรวจสอบเพิ่มเติม",
            action="นำรายชื่อเข้าตรวจพร้อมรายการนอกเวลา และขอปฏิทินวันหยุดของสถานศึกษาเพื่อแยกวันหยุดพิเศษ",
            use="หาห้องที่ยังใช้ไฟสูงในวันหยุด", read="แท่งยาวคือใช้ไฟวันหยุดสูง", method="เฉลี่ย kWh ต่อห้องต่อชั่วโมงเฉพาะเสาร์-อาทิตย์", n=int((d["day_type"] == "weekend").sum()))

with tabs[2]:
    ask("ห้องคอมพิวเตอร์ยังใช้ไฟต่อเนื่องแค่ไหนในช่วงที่ไม่มีคน?", "computer")
    comp = room[room["room_type"] == "ห้องคอมพิวเตอร์"].sort_values("other_off_mean_kwh_h", ascending=False)
    if len(comp) == 0:
        st.info("ไม่มีห้องคอมพิวเตอร์ในตัวกรองที่เลือก เลือกประเภทห้อง ห้องคอมพิวเตอร์ ที่แถบด้านซ้าย", icon=":material/info:")
    else:
        others = room[room["room_type"] != "ห้องคอมพิวเตอร์"]
        by_type = room.groupby("room_type").agg(rooms=("room_id", "count"), v=("other_off_mean_kwh_h", "median")).sort_values("v", ascending=False)
        c1, c2 = st.columns(2)
        with c1:
            f = go.Figure(go.Bar(y=(comp["room_id"] + " " + comp["building_name"])[::-1], x=comp["other_off_mean_kwh_h"][::-1], orientation="h", marker_color=BLUE,
                                 text=[f"{v:.2f}" for v in comp["other_off_mean_kwh_h"][::-1]], textposition="outside"))
            if len(others):
                f.add_vline(x=others["other_off_mean_kwh_h"].median(), line_dash="dash", line_color=SLATE)
            style(f, 330, "ห้องคอมพิวเตอร์ยังใช้ไฟต่อเนื่องแค่ไหนเมื่อไม่มีคน? (เส้นประ = ค่ากลางห้องประเภทอื่น)", legend=False); f.update_xaxes(range=[0, comp["other_off_mean_kwh_h"].max() * 1.35], title="kWh ต่อชั่วโมง")
            show(f, "ov_comp")
        with c2:
            f = go.Figure(go.Bar(y=by_type.index[::-1], x=by_type["v"][::-1], orientation="h", marker_color=[AMBER if k == "ห้องคอมพิวเตอร์" else SKY for k in by_type.index[::-1]],
                                 text=[f"{v:.2f} ({n} ห้อง{', กลุ่มเล็ก' if n < thr['small_rooms'] else ''})" for v, n in zip(by_type["v"][::-1], by_type["rooms"][::-1])], textposition="outside"))
            style(f, 330, "ประเภทห้องไหนใช้ไฟช่วงไม่มีคนมากที่สุด? (ไม่รวมช่วง 18:00-22:59)", legend=False); f.update_xaxes(range=[0, by_type["v"].max() * 1.7], title="kWh ต่อชั่วโมง")
            show(f, "ov_comptype")
        oth_med = others["other_off_mean_kwh_h"].median() if len(others) else float("nan")
        same = comp["other_off_mean_kwh_h"].max() - comp["other_off_mean_kwh_h"].min() < 0.02
        explain(
            short=f"ห้องคอมพิวเตอร์ {len(comp)} ห้องใช้ไฟช่วงไม่มีคนค่ากลาง {comp['other_off_mean_kwh_h'].median():.2f} kWh/ชม." + (f" สูงกว่าห้องอื่น {comp['other_off_mean_kwh_h'].median() / oth_med:.1f} เท่า" if oth_med == oth_med and oth_med > 0 else ""),
            found=f"ค่าอยู่ระหว่าง {comp['other_off_mean_kwh_h'].min():.2f}-{comp['other_off_mean_kwh_h'].max():.2f} kWh/ชม." + (" ทุกห้องใกล้เคียงกัน จึงไม่มีห้องใดเด่นกว่า" if same else f" ห้องสูงสุดคือ {comp.iloc[0]['room_id']}") + f" รวมไฟนอกเวลา {fmt(comp['off_kwh'].sum())} kWh ในช่วงที่เลือก",
            meaning="อาจมีการใช้พลังงานจากอุปกรณ์หรือระบบที่ทำงานต่อเนื่อง จึงควรตรวจสอบเพิ่มเติม ข้อมูลไม่ได้ระบุอุปกรณ์ จึงสรุปสาเหตุไม่ได้ และอาจเป็นการใช้งานที่จำเป็น",
            action="สอบถามผู้ดูแลห้องว่ามีอุปกรณ์ที่ต้องเปิดตลอดเวลาหรือไม่ ถ้าไม่จำเป็นให้ตั้งเวลาปิด (ภายใน 1 เดือน)",
            use="ดูว่าห้องคอมพิวเตอร์ใช้ไฟต่อเนื่องในช่วงไม่มีคนมากน้อยเพียงใด", read="แท่งยาวคือใช้ไฟช่วงไม่มีคนสูง เส้นประคือค่ากลางของห้องประเภทอื่น", method="ค่าเฉลี่ย kWh ต่อชั่วโมงเฉพาะชั่วโมงที่ไม่มีคน ตัดช่วง 18:00-22:59 ออก", n=len(comp))

