ชุดซ้อมแข่งทักษะการวิเคราะห์ข้อมูล (รายการที่ 59) - การใช้ไฟฟ้าในสถานศึกษา
=====================================================================
โจทย์: ค่าไฟสูงขึ้น ต้องการลดต้นทุนพลังงานและตรวจสอบพฤติกรรมการใช้ไฟที่ผิดปกติ
ข้อมูล: จำลองปี 2025, 5 อาคาร 40 ห้อง 40 มิเตอร์ รายชั่วโมง (ใช้เฉพาะคอลัมน์ที่มีจริง)

สิ่งที่อยู่ในชุดนี้
  data_raw/      ข้อมูลดิบที่ได้รับ (ไม่แก้ไข)
  notebooks/     01_cleaning.ipynb (ทำความสะอาด 5 ขั้น) -> 02_explore.ipynb (สำรวจ 4 ขั้น) รันแล้ว ไม่มี error
  data_clean/    ข้อมูลสะอาดและตารางสรุป (CSV/Parquet), ตารางค่าผิดปกติ, กระทบยอด, พจนานุกรมข้อมูล,
                 sample_first_week.csv = ไฟล์ตัวอย่างเล็กสำหรับทดสอบเร็ว
  dashboard/     เว็บแดชบอร์ด Streamlit (ไม่ต้องล็อกอิน) เมนูอยู่ด้านบน + ชุดทดสอบ + QUICK_GUIDE.md สำหรับกรรมการ
                 หน้า: ภาพรวม | สรุปผล | สถิติเบื้องต้น | จัดอันดับ | เจาะลึก | นอกเวลา | คน แอร์ อากาศ | คุณภาพข้อมูล | ปัญหาและแนวทาง | เพิ่มเติม (ข้อมูลที่ไม่มี, ส่งออกข้อมูล, คู่มือย่อ)
  docs/          infographic_user_manual.pdf (อินโฟกราฟิกคู่มือ 2 หน้า), infographic_page1/2.png, ไฟล์ต้นฉบับ HTML
  tools/         helpers.py ที่โน้ตบุ๊กใช้

รันแดชบอร์ดบนเครื่อง
  Windows: ดับเบิลคลิก dashboard/run_dashboard.bat
  อื่น ๆ : cd dashboard ; pip install -r requirements.txt ; streamlit run app.py   แล้วเปิด http://localhost:8501

รันโน้ตบุ๊กซ้ำ
  pip install -r requirements.txt   (ไฟล์อยู่ที่รากโฟลเดอร์)
  cd notebooks
  jupyter nbconvert --to notebook --execute --inplace 01_cleaning.ipynb
  jupyter nbconvert --to notebook --execute --inplace 02_explore.ipynb
  (ถ้าแก้โน้ตบุ๊ก 01 ให้คัดลอก data_clean/electricity_clean.parquet และไฟล์ csv สรุปไปไว้ที่ dashboard/data ด้วย)

ทดสอบแดชบอร์ด
  cd dashboard ; python tests/test_dashboard.py     (AppTest 143 รายการ)
  python tests/test_consistency.py   (เทียบตัวเลขไฟดิบ > ผลโน้ตบุ๊ก > แดชบอร์ด 15 รายการ)
  python tests/test_missing_data.py  (ไฟล์ข้อมูลหาย/เสีย ต้องขึ้นข้อความไทย)
  python tests/test_first_session.py 2   (บั๊กตัวกรองหาย: เซิร์ฟเวอร์ใหม่ เซสชันแรก) ต้องติดตั้ง playwright
  python tests/browser_check.py <url> A|B (เบราว์เซอร์จริง: ตัวกรอง เมนู ส่งออก และทุกหน้าทุกแท็บ)
  python tests/measure_load.py <url> out.md (จับเวลาโหลด ผลล่าสุดอยู่ที่ docs/performance_measurements.md)
  python preflight.py                (ตรวจก่อนรัน) | DEPLOY.md = แผน A ออนไลน์ / แผน B Windows

สถานะและข้อจำกัด
  - ไม่รวมสไลด์นำเสนอ (ยังไม่มีไฟล์ รอทีมยืนยัน)
  - หน้า สถิติเบื้องต้น ช้าสุด ราว 5-6 วินาที (หน้าอื่น 0.3-1.4 วินาที) ยังไม่ได้ปรับปรุงความเร็ว
  - ทดสอบบน Linux เท่านั้น: ยังไม่ได้ทดสอบ run_dashboard.bat บน Windows จริง และยังไม่ได้นำขึ้น Streamlit Cloud จริง
  - เกณฑ์ที่ตั้งเอง (ไฟนอกเวลาเกิน 15%, ช่วงเย็นสูงกว่า 3 เท่า ฯลฯ) เป็นค่าตั้งต้น ไม่ใช่มาตรฐานทางการ
  - ข้อมูลปีเดียว ไม่มีอัตราค่าไฟ จึงรายงานเป็น kWh และยืนยันไม่ได้ว่าค่าไฟสูงขึ้นเทียบปีก่อน
  - โค้ดและคอมเมนต์เป็นภาษาอังกฤษ ภาษาไทยอยู่ที่หัวข้อ ชื่อกราฟ และคำอธิบาย
