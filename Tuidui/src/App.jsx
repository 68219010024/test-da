import React, { useState } from "react";

const projects = [
  {
    number: "01",
    name: "บ้านใบไม้",
    type: "แบรนด์ไลฟ์สไตล์ · เว็บไซต์",
    className: "project-leaf",
    detail: "ค้นพบพื้นที่สีเขียว\nในแบบของคุณ",
    badge: "B",
  },
  {
    number: "02",
    name: "Morrow Coffee",
    type: "คาเฟ่ · อีคอมเมิร์ซ",
    className: "project-coffee",
    detail: "Make room for\nslow mornings.",
    badge: "m",
  },
  {
    number: "03",
    name: "Sunday Club",
    type: "คอมมูนิตี้ · แคมเปญ",
    className: "project-sunday",
    detail: "A little more\nsunshine, daily.",
    badge: "S",
  },
];

const services = [
  {
    number: "01",
    title: "เว็บไซต์",
    description: "เว็บไซต์ที่สวย ใช้งานง่าย และพร้อมเติบโตไปกับธุรกิจของคุณ",
    icon: "↗",
  },
  {
    number: "02",
    title: "แบรนด์ดิ้ง",
    description: "ค้นหาตัวตนของแบรนด์ แล้วเล่าออกมาให้คนจดจำ",
    icon: "✳",
  },
  {
    number: "03",
    title: "ดิจิทัลโปรดักต์",
    description: "เปลี่ยนไอเดียให้กลายเป็นประสบการณ์ที่คนอยากกลับมาใช้",
    icon: "◫",
  },
];

function ArrowIcon({ diagonal = false }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      fill="none"
      className="arrow-icon"
    >
      {diagonal ? (
        <path d="M5 15 15 5M6 5h9v9" />
      ) : (
        <path d="M3.5 10h12m-5-5 5 5-5 5" />
      )}
    </svg>
  );
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <>
      <header className="site-header">
        <a className="wordmark" href="#top" onClick={closeMenu} aria-label="Tuidui Studio หน้าแรก">
          tuidui<span>®</span>
        </a>
        <button
          className="menu-toggle"
          type="button"
          aria-label={menuOpen ? "ปิดเมนู" : "เปิดเมนู"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span />
          <span />
        </button>
        <nav className={menuOpen ? "main-nav is-open" : "main-nav"} aria-label="เมนูหลัก">
          <a href="#work" onClick={closeMenu}>ผลงาน</a>
          <a href="#services" onClick={closeMenu}>บริการ</a>
          <a href="#about" onClick={closeMenu}>เกี่ยวกับเรา</a>
          <a className="nav-contact" href="#contact" onClick={closeMenu}>
            มาคุยกัน <ArrowIcon diagonal />
          </a>
        </nav>
      </header>

      <main id="top">
        <section className="hero section-wrap">
          <div className="hero-copy">
            <p className="eyebrow"><span className="status-dot" /> CREATIVE DIGITAL STUDIO · BANGKOK</p>
            <h1>
              ทำไอเดีย
              <br />
              ให้เป็น<span className="handdrawn">จริง</span>
              <span className="hero-period">.</span>
            </h1>
            <div className="hero-bottom">
              <p className="hero-description">
                เราช่วยสร้างแบรนด์และเว็บไซต์
                <br className="desktop-break" />
                ที่เป็นตัวคุณ และเติบโตได้จริง
              </p>
              <a className="round-link" href="#work" aria-label="ดูผลงานของเรา">
                <ArrowIcon />
              </a>
            </div>
          </div>
          <div className="hero-art" aria-label="ภาพประกอบดอกไม้และก้อนสีสันสดใส" role="img">
            <div className="art-sun" />
            <div className="art-flower">
              <span /><span /><span /><span /><span /><span />
              <i />
            </div>
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <span className="art-spark spark-one">✳</span>
            <span className="art-spark spark-two">✳</span>
            <span className="art-note">little ideas,<br />big feelings</span>
            <span className="art-caption">GOOD THINGS GROW HERE ↗</span>
          </div>
          <div className="hero-footer">
            <span>คิดด้วยกัน · ทำด้วยใจ · ไปให้ไกล</span>
            <a href="#work">เลื่อนลงเพื่อสำรวจ <span>↓</span></a>
          </div>
        </section>

        <section className="work-section section-wrap" id="work">
          <div className="section-heading">
            <div>
              <p className="eyebrow">SELECTED WORK · 2023—2025</p>
              <h2>เรื่องราวที่เรา<span>ทำด้วยกัน</span></h2>
            </div>
            <a className="text-link" href="#contact">อยากเห็นโปรเจกต์ของคุณตรงนี้ <ArrowIcon diagonal /></a>
          </div>
          <div className="project-grid">
            {projects.map((project) => (
              <article className="project-card" key={project.number}>
                <a className={`project-art ${project.className}`} href="#contact" aria-label={`สอบถามเกี่ยวกับโปรเจกต์ ${project.name}`}>
                  <span className="project-number">{project.number} / PROJECT</span>
                  <span className="project-badge">{project.badge}</span>
                  <span className="project-detail">{project.detail}</span>
                  <span className="project-open"><ArrowIcon diagonal /></span>
                  <span className="project-decoration" aria-hidden="true" />
                </a>
                <div className="project-meta">
                  <h3>{project.name}</h3>
                  <span>{project.type}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="services-section" id="services">
          <div className="section-wrap services-inner">
            <div className="section-heading">
              <div>
                <p className="eyebrow">WHAT WE DO</p>
                <h2>เล็กพอดี <span>ดูแลทั่วถึง</span></h2>
              </div>
              <p className="section-aside">ทีมเล็ก ๆ ที่ตั้งใจฟัง<br />และลงมือทำไปกับคุณทุกขั้นตอน</p>
            </div>
            <div className="service-list">
              {services.map((service) => (
                <article className="service-row" key={service.number}>
                  <span className="service-number">{service.number}</span>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                  <span className="service-icon" aria-hidden="true">{service.icon}</span>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="about-section section-wrap" id="about">
          <div className="about-sticker" aria-hidden="true">
            <span>GOOD<br />IDEAS<br /><i>GROW</i></span>
            <b>✳</b>
          </div>
          <div className="about-copy">
            <p className="eyebrow">A LITTLE ABOUT US</p>
            <h2>เราเชื่อว่า<br />ของดีเริ่มจาก<br /><span>การได้คุยกัน</span></h2>
            <p className="about-description">
              Tuidui เป็นสตูดิโอสร้างสรรค์ที่ชอบเปลี่ยนเรื่องยากให้เข้าใจง่าย
              เราทำงานใกล้ชิดกับคนทำธุรกิจ เพื่อออกแบบสิ่งที่ทั้งสวย ใช้ได้จริง
              และรู้สึกเป็นตัวเอง
            </p>
            <a className="text-link" href="#contact">รู้จักเรามากขึ้น <ArrowIcon diagonal /></a>
          </div>
          <div className="about-note">
            <span>♡</span>
            <p>made with<br />curiosity & care</p>
          </div>
        </section>

        <section className="contact-section section-wrap" id="contact">
          <p className="eyebrow">HAVE A GOOD ONE IN MIND?</p>
          <h2>มาเริ่มอะไร<br /><span>ดี ๆ ด้วยกัน</span></h2>
          <a className="contact-button" href="mailto:hello@tuidui.studio">
            เล่าไอเดียให้เราฟัง <ArrowIcon diagonal />
          </a>
          <span className="contact-spark spark-left" aria-hidden="true">✳</span>
          <span className="contact-spark spark-right" aria-hidden="true">✳</span>
        </section>
      </main>

      <footer className="site-footer section-wrap">
        <a className="wordmark footer-wordmark" href="#top">tuidui<span>®</span></a>
        <p>สตูดิโอเล็ก ๆ สำหรับไอเดียดี ๆ</p>
        <div className="footer-links">
          <a href="mailto:hello@tuidui.studio">อีเมล</a>
          <a href="#top">Instagram ↗</a>
        </div>
        <span className="copyright">© 2025 TUIDUI STUDIO</span>
      </footer>
    </>
  );
}

export default App;
