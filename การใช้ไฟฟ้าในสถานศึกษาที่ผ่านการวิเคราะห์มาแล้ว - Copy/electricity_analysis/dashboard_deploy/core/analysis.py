"""Analysis functions. Same definitions as notebooks/02_explore.ipynb so numbers match when no filter is applied."""
import numpy as np
import pandas as pd
import streamlit as st
from core.data import filtered, load_all

E = "energy_clean"


@st.cache_resource(max_entries=16, show_spinner=False)
def _room_table(key, thr_items):
    thr = dict(thr_items)
    d = filtered(*key)
    off = d["is_off_hours"]
    hr = d["hour"].between(18, 22)
    eve, oth = off & hr, off & ~hr
    g = d.groupby("room_id")
    room = g.agg(meter_id=("meter_id", "first"), building_id=("building_id", "first"), building_name=("building_name", "first"),
                 room_type=("room_type", "first"), area_m2=("area_m2", "first"), capacity_people=("capacity_people", "first"),
                 ac_count=("air_conditioner_count", "first"), total_kwh=(E, "sum"), mean_kwh_h=(E, "mean"),
                 peak_kwh_h=(E, "max"), hours_n=(E, "size"))

    def part(mask, how):
        return getattr(d[mask].groupby("room_id")[E], how)().reindex(room.index)

    room["off_kwh"] = part(off, "sum").fillna(0.0)
    room["off_hours_n"] = d[off].groupby("room_id").size().reindex(room.index).fillna(0).astype(int)
    room["off_mean_kwh_h"] = part(off, "mean")
    room["evening_mean_kwh_h"] = part(eve, "mean")
    room["evening_hours_n"] = d[eve].groupby("room_id").size().reindex(room.index).fillna(0).astype(int)
    room["other_off_mean_kwh_h"] = part(oth, "mean")
    room["evening_ratio"] = room["evening_mean_kwh_h"] / room["other_off_mean_kwh_h"]
    room["off_share_pct"] = 100 * room["off_kwh"] / room["total_kwh"]
    room["weekend_mean_kwh_h"] = part(d["day_type"] == "weekend", "mean")
    room["occupied_mean_kwh_h"] = part(~off, "mean")
    room["mean_people_occupied"] = d[~off].groupby("room_id")["occupancy_people"].mean().reindex(room.index)
    room["outlier_count"] = d[d["flag_outlier"]].groupby("room_id").size().reindex(room.index).fillna(0).astype(int)
    base = room["other_off_mean_kwh_h"].median()
    base = 0.0 if pd.isna(base) else float(base)
    room["flag_evening_block"] = (room["evening_ratio"] >= thr["evening_ratio"]).fillna(False)
    room["flag_continuous_baseline"] = (room["other_off_mean_kwh_h"] >= thr["standby_x"] * base).fillna(False) if base > 0 else False
    room["flag_off_share"] = (room["off_share_pct"] > thr["off_share_pct"]).fillna(False)
    room["evening_excess_kwh"] = ((room["evening_mean_kwh_h"] - room["other_off_mean_kwh_h"]).clip(lower=0) * room["evening_hours_n"]).where(room["flag_evening_block"], 0).fillna(0)
    room["baseline_excess_kwh"] = ((room["other_off_mean_kwh_h"] - base).clip(lower=0) * room["off_hours_n"]).where(room["flag_continuous_baseline"], 0).fillna(0)

    def pattern(r):
        if r["flag_evening_block"] and r["flag_continuous_baseline"]:
            return "สูงช่วง 18:00-22:59 และมีฐานต่อเนื่อง"
        if r["flag_evening_block"]:
            return "สูงช่วง 18:00-22:59"
        if r["flag_continuous_baseline"]:
            return "ใช้ต่อเนื่องทั้งวัน"
        return "-"
    room["pattern"] = room.apply(pattern, axis=1)
    room.attrs["baseline"] = base
    return room.reset_index()


def room_table(ctx):
    t = ctx["thr"]
    return _room_table(ctx["key"], tuple(sorted(t.items())))


def tier(p, thr):
    return "สูง" if p >= thr["impact_high"] else ("กลาง" if p >= thr["impact_mid"] else "ต่ำ")


def lower(t):
    return {"สูง": "กลาง", "กลาง": "ต่ำ", "ต่ำ": "ต่ำ"}[t]


def problems(ctx, room):
    """Problem list with severity = impact tier lowered one level when the cause is uncertain."""
    d, thr = ctx["d"], ctx["thr"]
    total = d[E].sum()
    A = ctx["all"]
    out = d[d["flag_outlier"]]
    dup_n = int(A["clean_log"].loc[A["clean_log"]["issue"].str.contains("duplicate"), "rows_affected"].sum())
    rows = []

    def add(pid, title, where, excess, cert, why, action, owner, when):
        pct = 100 * excess / total if total else 0.0
        t = tier(pct, thr)
        rows.append({"id": pid, "problem": title, "where": where, "excess_kwh": float(excess), "impact_pct": float(pct), "certainty": cert,
                     "certainty_reason": why, "severity": t if cert == "สูง" else lower(t), "action": action, "owner": owner, "timeframe": when})

    ev, bs = room[room["flag_evening_block"]], room[room["flag_continuous_baseline"]]
    if len(ev):
        add("P1", "ใช้ไฟสูงผิดปกติช่วง 18:00-22:59 น. ทั้งที่ไม่มีคน", ", ".join(ev["room_id"]), ev["evening_excess_kwh"].sum(), "สูง",
            "จำนวนคนเป็น 0 ในทุกชั่วโมงที่พบ และเกิดซ้ำสม่ำเสมอ", "ตรวจการตั้งเวลาและสถานะอุปกรณ์หลัง 18:00 น. แล้วเทียบผลก่อน-หลัง",
            "ฝ่ายอาคารสถานที่", "ภายใน 1 สัปดาห์")
    if len(bs):
        add("P2", "ใช้ไฟต่อเนื่องในช่วงไม่มีคน (ห้องที่ฐานไฟสูงกว่าห้องอื่น)", ", ".join(bs["room_id"]), bs["baseline_excess_kwh"].sum(), "กลาง",
            "อาจมีอุปกรณ์หรือระบบที่ต้องทำงานต่อเนื่อง ข้อมูลไม่ระบุอุปกรณ์", "สอบถามผู้ดูแลห้องว่าอุปกรณ์ใดต้องเปิดตลอด ที่ไม่จำเป็นให้ตั้งเวลาปิด",
            "ผู้ดูแลห้อง", "ภายใน 1 เดือน")
    if len(out):
        add("P3", "ค่าสูงผิดปกติรายชั่วโมง (%d จุด)" % len(out), "%d ห้อง (ดูตารางค่าผิดปกติ)" % out["room_id"].nunique(),
            (out["energy_kwh"] - out["cell_median"]).sum(), "กลาง", "เป็นได้ทั้งการอ่านค่าผิดพลาดและเหตุการณ์จริง ข้อมูลยืนยันไม่ได้",
            "ตรวจมิเตอร์ตามวันเวลาในตาราง ถ้าเป็นเหตุการณ์จริงให้ใส่ค่าเดิมกลับ", "ผู้ดูแลมิเตอร์", "ภายใน 2 สัปดาห์")
    add("P4", "คุณภาพการบันทึกข้อมูล (ซ้ำ %d, ว่าง %d, ติดลบ %d)" % (dup_n, int(d["flag_missing"].sum()), int(d["flag_negative"].sum())),
        "มิเตอร์ M001, M009, M017, M025, M033 (ซ้ำ) และมิเตอร์อื่น (ว่าง/ติดลบ)", 0.0, "สูง", "นับจากข้อมูลโดยตรง",
        "แก้ระบบบันทึกไม่ให้ซ้ำ ไม่ส่งค่า -0.5 และแจ้งเตือนเมื่อข้อมูลขาด", "ผู้ดูแลระบบมิเตอร์", "ภายใน 1 เดือน")
    p = pd.DataFrame(rows)
    order = {"สูง": 0, "กลาง": 1, "ต่ำ": 2}
    p["_o"] = p["severity"].map(order)
    return p.sort_values(["_o", "impact_pct"], ascending=[True, False]).drop(columns="_o").reset_index(drop=True)


def within_corr(d, a, b, by):
    x = d[a] - d.groupby(by)[a].transform("mean")
    y = d[b] - d.groupby(by)[b].transform("mean")
    return float(x.corr(y))


def std_effects(occ, cols):
    """Standardized least-squares effects (kWh per 1 SD) on occupied hours. Columns without variation are dropped."""
    use = [c for c in cols if occ[c].std() and occ[c].std() > 0]
    if len(occ) < 200 or not use:
        return None
    X = ((occ[use] - occ[use].mean()) / occ[use].std()).to_numpy()
    X1 = np.column_stack([np.ones(len(X)), X])
    y = occ[E].to_numpy()
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    pred = X1 @ beta
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return pd.Series(beta[1:], index=use), float(r2), [c for c in cols if c not in use]


MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def thai_date(ts):
    return f"{ts.day} {MONTHS[ts.month - 1]} {ts.year}"


def outlier_summary(d):
    """Where / when / how often outliers occur in the selected data (all numbers computed from flags)."""
    out = d[d["flag_outlier"]]
    n, N = len(out), len(d)
    r = {"n": n, "pct": 100 * n / N if N else 0.0, "N": N, "missing": int(d["flag_missing"].sum()), "negative": int(d["flag_negative"].sum()), "has": n > 0}
    if n == 0:
        return r
    by_b = out.groupby("building_name").size().sort_values(ascending=False)
    by_h = out.groupby("hour").size().sort_values(ascending=False)
    by_m = out.groupby("month").size().sort_values(ascending=False)
    by_room = out.groupby("room_id").size()
    r.update({"by_b": by_b, "top_b": by_b.index[0], "top_b_n": int(by_b.iloc[0]), "b_spread": int(by_b.max() - by_b.min()),
              "top_h": int(by_h.index[0]), "top_h_n": int(by_h.iloc[0]), "top_m": int(by_m.index[0]), "top_m_n": int(by_m.iloc[0]),
              "rooms": int(by_room.size), "max_per_room": int(by_room.max()),
              "ratio_min": float((out["energy_kwh"] / out["cell_median"]).min()), "ratio_max": float((out["energy_kwh"] / out["cell_median"]).max()),
              "excess_kwh": float((out["energy_kwh"] - out["cell_median"]).sum())})
    return r


def key_answers(ctx, room, probs):
    """Automatic answers to the key questions. Everything is computed from the selected data; nothing is typed in."""
    d = ctx["d"]
    total = float(d[E].sum())
    off = d["is_off_hours"]
    R = {}
    bld = room.groupby("building_name")["total_kwh"].sum().sort_values(ascending=False)
    rooms_sorted = room.sort_values("total_kwh", ascending=False)
    R.update({"total": total, "n_rooms": len(room), "bld": bld, "top_b": bld.index[0], "top_b_kwh": float(bld.iloc[0]), "top_b_share": 100 * float(bld.iloc[0]) / total,
              "rooms_sorted": rooms_sorted, "top_room": rooms_sorted.iloc[0]})
    hm = d.groupby("hour")[E].mean()
    daily = d.groupby("day")[E].sum()
    mon = d.groupby("month")[E].sum()
    R.update({"hour_mean": hm, "peak_hour": int(hm.idxmax()), "peak_hour_val": float(hm.max()), "daily": daily, "peak_day": daily.idxmax(), "peak_day_kwh": float(daily.max()),
              "mon": mon, "peak_month": int(mon.idxmax()), "peak_month_kwh": float(mon.max())})
    room = room.copy()
    room["excess_kwh"] = room["evening_excess_kwh"] + room["baseline_excess_kwh"]
    first = room[room["excess_kwh"] > 0].sort_values("excess_kwh", ascending=False)
    if len(first) == 0:
        first = room.sort_values("off_share_pct", ascending=False)
    R.update({"first": first, "n_check": int(room["flag_off_share"].sum()), "off_share": 100 * float(d.loc[off, E].sum()) / total if total else 0.0,
              "off_rank": room.dropna(subset=["off_share_pct"]).sort_values("off_share_pct", ascending=False)})
    wk = d[d["day_type"] == "weekday"][E]
    we = d[d["day_type"] == "weekend"][E]
    wr = room.dropna(subset=["weekend_mean_kwh_h"]).sort_values("weekend_mean_kwh_h", ascending=False)
    R.update({"wd_mean": float(wk.mean()) if len(wk) else None, "we_mean": float(we.mean()) if len(we) else None, "we_rank": wr,
              "we_delta": 100 * (float(we.mean()) / float(wk.mean()) - 1) if len(wk) and len(we) else None,
              "we_share": 100 * float(we.sum()) / total if len(we) and total else None})
    R["out"] = outlier_summary(d)
    # plain-language Q/A list (icon, question, answer)
    qa = []
    qa.append(("apartment", "ใช้ไฟมากที่สุดที่ไหน?", f"{R['top_b']} ({fmt_n(R['top_b_kwh'])} kWh หรือ {R['top_b_share']:.1f}% ของไฟที่เลือก) และห้อง {R['top_room']['room_id']} ({R['top_room']['room_type']}) ใช้ไฟ {fmt_n(R['top_room']['total_kwh'])} kWh"))
    qa.append(("schedule", "ช่วงไหนใช้ไฟมากที่สุด?", f"ชั่วโมง {R['peak_hour']:02d}:00 (เฉลี่ย {R['peak_hour_val']:.2f} kWh ต่อห้อง) เดือน {MONTHS[R['peak_month'] - 1]} ({fmt_n(R['peak_month_kwh'])} kWh) และวันที่ใช้ไฟรวมสูงสุดคือ {thai_date(R['peak_day'])} ({fmt_n(R['peak_day_kwh'])} kWh)"))
    top3 = ", ".join(f"{r['room_id']} ({r['off_share_pct']:.1f}%)" for _, r in R["off_rank"].head(3).iterrows())
    qa.append(("manage_search", "พื้นที่ไหนควรตรวจสอบก่อน?", f"พื้นที่ที่ควรตรวจสอบเพิ่มเติมก่อน (เรียงตามส่วนเกินที่ประมาณได้): " + ", ".join(f"{r['room_id']} ({r['pattern']})" for _, r in first.head(3).iterrows()) + f" และห้องที่สัดส่วนไฟนอกเวลาสูงสุดคือ {top3}"))
    if R["we_delta"] is not None and len(wr):
        qa.append(("weekend", "วันหยุด พื้นที่ไหนยังใช้ไฟสูง?", f"วันหยุดใช้ไฟเฉลี่ยต่ำกว่าวันทำการ {-R['we_delta']:.0f}% แต่ห้อง {wr.iloc[0]['room_id']} ({wr.iloc[0]['room_type']}) ยังใช้ไฟ {wr.iloc[0]['weekend_mean_kwh_h']:.2f} kWh ต่อชั่วโมง ตามด้วย {wr.iloc[1]['room_id']} และ {wr.iloc[2]['room_id']}" if len(wr) >= 3 else f"ห้อง {wr.iloc[0]['room_id']} ใช้ไฟวันหยุดสูงสุด"))
    else:
        qa.append(("weekend", "วันหยุด พื้นที่ไหนยังใช้ไฟสูง?", "ไม่มีข้อมูลทั้งวันทำการและวันหยุดในตัวกรองที่เลือก"))
    o = R["out"]
    if o["has"]:
        spread = "กระจายใกล้เคียงกันทุกอาคาร" if o["b_spread"] <= 1 else f"มากที่สุดที่{o['top_b']} ({o['top_b_n']} จุด)"
        qa.append(("report", "พบค่าผิดปกติที่ไหนมากที่สุด?", f"พบ {o['n']} จุด ({o['pct']:.4f}% ของข้อมูล) ใน {o['rooms']} ห้อง ห้องละไม่เกิน {o['max_per_room']} จุด {spread} เกิดบ่อยสุดช่วง {o['top_h']:02d}:00 และเดือน {MONTHS[o['top_m'] - 1]}"))
    else:
        qa.append(("report", "พบค่าผิดปกติที่ไหนมากที่สุด?", "ไม่พบค่าผิดปกติในตัวกรองที่เลือก"))
    R["qa"] = qa
    return R


def fmt_n(x, dec=0):
    return format(round(float(x), dec), ",.%df" % dec)


@st.cache_resource(show_spinner=False)
def quality_summary():
    """Data-quality facts for the WHOLE dataset (not filtered): row counts, issues, treatment impact, level-shift check."""
    A = load_all()
    df, log, rec, out = A["df"], A["clean_log"], A["recon"], A["out_log"]
    pick = lambda key: int(log.loc[log["issue"].str.contains(key, regex=False), "rows_affected"].sum())
    dup, miss, neg, spike = pick("duplicate"), pick("missing"), pick("negative"), pick("isolated spikes")
    # level-shift check: median of the same meter x hour x day type, first half-year vs second half-year
    half = np.where(df["month"] <= 6, "H1", "H2")
    g = df.groupby(["meter_id", "hour", "day_type", half])[E].median().unstack(-1)
    ratio = g["H2"] / g["H1"]
    shifted = int(((ratio > 1.5) | (ratio < 1 / 1.5)).sum())
    raw = df["energy_kwh"]
    before = {"total": float(raw.where(raw >= 0).sum()), "mean": float(raw.where(raw >= 0).mean()), "max": float(raw.max()), "std": float(raw.where(raw >= 0).std()), "n": int(raw.where(raw >= 0).count())}
    after = {"total": float(df[E].sum()), "mean": float(df[E].mean()), "max": float(df[E].max()), "std": float(df[E].std()), "n": int(df[E].count())}
    deltas = {r["stage"].split(" ", 1)[0]: float(r["delta_kWh"]) for _, r in rec.iterrows() if str(r["stage"])[0] in "12345"}
    return {"rows_after": len(df), "rows_before": len(df) + dup, "dup": dup, "missing": miss, "negative": neg, "outliers": int(df["flag_outlier"].sum()), "spike_logged": spike,
            "isolated": int(out["isolated"].sum()) if "isolated" in out else None, "shift_cells": int(len(ratio)), "shifted": shifted,
            "ratio_min": float(ratio.min()), "ratio_max": float(ratio.max()), "before": before, "after": after, "raw_total_with_dups": float(rec["running_total_kWh"].iloc[0]),
            "delta_dup": deltas.get("2", 0.0), "delta_neg": deltas.get("3", 0.0), "delta_missing": deltas.get("4", 0.0), "delta_out": deltas.get("5", 0.0)}


def eta_squared(d, groups, y=E):
    """Share of the variation of kWh that is explained by group membership (0-1). Association only, not causation."""
    out = {}
    tot = ((d[y] - d[y].mean()) ** 2).sum()
    for label, col in groups.items():
        if col not in d or d[col].nunique() < 2 or tot == 0:
            continue
        gm = d.groupby(col)[y].agg(["count", "mean"])
        out[label] = float((gm["count"] * (gm["mean"] - d[y].mean()) ** 2).sum() / tot)
    return out


def daily_temp_scatter(occ):
    """One point per day and air-conditioner group: mean outdoor temperature vs mean kWh per room-hour (occupied hours only)."""
    t = occ.groupby("day")["temperature_c"].mean()
    k = occ.groupby(["day", "air_conditioner_count"])[E].mean().unstack()
    r = k.join(t.rename("temp"))
    return r.dropna(subset=["temp"])
