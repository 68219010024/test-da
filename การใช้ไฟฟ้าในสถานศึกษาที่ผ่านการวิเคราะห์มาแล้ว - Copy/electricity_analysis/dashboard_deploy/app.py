"""Entry point: page config, top menu (5 groups), shared filters (kept here so they survive page switches). No login."""
import streamlit as st

st.set_page_config(page_title="วิเคราะห์การใช้ไฟฟ้าในสถานศึกษา", page_icon=":material/bolt:", layout="wide", initial_sidebar_state="collapsed")

from core.ui import inject_css
from core.data import render_filters

inject_css()

# 5 menus: overview -> deep analysis -> data quality -> insight and action -> data and export
menus = {
    "ภาพรวม": [
        st.Page("pages/overview.py", title="ภาพรวม", icon=":material/dashboard:", default=True, url_path="overview"),
    ],
    "วิเคราะห์เชิงลึก": [
        st.Page("pages/stats.py", title="สถิติเบื้องต้น", icon=":material/calculate:", url_path="stats"),
        st.Page("pages/ranking.py", title="จัดอันดับ", icon=":material/leaderboard:", url_path="ranking"),
        st.Page("pages/drilldown.py", title="เจาะลึก อาคาร ห้อง ช่วงเวลา", icon=":material/account_tree:", url_path="drilldown"),
        st.Page("pages/offhours.py", title="นอกเวลาและวันหยุด", icon=":material/dark_mode:", url_path="offhours"),
        st.Page("pages/factors.py", title="ความสัมพันธ์ (คน แอร์ อากาศ)", icon=":material/thermostat:", url_path="factors"),
    ],
    "คุณภาพข้อมูล": [
        st.Page("pages/dataquality.py", title="คุณภาพข้อมูล", icon=":material/fact_check:", url_path="dataquality"),
    ],
    "Insight และแนวทาง": [
        st.Page("pages/summary.py", title="สรุปผลการวิเคราะห์", icon=":material/target:", url_path="summary"),
        st.Page("pages/problems.py", title="ปัญหาและแนวทางแก้ไข", icon=":material/build_circle:", url_path="problems"),
    ],
    "ข้อมูลและส่งออก": [
        st.Page("pages/data.py", title="ตารางข้อมูลและพจนานุกรม", icon=":material/table_view:", url_path="data"),
        st.Page("pages/export.py", title="ส่งออกข้อมูล", icon=":material/download:", url_path="export"),
        st.Page("pages/missing.py", title="ข้อมูลที่ไม่มี", icon=":material/help_center:", url_path="missing"),
        st.Page("pages/guide.py", title="คู่มือย่อ", icon=":material/menu_book:", url_path="guide"),
    ],
}
pg = st.navigation(menus, position="top")
render_filters()
try:
    pg.run()
except Exception:
    # StopException / RerunException are BaseException in Streamlit, so normal st.stop() and reruns are not caught here
    st.error("หน้านี้แสดงผลไม่สำเร็จ กรุณาลองกดล้างตัวกรอง หรือรีเฟรชหน้า ถ้ายังไม่หายให้เปลี่ยนไปหน้าอื่นก่อนแล้วแจ้งผู้ดูแลระบบ", icon=":material/error:")
    with st.expander("รายละเอียดสำหรับผู้ดูแลระบบ", icon=":material/bug_report:"):
        import traceback
        st.code(traceback.format_exc(limit=3))
