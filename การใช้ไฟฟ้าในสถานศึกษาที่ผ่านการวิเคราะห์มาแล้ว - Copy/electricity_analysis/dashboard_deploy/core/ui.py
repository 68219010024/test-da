"""UI helpers: electricity-in-school theme (navy + electric blue + amber), black Material icons (no emoji),
chart explanation boxes with short/full mode, consistent Plotly style."""
import streamlit as st
import plotly.graph_objects as go

NAVY, BLUE, SKY, AMBER, INK, MUTED, PANEL = "#0B2F6B", "#1E6FD9", "#8DB9F2", "#F5B700", "#0F1B2D", "#5B6B82", "#F3F7FC"
RED, ORANGE, SLATE = "#C62828", "#E08A00", "#5B7FA6"
SEV_COLOR = {"สูง": RED, "กลาง": ORANGE, "ต่ำ": SLATE}
SEV_BADGE = {"สูง": ":red-badge[ความรุนแรงสูง]", "กลาง": ":orange-badge[ความรุนแรงกลาง]", "ต่ำ": ":blue-badge[ความรุนแรงต่ำ]"}
FONT = "Sarabun, 'Noto Sans Thai', Tahoma, 'Leelawadee UI', sans-serif"

# black lightning-bolt icon used in the banner (inline SVG, no emoji)
BOLT_SVG = ('<svg width="34" height="34" viewBox="0 0 24 24" fill="#111111" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z"/></svg>')

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: {FONT}; }}
.block-container {{ padding-top: 3.4rem; max-width: 1500px; }}
.banner {{ display:flex; align-items:center; gap:16px; background:linear-gradient(90deg,{PANEL},#FFFFFF);
  border-left:10px solid {AMBER}; border-bottom:3px solid {NAVY}; padding:14px 20px; border-radius:6px; margin-bottom:10px; }}
.banner h1 {{ color:{NAVY}; margin:0; font-size:1.75rem; line-height:1.2; font-weight:700; }}
.banner p {{ color:{MUTED}; margin:2px 0 0 0; font-size:.95rem; }}
[data-testid="stMetric"] {{ background:{PANEL}; border:1px solid #D6E2F3; border-top:4px solid {NAVY}; border-radius:8px; padding:10px 14px; }}
[data-testid="stMetricValue"] {{ color:{NAVY}; font-weight:700; }}
h2, h3 {{ color:{NAVY}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color:{AMBER}; height:4px; }}
.stTabs [data-baseweb="tab"] p {{ font-weight:600; }}
section[data-testid="stSidebar"] {{ border-right:4px solid {AMBER}; }}
div[data-testid="stExpander"] summary p {{ font-weight:600; color:{NAVY}; }}
.small-note {{ color:{MUTED}; font-size:.82rem; }}
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:none; }} }}
[data-testid="stMetric"], div[data-testid="stVerticalBlockBorderWrapper"] {{ animation: fadeUp .45s ease-out both; transition: box-shadow .2s ease; }}
[data-testid="stMetric"]:hover {{ box-shadow:0 3px 10px rgba(11,47,107,.15); }}
@media (prefers-reduced-motion: reduce) {{ [data-testid="stMetric"], div[data-testid="stVerticalBlockBorderWrapper"] {{ animation:none; transition:none; }} }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def banner(title, subtitle):
    st.markdown(f'<div class="banner">{BOLT_SVG}<div><h1>{title}</h1><p>{subtitle}</p></div></div>', unsafe_allow_html=True)


def section(title, icon, sub=None):
    """Section heading with a black Material icon."""
    st.markdown(f"### :material/{icon}: {title}")
    if sub:
        st.caption(sub)


def fmt(x, d=0):
    return format(round(float(x), d), ",.%df" % d)


def style(fig, height=380, title=None, legend=True):
    """Apply the shared Plotly style."""
    fig.update_layout(
        height=height, title=dict(text=title, font=dict(size=15, color=NAVY)) if title else None,
        font=dict(family=FONT, size=13, color=INK), plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=50 if title else 20, b=60 if legend else 10), showlegend=legend,
        colorway=[BLUE, AMBER, NAVY, SKY, SLATE, RED],
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
        hoverlabel=dict(font_family=FONT))
    fig.update_xaxes(gridcolor="#E6ECF5", zeroline=False, linecolor="#C9D5E6")
    fig.update_yaxes(gridcolor="#E6ECF5", zeroline=False, linecolor="#C9D5E6")
    return fig


def show(fig, key):
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}})


def explain(short, found, meaning, action, use, read, method, n=None):
    """Chart explanation. Sidebar switch decides: short = one line, full = one line + expandable detail."""
    nn = f" (n={fmt(n)})" if n is not None else ""
    st.markdown(f":material/info: **สรุปสั้น{nn}:** {short}")
    if st.session_state.get("mode", "เต็ม") == "เต็ม":
        with st.expander("ดูวิธีวิเคราะห์และรายละเอียด", icon=":material/manage_search:"):
            st.markdown(f":material/search: **What (พบอะไร):** {found}")
            st.markdown(f":material/lightbulb: **So What (มีความหมายอย่างไร):** {meaning}")
            st.markdown(f":material/flag: **Now What (ควรทำอะไรต่อ):** {action}")
            st.caption(f"ใช้ดูอะไร: {use}  |  อ่านอย่างไร: {read}  |  วิเคราะห์ด้วยวิธี: {method}")


def empty_state(msg="ไม่พบข้อมูลตามตัวกรองที่เลือก"):
    st.warning(msg + " ลองกดปุ่มล้างตัวกรองที่แถบด้านซ้าย หรือขยายช่วงวันที่/เพิ่มอาคาร", icon=":material/search_off:")
    st.stop()


# ---------------- question headings, ranking cards, self-set criteria notice ----------------
CRITERIA_TEXT = "เกณฑ์นี้ใช้สำหรับคัดกรองเบื้องต้น ไม่ใช่มาตรฐานทางการ และสามารถปรับเปลี่ยนได้ตามบริบทหรือข้อมูลจริง"
RANK_ICONS = [":material/emoji_events:", ":material/military_tech:", ":material/workspace_premium:"]


def ask(text, icon="help"):
    """Question heading shown above a chart: what does this chart answer?"""
    st.markdown(f"#### :material/{icon}: {text}")


def rank_cards(items):
    """Top-3 podium cards. items = [{'label','value','sub'}]. Black Material icons instead of medals."""
    if not items:
        return
    cols = st.columns(len(items))
    for i, (col, it) in enumerate(zip(cols, items)):
        with col:
            with st.container(border=True):
                st.markdown(f"{RANK_ICONS[i]} **อันดับ {i + 1}**")
                st.markdown(f"**{it['label']}**")
                st.markdown(it["value"])
                if it.get("sub"):
                    st.caption(it["sub"])


def criteria_note(thr, detail=True):
    """Visible notice for every self-set threshold + a table of where each value comes from."""
    st.info(f"**เกณฑ์ที่ใช้:** ไฟนอกเวลาเกิน {thr['off_share_pct']:.0f}% ของไฟห้อง และช่วงเย็นสูงกว่าช่วงอื่นนอกเวลา {thr['evening_ratio']:.1f} เท่า เป็นค่าตั้งต้นที่ทีมตั้งเอง "
            f"{CRITERIA_TEXT} (ปรับได้ที่ตัวกรองด้านบน)", icon=":material/rule:")
    if detail:
        import pandas as pd
        with st.expander("ดูรายการเกณฑ์ทั้งหมดและที่มา", icon=":material/rule:"):
            st.dataframe(pd.DataFrame({
                "เกณฑ์": ["สัดส่วนไฟนอกเวลาที่ควรตรวจ", "ช่วงเย็น (18:00-22:59) สูงกว่าช่วงอื่นนอกเวลา", "ฐานไฟต่อเนื่องสูงกว่าห้องอื่น", "ระดับความรุนแรงสูง/กลาง (ส่วนเกินเทียบไฟรวม)",
                          "กลุ่มเล็ก (จำนวนห้อง)", "ค่าสูงผิดปกติ"],
                "ค่า": [f"{thr['off_share_pct']:.0f}%", f"{thr['evening_ratio']:.1f} เท่า", f"{thr['standby_x']:.0f} เท่าของค่ากลาง", f"{thr['impact_high']:.1f}% / {thr['impact_mid']:.1f}%",
                        f"น้อยกว่า {thr['small_rooms']} ห้อง", "สูงกว่า Q3+3xIQR และเกิน 3 เท่าของค่ากลางของช่วงเวลาเดียวกัน"],
                "ที่มา": ["ทีมกำหนดเอง (ค่าตั้งต้น ปรับได้)", "ทีมกำหนดเอง (ค่าตั้งต้น ปรับได้) ช่วงเวลาเลือกจากรูปแบบที่พบในข้อมูล", "ทีมกำหนดเอง (ค่าตั้งต้น)",
                          "ทีมกำหนดเอง (ค่าตั้งต้น)", "ทีมกำหนดเอง (ค่าตั้งต้น)", "หลักสถิติทั่วไป (IQR) ผสมค่าที่ทีมเลือก (3 เท่า)"]}), hide_index=True, width="stretch")
            st.caption(CRITERIA_TEXT)


HIGH_VS_WASTE = ("ใช้ไฟสูง ไม่เท่ากับ ใช้ไฟสิ้นเปลือง: ข้อมูลนี้บอกได้ว่าพื้นที่ไหนใช้ไฟสูงหรือสูงผิดปกติ แต่ไม่มีตารางการใช้ห้อง วัตถุประสงค์การใช้งาน หรือข้อมูลอุปกรณ์ "
                 "จึงสรุปไม่ได้ว่าสิ้นเปลืองหรือไม่ ต้องตรวจสอบเพิ่มเติม")


def note_high_vs_waste():
    st.caption(f":material/balance: {HIGH_VS_WASTE}")


def relationship_bars(occ, E, key):
    """Simple bar chart: how strongly each factor goes together with kWh (occupied hours). Longer bar = stronger. No matrix, no jargon."""
    import pandas as pd
    import plotly.graph_objects as go
    names = {"air_conditioner_count": "จำนวนแอร์", "occupancy_people": "จำนวนคน", "temperature_c": "อุณหภูมิ", "relative_humidity_percent": "ความชื้น", "area_m2": "พื้นที่ห้อง"}
    r = pd.Series({lab: occ[col].corr(occ[E]) for col, lab in names.items()}).dropna()
    order = r.abs().sort_values()
    lvl = lambda v: "เกี่ยวข้องมาก" if abs(v) >= 0.7 else ("ปานกลาง" if abs(v) >= 0.4 else "เกี่ยวข้องน้อย")
    fig = go.Figure(go.Bar(y=list(order.index), x=[abs(r[k]) for k in order.index], orientation="h", marker_color=[BLUE if r[k] >= 0 else ORANGE for k in order.index],
                           text=[f"{lvl(r[k])} ({r[k]:+.2f})" for k in order.index], textposition="outside"))
    style(fig, 320, "อะไรเกี่ยวข้องกับการใช้ไฟมากที่สุด? (ช่วงมีคน สีน้ำเงิน = เพิ่มไปด้วยกัน สีส้ม = สวนทางกัน)", legend=False)
    fig.update_xaxes(range=[0, 1.4], title="ยิ่งแท่งยาว ยิ่งเกี่ยวข้องกับการใช้ไฟ (0 = ไม่เกี่ยว, 1 = เกี่ยวมาก)")
    show(fig, key)
    top = order.index[::-1]
    explain(
        short=f"ในช่วงมีคน {top[0]} เกี่ยวข้องกับการใช้ไฟมากที่สุด ({r[top[0]]:+.2f}) รองลงมาคือ {top[1]} ({r[top[1]]:+.2f})",
        found=f"{top[0]} {lvl(r[top[0]])} ({r[top[0]]:+.2f}) {top[1]} {lvl(r[top[1]])} ({r[top[1]]:+.2f})" + (f" ส่วนพื้นที่ห้อง {lvl(r['พื้นที่ห้อง'])} ({r['พื้นที่ห้อง']:+.2f})" if "พื้นที่ห้อง" in r else ""),
        meaning="พบความสัมพันธ์ แต่ไม่ได้แปลว่าเป็นสาเหตุโดยตรง และข้อมูลมีปีเดียว ตัวแปรบางตัวเปลี่ยนไปพร้อมกัน (เช่น อุณหภูมิกับความชื้น) จึงแยกผลยาก",
        action="เวลาเทียบห้อง ให้เทียบกับห้องที่มีแอร์เท่ากัน และอย่าสรุปว่าตัวแปรใดเป็นสาเหตุจนกว่าจะมีข้อมูลเพิ่ม",
        use="ดูว่าตัวแปรไหนไปด้วยกันกับการใช้ไฟ", read="แท่งยาว = เกี่ยวข้องมาก ตัวเลขในวงเล็บคือค่า r (-1 ถึง +1)", method="ค่าสหสัมพันธ์แบบเพียร์สัน (r) ระหว่าง kWh กับแต่ละตัวแปร เฉพาะช่วงมีคน", n=len(occ))
