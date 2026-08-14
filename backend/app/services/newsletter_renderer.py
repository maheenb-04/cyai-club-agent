import base64
import io
import os
from pathlib import Path

import qrcode
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

LOGO_PATH = Path(__file__).parent.parent / "assets" / "cyai-logo.png"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "events"

CATEGORY_COLORS = {
    "scholarship": "#C41E3A",
    "internship": "#A8B4D8",
    "job": "#E3A83B",
    "ctf": "#2A2A2A",
    "bootcamp": "#4A90A4",
    "fellowship": "#D97B4F",
}
CATEGORY_CTA = {
    "scholarship": "APPLY NOW",
    "internship": "APPLY HERE",
    "job": "APPLY HERE",
    "ctf": "REGISTER",
    "bootcamp": "START NOW",
    "fellowship": "APPLY NOW",
}


def _get_logo_base64() -> str:
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_event_image_base64(image_filename: str) -> str:
    if not image_filename:
        return ""
    filepath = UPLOADS_DIR / image_filename
    if not filepath.exists():
        return ""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _generate_qr_base64(url: str) -> str:
    if not url or not url.startswith("http"):
        return ""
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2A2A2A", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _event_card_html(event: dict) -> str:
    image_b64 = _get_event_image_base64(event.get("image_filename"))
    qr_b64 = _generate_qr_base64(event.get("rsvp_link", ""))

    image_html = ""
    if image_b64:
        image_html = f'<img class="event-photo" src="data:image/png;base64,{image_b64}">'
    else:
        image_html = '<div class="event-photo-placeholder">CYAI</div>'

    qr_html = ""
    if qr_b64:
        qr_html = f'<img class="qr-code" src="data:image/png;base64,{qr_b64}"><p class="qr-label">Scan to RSVP</p>'

    return f"""
    <div class="event-card">
      <div class="event-photo-col">{image_html}</div>
      <div class="event-info-col">
        <h3>{event.get('title', '')}</h3>
        <p class="meta">{event.get('event_date', 'TBD')} &middot; {event.get('time_display', 'TBD')} &middot; {event.get('location', 'TBD')}</p>
        <p class="desc">{event.get('description', '')}</p>
      </div>
      <div class="event-qr-col">{qr_html}</div>
    </div>
    """


def _opportunity_card_html(opp: dict) -> str:
    color = CATEGORY_COLORS.get(opp.get("category", ""), "#A8B4D8")
    cta = CATEGORY_CTA.get(opp.get("category", ""), "LEARN MORE")
    qr_b64 = _generate_qr_base64(opp.get("url", ""))

    qr_html = f'<img class="qr-code-small" src="data:image/png;base64,{qr_b64}">' if qr_b64 else ""

    deadline = opp.get("deadline") or "Rolling"

    return f"""
    <div class="opp-card" style="border-left-color: {color};">
      <div class="opp-text">
        <h4>{opp.get('title', '')}</h4>
        <p class="meta">{opp.get('organization', 'N/A')} &middot; Deadline: {deadline}</p>
        <p class="desc">{(opp.get('description') or '')[:140]}</p>
      </div>
      <div class="opp-cta-col">
        {qr_html}
        <span class="cta-badge" style="background: {color};">{cta}</span>
      </div>
    </div>
    """


def _build_full_html(subject: str, intro_html: str, events: list, opportunities_by_category: dict) -> str:
    logo_b64 = _get_logo_base64()

    events_html = ""
    if events:
        events_html = '<h2 class="section-title">Upcoming Events</h2>'
        for event in events:
            events_html += _event_card_html(event)

    opps_html = ""
    for category, items in opportunities_by_category.items():
        color = CATEGORY_COLORS.get(category, "#A8B4D8")
        opps_html += f'<h2 class="section-title" style="border-color: {color};">{category.title()}s</h2>'
        for opp in items:
            opps_html += _opportunity_card_html(opp)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #F2E9D8; color: #2A2A2A; font-family: 'IBM Plex Sans', sans-serif; font-size: 11px; }}
  .page {{ max-width: 800px; margin: 0 auto; background: #FAF7F0; }}
  .banner {{ background: #C41E3A; padding: 20px 28px; display: flex; align-items: center; gap: 14px; }}
  .banner img {{ width: 48px; height: 48px; border-radius: 50%; border: 3px solid white; }}
  .banner h1 {{ font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 22px; color: white; margin: 0; }}
  .banner p {{ font-family: 'Space Grotesk', sans-serif; font-size: 11px; color: #F2E9D8; margin: 2px 0 0; text-transform: uppercase; letter-spacing: 0.05em; }}
  .intro {{ background: white; padding: 16px 28px; font-size: 11px; line-height: 1.5; }}
  .content {{ padding: 16px 28px; }}
  .section-title {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px; color: #2A2A2A; border-bottom: 3px solid #E3A83B; padding-bottom: 4px; margin: 16px 0 10px; }}
  .event-card {{ display: flex; gap: 10px; background: #A8B4D8; border-radius: 10px; padding: 10px; margin-bottom: 10px; align-items: center; }}
  .event-photo {{ width: 70px; height: 70px; object-fit: cover; border-radius: 8px; }}
  .event-photo-placeholder {{ width: 70px; height: 70px; border-radius: 8px; background: #E3A83B; display: flex; align-items: center; justify-content: center; font-family: 'Space Grotesk'; font-weight: 800; color: white; font-size: 14px; }}
  .event-info-col {{ flex: 1; }}
  .event-info-col h3 {{ font-family: 'Space Grotesk', sans-serif; font-size: 13px; margin: 0 0 2px; }}
  .event-info-col .meta {{ font-size: 9px; color: #2A2A2A; margin: 0 0 4px; }}
  .event-info-col .desc {{ font-size: 9px; margin: 0; }}
  .event-qr-col {{ text-align: center; flex-shrink: 0; }}
  .qr-code {{ width: 44px; height: 44px; }}
  .qr-label {{ font-size: 7px; margin: 2px 0 0; }}
  .opp-card {{ display: flex; justify-content: space-between; gap: 10px; background: white; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 4px solid #A8B4D8; }}
  .opp-text h4 {{ font-family: 'Space Grotesk', sans-serif; font-size: 11px; margin: 0 0 2px; }}
  .opp-text .meta {{ font-size: 8px; color: #4A4A4A; margin: 0 0 3px; }}
  .opp-text .desc {{ font-size: 8px; margin: 0; }}
  .opp-cta-col {{ text-align: center; flex-shrink: 0; }}
  .qr-code-small {{ width: 32px; height: 32px; display: block; margin: 0 auto 4px; }}
  .cta-badge {{ display: inline-block; color: white; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 7px; padding: 3px 8px; border-radius: 999px; white-space: nowrap; }}
  .footer {{ background: #2A2A2A; color: #F2E9D8; padding: 12px 28px; text-align: center; font-family: 'Space Grotesk', sans-serif; font-size: 9px; }}
</style>
</head>
<body>
  <div class="page">
    <div class="banner">
      <img src="data:image/png;base64,{logo_b64}">
      <div>
        <h1>{subject}</h1>
        <p>Cybersecurity &amp; AI Club &middot; York College</p>
      </div>
    </div>
    <div class="intro">{intro_html}</div>
    <div class="content">
      {events_html}
      {opps_html}
    </div>
    <div class="footer">@CYAIYORK &middot; cyai.club@gmail.com</div>
  </div>
</body>
</html>"""


def _render_pdf_bytes(full_html: str) -> bytes:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html, wait_until="networkidle")
        pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()
    return pdf_bytes


def _count_pdf_pages(pdf_bytes: bytes) -> int:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)


def render_newsletter_pdf(subject: str, intro_html: str, events: list, opportunities_by_category: dict, max_pages: int = 2) -> bytes:
    max_items = 5
    last_pdf = None

    while max_items >= 1:
        truncated = {cat: items[:max_items] for cat, items in opportunities_by_category.items()}
        full_html = _build_full_html(subject, intro_html, events, truncated)
        pdf_bytes = _render_pdf_bytes(full_html)
        last_pdf = pdf_bytes

        page_count = _count_pdf_pages(pdf_bytes)
        if page_count <= max_pages:
            return pdf_bytes

        max_items -= 1

    return last_pdf
