#!/usr/bin/env python3
"""
自動掃描目前資料夾下所有筆記 HTML 檔案（排除 index.html），
讀取每份檔案 <head> 裡的 note-title / note-desc / note-tags / note-unit
meta 標籤，重新產生 index.html。

用法：python3 generate_index.py
（GitHub Actions 會自動執行，不需要手動跑）
"""

import re
import os
import glob
import html

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(REPO_ROOT, "index.html")
COURSE_TITLE = "行政法｜徐偉超"
EYEBROW = "課程筆記主頁"

def extract_meta(content, name, default=""):
    m = re.search(
        r'<meta\s+name=["\']' + re.escape(name) + r'["\']\s+content=["\'](.*?)["\']\s*/?>',
        content, re.IGNORECASE | re.DOTALL
    )
    return html.unescape(m.group(1)).strip() if m else default

def extract_title_tag(content, default="未命名筆記"):
    m = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    return html.unescape(m.group(1)).strip() if m else default

def build_note_card(filename, content):
    title = extract_meta(content, "note-title") or extract_title_tag(content, filename)
    desc = extract_meta(content, "note-desc")
    tags_raw = extract_meta(content, "note-tags")
    unit = extract_meta(content, "note-unit", default="未分類")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
    desc_html = f'<div class="note-card-desc">{html.escape(desc)}</div>' if desc else ""
    meta_html = f'<div class="note-card-meta">{tags_html}</div>' if tags else ""

    card = f'''    <a class="note-card" href="{html.escape(filename)}">
      <div class="note-card-top">
        <span class="note-card-title">{html.escape(title)}</span>
        <svg class="note-card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      </div>
      {desc_html}
      {meta_html}
    </a>'''
    return unit, card

def main():
    html_files = sorted(
        f for f in glob.glob(os.path.join(REPO_ROOT, "*.html"))
        if os.path.basename(f).lower() != "index.html"
    )

    units = {}  # unit_name -> [card_html, ...], insertion order preserved by first appearance
    unit_order = []

    for filepath in html_files:
        filename = os.path.basename(filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        unit, card = build_note_card(filename, content)
        if unit not in units:
            units[unit] = []
            unit_order.append(unit)
        units[unit].append(card)

    if not html_files:
        body_sections = '    <div class="empty-slot">目前資料夾內尚無筆記檔案</div>\n'
    else:
        sections = []
        for unit in unit_order:
            cards = "\n\n".join(units[unit])
            sections.append(f'''  <div class="unit-group">
    <div class="unit-group-title">{html.escape(unit)}</div>

{cards}
  </div>''')
        body_sections = "\n\n".join(sections) + "\n"

    output = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(COURSE_TITLE)}</title>
<style>
  :root {{
    --bg: #ffffff;
    --bg-soft: #fafafa;
    --ink: #1a1a1a;
    --ink-soft: #555555;
    --line: #e5e5e5;
    --tag-bg: #eef0ec;
    --tag-ink: #4a5a45;
    --max-width: 760px;
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang TC", "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    line-height: 1.7;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
  }}

  .wrap {{
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 48px 24px 100px;
  }}

  header.page-header {{
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--line);
  }}
  header.page-header .eyebrow {{
    font-size: 13px;
    color: var(--ink-soft);
    letter-spacing: 0.05em;
    margin-bottom: 8px;
  }}
  header.page-header h1 {{
    font-size: 26px;
    margin: 0;
    line-height: 1.4;
  }}

  .unit-group {{
    margin-bottom: 36px;
  }}
  .unit-group-title {{
    font-size: 13px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--ink-soft);
    font-weight: 700;
    margin-bottom: 12px;
  }}

  .note-card {{
    display: block;
    text-decoration: none;
    color: inherit;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    background: var(--bg);
    transition: border-color 0.15s, background 0.15s;
  }}
  .note-card:hover {{
    border-color: #c9c9c9;
    background: var(--bg-soft);
  }}
  .note-card-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }}
  .note-card-title {{
    font-size: 16.5px;
    font-weight: 700;
    color: var(--ink);
  }}
  .note-card-arrow {{
    flex-shrink: 0;
    width: 18px;
    height: 18px;
    color: var(--ink-soft);
    transition: transform 0.15s;
  }}
  .note-card:hover .note-card-arrow {{
    transform: translateX(3px);
  }}
  .note-card-desc {{
    font-size: 14px;
    color: var(--ink-soft);
    margin-top: 6px;
  }}
  .note-card-meta {{
    display: flex;
    gap: 8px;
    margin-top: 10px;
    flex-wrap: wrap;
  }}
  .tag {{
    display: inline-block;
    background: var(--tag-bg);
    color: var(--tag-ink);
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 600;
  }}

  .empty-slot {{
    border: 1px dashed var(--line);
    border-radius: 10px;
    padding: 18px 20px;
    color: var(--ink-soft);
    font-size: 14.5px;
    text-align: center;
  }}

  footer.page-footer {{
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid var(--line);
    font-size: 13px;
    color: var(--ink-soft);
  }}

  @media (max-width: 600px) {{
    .wrap {{ padding: 32px 18px 80px; }}
    header.page-header h1 {{ font-size: 22px; }}
  }}
</style>
</head>
<body>

<div class="wrap">

  <header class="page-header">
    <div class="eyebrow">{html.escape(EYEBROW)}</div>
    <h1>{html.escape(COURSE_TITLE)}</h1>
  </header>

{body_sections}
  <footer class="page-footer">
    <p>此頁面由腳本自動產生，每次上傳新筆記後會自動重新整理清單。</p>
  </footer>

</div>

</body>
</html>
'''

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"已產生 index.html，共收錄 {len(html_files)} 份筆記。")

if __name__ == "__main__":
    main()
