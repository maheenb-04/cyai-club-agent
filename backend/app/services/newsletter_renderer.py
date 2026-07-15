import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

LOGO_PATH = Path(__file__).parent.parent / "assets" / "cyai-logo.png"


def _get_logo_base64() -> str:
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_full_html(subject: str, html_content: str) -> str:
    logo_b64 = _get_logo_base64()

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #F2E9D8;
    color: #2A2A2A;
    font-family: 'IBM Plex Sans', sans-serif;
    padding: 0;
  }}
  .page {{
    max-width: 800px;
    margin: 0 auto;
    background: #FAF7F0;
  }}
  .header {{
    background: white;
    padding: 24px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 4px solid #C41E3A;
  }}
  .header img {{
    width: 56px;
    height: 56px;
    border-radius: 50%;
  }}
  .header h1 {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 28px;
    margin: 0;
  }}
  .header h1 span {{ color: #C41E3A; }}
  .content {{
    padding: 32px;
  }}
  .content h2 {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 24px;
    color: #C41E3A;
    border-bottom: 2px solid #E3A83B;
    padding-bottom: 8px;
    margin-top: 32px;
  }}
  .content strong {{ color: #2A2A2A; }}
  .content a {{ color: #C41E3A; font-weight: 600; text-decoration: none; }}
  .content ul {{ padding-left: 0; list-style: none; }}
  .content li {{
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid #A8B4D8;
  }}
  .footer {{
    background: #2A2A2A;
    color: #F2E9D8;
    padding: 20px 32px;
    text-align: center;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
  }}
</style>
</head>
<body>
  <div class="page">
    <div class="header">
      <img src="data:image/png;base64,{logo_b64}" alt="CYAI Logo">
      <h1>CY<span>AI</span> Newsletter</h1>
    </div>
    <div class="content">
      {html_content}
    </div>
    <div class="footer">
      Cybersecurity &amp; Artificial Intelligence Club &middot; York College, CUNY
    </div>
  </div>
</body>
</html>"""


def render_newsletter_pdf(subject: str, html_content: str) -> bytes:
    full_html = _build_full_html(subject, html_content)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html, wait_until="networkidle")
        pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        browser.close()

    return pdf_bytes


def render_newsletter_image(subject: str, html_content: str) -> bytes:
    full_html = _build_full_html(subject, html_content)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 600})
        page.set_content(full_html, wait_until="networkidle")
        image_bytes = page.screenshot(full_page=True)
        browser.close()

    return image_bytes
