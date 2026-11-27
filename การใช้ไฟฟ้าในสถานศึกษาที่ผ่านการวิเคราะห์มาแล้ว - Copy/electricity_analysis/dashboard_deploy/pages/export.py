"""Export page: every table and the full report, with the filters recorded."""
import streamlit as st
from core.ui import banner, section, fmt
from core.data import get_ctx
from core.analysis import room_table, problems
from core.export import excel_report, prob_export, room_export, csv_bytes, hourly_csv

ctx = get_ctx()
d, A = ctx["d"], ctx["all"]
room = room_table(ctx)
probs = problems(ctx, room)
banner("ส่งออกข้อมูลที่วิเคราะห์", "ไฟล์ตรงกับตัวกรองที่เลือก และบันทึกเงื่อนไขการกรองกับเกณฑ์ตั้งต้นไว้ในไฟล์ Excel")

section("เงื่อนไขที่ใช้ส่งออก", "filter_alt")
for k, v in ctx["desc"].items():
    st.markdown(f"- **{k}:** {v}")
st.markdown(f"- **จำนวนแถวรายชั่วโมงที่เลือก:** {fmt(len(d))} | **ห้อง:** {len(room)}")

section("ดาวน์โหลด", "download")
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        st.markdown("**รายงานสรุป (Excel)**")
        st.caption("10 ชีต: เงื่อนไขการกรอง เกณฑ์ ปัญหาและแนวทาง จัดอันดับห้อง สรุปอาคาร รายเดือน รายชั่วโมง ค่าผิดปกติ ข้อมูลที่ไม่มี พจนานุกรม")
        st.download_button("ดาวน์โหลดรายงาน Excel", excel_report(ctx), "electricity_report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", icon=":material/summarize:", width="stretch", key="x_xlsx")
    with st.container(border=True):
        st.markdown("**ปัญหาและแนวทางแก้ไข (CSV)**")
        st.download_button("ดาวน์โหลด", csv_bytes(prob_export(probs)), "problems_and_actions.csv", "text/csv", icon=":material/description:", width="stretch", key="x_prob")
    with st.container(border=True):
        st.markdown("**จัดอันดับรายห้อง (CSV)**")
        st.download_button("ดาวน์โหลด", csv_bytes(room_export(room)), "room_ranking.csv", "text/csv", icon=":material/table_chart:", width="stretch", key="x_room")
with c2:
    with st.container(border=True):
        st.markdown("**ตารางค่าผิดปกติ (CSV)**")
        out = A["out_log"]
        st.download_button("ดาวน์โหลด", csv_bytes(out), "outliers_log.csv", "text/csv", icon=":material/report:", width="stretch", key="x_out")
    with st.container(border=True):
        st.markdown("**พจนานุกรมข้อมูลและข้อมูลที่ไม่มี (CSV)**")
        a, b = st.columns(2)
        a.download_button("พจนานุกรม", csv_bytes(A["dd"]), "data_dictionary.csv", "text/csv", icon=":material/menu_book:", width="stretch", key="x_dd")
        b.download_button("ข้อมูลที่ไม่มี", csv_bytes(A["miss"]), "missing_data.csv", "text/csv", icon=":material/help_center:", width="stretch", key="x_miss")
    with st.container(border=True):
        st.markdown("**ข้อมูลรายชั่วโมงตามตัวกรอง (CSV)**")
        st.caption(f"ไฟล์ใหญ่ ({fmt(len(d))} แถว) กดเตรียมไฟล์ก่อน")
        if st.button("เตรียมไฟล์ข้อมูลรายชั่วโมง", icon=":material/hourglass_top:", width="stretch", key="x_prep"):
            st.session_state["hourly_ready"] = (ctx["key"], hourly_csv(ctx))
        ready = st.session_state.get("hourly_ready")
        if ready and ready[0] == ctx["key"]:
            st.download_button("ดาวน์โหลดข้อมูลรายชั่วโมง", ready[1], "electricity_hourly_filtered.csv", "text/csv", icon=":material/download:", width="stretch", key="x_hourly")
        elif ready:
            st.caption("ตัวกรองเปลี่ยนแล้ว กดเตรียมไฟล์ใหม่")
