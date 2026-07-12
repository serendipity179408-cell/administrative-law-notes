#!/usr/bin/env python3
"""
掃描 repository 根目錄下所有符合「NN_主題.html」命名規則的筆記檔案，
自動重新產生 index.html 中 <!-- AUTO-GENERATED-LIST-START/END --> 之間的清單區塊。

命名規則：
  01_基礎理論與行政定義.html
  02_行政組織.html
  ...
- 開頭需為數字（可一位數或多位數），底線後接主題，副檔名為 .html
- 不符合規則的 .html 檔案（包含 index.html 本身）會被忽略

每份筆記檔案的卡片標題與副標，會嘗試從該筆記 HTML 內的
<h1>...</h1> 與 <div class="eyebrow">...</div> 擷取；
擷取不到時，退回使用檔名本身作為標題。
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "index.html")
START_MARKER = "<!-- AUTO-GENERATED-LIST-START -->"
END_MARKER = "<!-- AUTO-GENERATED-LIST-END -->"

FILENAME_RE = re.compile(r'^(\d+)_(.+)\.html$')
TAG_STRIP_RE = re.compile(r'<[^<]+?>')


def strip_tags(s: str) -> str:
    return TAG_STRIP_RE.sub('', s).strip()


def extract_h1(content: str):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.S)
    return strip_tags(m.group(1)) if m else None


def extract_eyebrow(content: str):
    m = re.search(r'<div class="eyebrow"[^>]*>(.*?)</div>', content, re.S)
    return strip_tags(m.group(1)) if m else None


def collect_entries():
    entries = []
    for fname in sorted(os.listdir(ROOT)):
        if fname == "index.html" or not fname.endswith(".html"):
            continue
        m = FILENAME_RE.match(fname)
        if not m:
            print(f"[skip] 檔名不符合 NN_主題.html 規則，略過：{fname}")
            continue
        num_str, slug = m.groups()
        path = os.path.join(ROOT, fname)
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"[warn] 無法讀取 {fname}：{e}")
            content = ""

        title = extract_h1(content) or slug.replace("_", " ")
        eyebrow = extract_eyebrow(content) or ""

        entries.append({
            "num": int(num_str),
            "num_str": num_str,
            "fname": fname,
            "title": title,
            "eyebrow": eyebrow,
        })

    entries.sort(key=lambda e: e["num"])
    return entries


def build_html(entries):
    if not entries:
        return '  <div class="empty-slot">尚無筆記檔案</div>\n'

    cards = []
    for e in entries:
        cards.append(
            '  <a class="note-card" href="{fname}">\n'
            '    <div class="note-card-top">\n'
            '      <span class="note-card-title">第{num}堂課：{title}</span>\n'
            '      <svg class="note-card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>\n'
            '    </div>\n'
            '    <div class="note-card-desc">{eyebrow}</div>\n'
            '  </a>\n'.format(
                fname=e["fname"],
                num=e["num_str"],
                title=e["title"],
                eyebrow=e["eyebrow"],
            )
        )
    return "".join(cards)


def main():
    if not os.path.exists(INDEX_PATH):
        print(f"[error] 找不到 {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, encoding="utf-8") as f:
        index_content = f.read()

    if START_MARKER not in index_content or END_MARKER not in index_content:
        print("[error] index.html 缺少 AUTO-GENERATED-LIST 標記，無法自動更新。", file=sys.stderr)
        sys.exit(1)

    entries = collect_entries()
    list_html = build_html(entries)
    new_block = f"{START_MARKER}\n{list_html}  {END_MARKER}"

    pattern = re.compile(re.escape(START_MARKER) + r'.*?' + re.escape(END_MARKER), re.S)
    new_index = pattern.sub(lambda _m: new_block, index_content)

    if new_index != index_content:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            f.write(new_index)
        print(f"index.html 已更新，共 {len(entries)} 份筆記。")
    else:
        print("index.html 內容無需變更。")


if __name__ == "__main__":
    main()
