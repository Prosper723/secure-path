"""
Secure Path — design system.

Rules: one neutral palette + four status tones (green / blue / amber / red).
Every status is shown with an icon AND a word, never colour alone.
"""

from html import escape
import re

import streamlit as st

from data import STATUS, CONFIDENCE, DATA_REVIEWED, COUNTRIES

TONES = {
    "green": ("#15803D", "#F0FDF4", "#BBF7D0"),
    "blue":  ("#1D4ED8", "#EFF6FF", "#BFDBFE"),
    "amber": ("#B45309", "#FFFBEB", "#FDE68A"),
    "red":   ("#B91C1C", "#FEF2F2", "#FECACA"),
    "grey":  ("#475569", "#F8FAFC", "#E2E8F0"),
}
VERDICT_TONE = {"go": "green", "evisa": "blue", "check": "amber", "visa": "red", "stop": "red", "home": "grey"}
VERDICT_ICON = {"go": "✓", "evisa": "◐", "check": "?", "visa": "✕", "stop": "!", "home": "⌂"}
OUTCOME = {"pass": ("✓", "green"), "warn": ("!", "amber"), "fail": ("✕", "red"), "info": ("i", "grey")}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--ink:#0F172A;--muted:#475569;--soft:#64748B;--line:#E2E8F0;--surface:#F8FAFC;--brand:#1D4ED8;--navy:#0B1F4B;}
html, body, [class*="css"], .stMarkdown, button, input, textarea {font-family:'Inter',system-ui,sans-serif;}
.block-container{max-width:1160px;padding-top:1.2rem;padding-bottom:4rem;}
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"]{visibility:hidden;}
h1,h2,h3{letter-spacing:-0.015em;color:var(--ink);}
p, li{line-height:1.6;}

/* header */
.sp-header{display:flex;align-items:center;justify-content:space-between;gap:1rem;
  padding:0.4rem 0 1.1rem;border-bottom:1px solid var(--line);margin-bottom:0.6rem;flex-wrap:wrap;}
.sp-brand{display:flex;align-items:center;gap:0.75rem;}
.sp-brand .name{font-weight:700;font-size:1.25rem;color:var(--ink);line-height:1.1;}
.sp-brand .tag{font-size:0.86rem;color:var(--soft);}
.sp-meta{font-size:0.78rem;color:var(--soft);display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;}
.pill{display:inline-flex;align-items:center;gap:0.35rem;padding:0.18rem 0.6rem;border-radius:999px;
  font-size:0.76rem;font-weight:600;border:1px solid var(--line);background:#fff;color:var(--muted);white-space:nowrap;}
.pill.dot::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;}

/* tabs */
.stTabs [data-baseweb="tab-list"]{gap:0.25rem;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{padding:0.6rem 0.9rem;font-weight:500;color:var(--muted);}
.stTabs [aria-selected="true"]{color:var(--ink);}

/* section label */
.eyebrow{font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:var(--soft);margin:0.2rem 0 0.4rem;}
.lead{font-size:1.02rem;color:var(--muted);margin:-0.2rem 0 1rem;}

/* verdict */
.verdict{border-radius:16px;padding:1.25rem 1.35rem;border:1px solid;display:flex;gap:1rem;align-items:flex-start;}
.verdict .ico{flex:0 0 44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:1.3rem;color:#fff;}
.verdict .where{font-size:0.82rem;font-weight:600;color:var(--muted);margin-bottom:0.15rem;}
.verdict .head{font-size:1.4rem;font-weight:700;color:var(--ink);line-height:1.25;margin:0 0 0.35rem;}
.verdict .sum{color:#334155;margin:0 0 0.7rem;}
.chips{display:flex;gap:0.4rem;flex-wrap:wrap;}

/* status chip */
.chip{display:inline-flex;align-items:center;gap:0.35rem;padding:0.15rem 0.55rem;border-radius:999px;font-size:0.76rem;
  font-weight:600;border:1px solid;white-space:nowrap;}

/* actions */
.actions{list-style:none;margin:0.4rem 0 0;padding:0;counter-reset:a;}
.actions li{counter-increment:a;display:flex;gap:0.7rem;padding:0.55rem 0;border-bottom:1px solid var(--line);color:#1E293B;}
.actions li:last-child{border-bottom:0;}
.actions li::before{content:counter(a);flex:0 0 24px;height:24px;border-radius:50%;background:var(--navy);color:#fff;
  font-size:0.78rem;font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:1px;}

/* reasoning steps */
.steps{list-style:none;margin:0;padding:0;}
.steps li{display:flex;gap:0.75rem;padding:0.7rem 0;border-bottom:1px solid var(--line);}
.steps li:last-child{border-bottom:0;}
.steps .mk{flex:0 0 26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:0.82rem;border:1px solid;}
.steps .t{font-weight:600;color:var(--ink);font-size:0.94rem;}
.steps .d{color:var(--muted);font-size:0.9rem;margin-top:0.1rem;}
.steps .s{font-size:0.78rem;margin-top:0.2rem;}
.steps .s a{color:var(--brand);text-decoration:none;}

/* timeline */
.tl{position:relative;margin:0.3rem 0 0;padding:0 0 0 1.4rem;list-style:none;}
.tl::before{content:"";position:absolute;left:6px;top:6px;bottom:6px;width:2px;background:var(--line);}
.tl li{position:relative;padding:0 0 1rem;}
.tl li::before{content:"";position:absolute;left:-1.4rem;top:4px;width:14px;height:14px;border-radius:50%;
  background:#fff;border:3px solid var(--brand);}
.tl li.done::before{background:var(--brand);}
.tl .w{font-size:0.75rem;font-weight:600;color:var(--brand);text-transform:uppercase;letter-spacing:0.05em;}
.tl .t{font-weight:600;color:var(--ink);}
.tl .d{color:var(--muted);font-size:0.9rem;}

/* stat tiles */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.75rem;margin:0.4rem 0 1rem;}
.tile{border:1px solid var(--line);border-radius:14px;padding:0.9rem 1rem;background:#fff;}
.tile .n{font-size:1.7rem;font-weight:700;color:var(--ink);line-height:1.1;}
.tile .l{font-size:0.82rem;color:var(--muted);margin-top:0.2rem;display:flex;align-items:center;gap:0.4rem;}
.tile .sw{width:10px;height:10px;border-radius:3px;display:inline-block;}

/* cards */
.card{border:1px solid var(--line);border-radius:14px;padding:1rem 1.1rem;background:#fff;height:100%;}
.card .t{font-weight:600;color:var(--ink);margin-bottom:0.25rem;}
.card .d{color:var(--muted);font-size:0.9rem;}
.callout{border-radius:14px;padding:1rem 1.15rem;border:1px solid;margin:0.4rem 0 1rem;}
.callout .t{font-weight:600;margin-bottom:0.25rem;}
.empty{border:1.5px dashed var(--line);border-radius:16px;padding:1.6rem 1.4rem;text-align:left;background:var(--surface);}
.empty .t{font-weight:600;font-size:1.05rem;color:var(--ink);}
.empty .d{color:var(--muted);font-size:0.92rem;margin-top:0.25rem;}
.fine{font-size:0.78rem;color:var(--soft);}
.fine a{color:var(--soft);}

/* chat */
[data-testid="stChatMessage"]{padding:0.6rem 0.2rem;}
@media (max-width: 640px){
  .verdict{flex-direction:column;gap:0.7rem;} .verdict .head{font-size:1.2rem;}
  .verdict .ico{flex:0 0 auto;width:40px;height:40px;}
  .block-container{padding-left:1rem;padding-right:1rem;}
}
</style>
"""

LOGO = """<svg width="38" height="38" viewBox="0 0 40 40" aria-hidden="true">
<rect width="40" height="40" rx="11" fill="#0B1F4B"/>
<path d="M20 8l9 3.5v7.2c0 6-3.9 10.7-9 12.3-5.1-1.6-9-6.3-9-12.3v-7.2L20 8z" fill="none" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/>
<path d="M15.5 20.5l3.2 3.2 6-6.4" fill="none" stroke="#60A5FA" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(CONTACT_CSS, unsafe_allow_html=True)


def header():
    st.markdown(f"""
<div class="sp-header">
  <div class="sp-brand">{LOGO}<div><div class="name">Secure Path</div>
    <div class="tag">Clear visa answers for people travelling on UK refugee and stateless travel documents</div></div></div>
  <div class="sp-meta"><span class="pill dot" style="color:#15803D">{len(COUNTRIES)} countries</span>
    <span class="pill">Data reviewed {_fmt_date(DATA_REVIEWED)}</span><span class="pill">Prototype</span></div>
</div>""", unsafe_allow_html=True)


def _fmt_date(iso: str) -> str:
    from datetime import date
    d = date.fromisoformat(iso)
    return f"{d.day} {d:%b %Y}"  # portable: %-d is not supported on Windows


def status_chip(status: str) -> str:
    s = STATUS[status]
    fg, bg, bd = TONES[s["tone"]]
    return f'<span class="chip" style="color:{fg};background:{bg};border-color:{bd}">{s["icon"]} {s["label"]}</span>'


def confidence_chip(level: str) -> str:
    fg, bg, bd = TONES[{"verified": "green", "high": "green", "medium": "blue", "low": "grey"}[level]]
    if level == "verified":
        return (f'<span class="chip" title="{escape(CONFIDENCE[level]["help"])}" '
                f'style="color:{fg};background:{bg};border-color:{bd}">✓ {CONFIDENCE[level]["label"]}</span>')
    return (f'<span class="chip" title="{escape(CONFIDENCE[level]["help"])}" '
            f'style="color:{fg};background:{bg};border-color:{bd}">{CONFIDENCE[level]["label"]}</span>')


def plain_chip(text: str) -> str:
    return f'<span class="chip" style="color:#475569;background:#fff;border-color:#E2E8F0">{escape(text)}</span>'


def verdict_card(a, extra_chips: list[str] | None = None):
    tone = VERDICT_TONE[a.verdict]
    fg, bg, bd = TONES[tone]
    c = a.country
    chips = [confidence_chip(a.confidence), plain_chip(f"{len(c['sources'])} sources")] + (extra_chips or [])
    st.markdown(f"""
<div class="verdict" style="background:{bg};border-color:{bd}" role="status">
  <div class="ico" style="background:{fg}" aria-hidden="true">{VERDICT_ICON[a.verdict]}</div>
  <div><div class="where">{c['flag']} {escape(c['name'])}</div>
    <div class="head">{escape(a.headline)}</div>
    <p class="sum">{escape(a.summary)}</p>
    <div class="chips">{''.join(chips)}</div></div>
</div>""", unsafe_allow_html=True)


def action_list(actions: list[str]):
    items = "".join(f"<li><span>{_linkify(a)}</span></li>" for a in actions)
    st.markdown(f'<ol class="actions">{items}</ol>', unsafe_allow_html=True)


def _linkify(text: str) -> str:
    import re
    t = escape(text)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)


def step_list(steps):
    rows = []
    for s in steps:
        icon, tone = OUTCOME[s.outcome]
        fg, bg, bd = TONES[tone]
        src = (f'<div class="s"><a href="{escape(s.source["url"])}" target="_blank" rel="noopener">'
               f'Source: {escape(s.source["label"])} ↗</a></div>') if s.source else ""
        rows.append(f'<li><div class="mk" style="color:{fg};background:{bg};border-color:{bd}">{icon}</div>'
                    f'<div><div class="t">{escape(s.title)}</div><div class="d">{escape(s.detail)}</div>{src}</div></li>')
    st.markdown(f'<ul class="steps">{"".join(rows)}</ul>', unsafe_allow_html=True)


def timeline(items: list[dict]):
    rows = "".join(
        f'<li class="{"done" if i["when"] == "Done" else ""}"><div class="w">{escape(i["when"])}</div>'
        f'<div class="t">{escape(i["title"])}</div><div class="d">{escape(i["detail"])}</div></li>' for i in items)
    st.markdown(f'<ul class="tl">{rows}</ul>', unsafe_allow_html=True)


def tiles(items: list[tuple]):
    html = "".join(
        f'<div class="tile"><div class="n">{n}</div><div class="l">'
        + (f'<span class="sw" style="background:{color}"></span>' if color else "") + f'{escape(label)}</div></div>'
        for n, label, color in items)
    st.markdown(f'<div class="tiles">{html}</div>', unsafe_allow_html=True)


def callout(title: str, body: str, tone: str = "blue"):
    fg, bg, bd = TONES[tone]
    st.markdown(f'<div class="callout" style="background:{bg};border-color:{bd}">'
                f'<div class="t" style="color:{fg}">{escape(title)}</div><div style="color:#334155">{body}</div></div>',
                unsafe_allow_html=True)


def card(title: str, body: str):
    st.markdown(f'<div class="card"><div class="t">{escape(title)}</div><div class="d">{body}</div></div>',
                unsafe_allow_html=True)


def eyebrow(text: str):
    st.markdown(f'<div class="eyebrow">{escape(text)}</div>', unsafe_allow_html=True)


def lead(text: str):
    st.markdown(f'<p class="lead">{text}</p>', unsafe_allow_html=True)


# ── Embassy & consulate contact cards ───────────────────────────────────────
CONTACT_CSS = """
<style>
.ct{border:1px solid var(--line);border-radius:14px;padding:0.95rem 1.05rem;background:#fff;margin-bottom:0.7rem;}
.ct.hl{border-color:#93C5FD;background:#F8FBFF;}
.ct .top{display:flex;justify-content:space-between;gap:0.6rem;align-items:flex-start;flex-wrap:wrap;}
.ct .nm{font-weight:600;color:var(--ink);font-size:0.97rem;}
.ct .kd{font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:var(--soft);margin-bottom:0.1rem;}
.ct .rows{margin-top:0.45rem;display:grid;gap:0.25rem;font-size:0.9rem;color:#334155;}
.ct .rows a{color:var(--brand);text-decoration:none;}
.ct .rows .k{display:inline-block;width:1.4rem;color:var(--soft);}
.ct .ar{font-size:0.8rem;color:var(--muted);margin-top:0.45rem;}
</style>
"""


def contact_card(rec: dict, kind: str, highlight: bool = False, distance: str | None = None,
                 covers: bool = False):
    from contacts import maps_url, tel_url
    chips = []
    if rec.get("status"):
        chips.append(f'<span class="chip" style="color:#B45309;background:#FFFBEB;border-color:#FDE68A">'
                     f'{escape(rec["status"])}</span>')
    if covers:
        chips.append('<span class="chip" style="color:#15803D;background:#F0FDF4;border-color:#BBF7D0">'
                     '✓ Covers your area</span>')
    if distance:
        chips.append(plain_chip(distance))
    rows = []
    if rec.get("address"):
        rows.append(f'<div><span class="k">📍</span>{escape(rec["address"])} · '
                    f'<a href="{maps_url(rec["address"])}" target="_blank" rel="noopener">Map ↗</a></div>')
    for p in rec.get("phone") or []:
        rows.append(f'<div><span class="k">☎</span><a href="{tel_url(p)}">{escape(p)}</a></div>')
    for e in rec.get("email") or []:
        rows.append(f'<div><span class="k">✉</span><a href="mailto:{escape(e)}">{escape(e)}</a></div>')
    if rec.get("website"):
        w = rec["website"]
        short = re.sub(r"^https?://(www[.])?", "", w).rstrip("/")
        rows.append(f'<div><span class="k">🌐</span><a href="{escape(w)}" target="_blank" rel="noopener">'
                    f'{escape(short)} ↗</a></div>')
    for h in rec.get("hours") or []:
        rows.append(f'<div><span class="k">🕘</span>{escape(h)}</div>')
    if not rows and not rec.get("status"):
        rows.append('<div style="color:#64748B">No public contact details listed — try the embassy.</div>')
    area = f'<div class="ar">Covers: {escape(rec["area"])}</div>' if rec.get("area") else ""
    st.markdown(f'<div class="ct {"hl" if highlight else ""}"><div class="top"><div><div class="kd">{escape(kind)}</div>'
                f'<div class="nm">{escape(rec.get("name") or "")}</div></div><div class="chips">{"".join(chips)}</div></div>'
                f'<div class="rows">{"".join(rows)}</div>{area}</div>', unsafe_allow_html=True)
