#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 README 里自带的两张图表（贡献热力图 + 数据面板）。

不依赖任何第三方图片服务：数据从 GitHub 公开接口抓取，SVG 直接写进 assets/，
所以页面上永远不会出现"裂图"。

用法:
    python scripts/gen_assets.py                 # 抓取 oneroomlife 的数据
    python scripts/gen_assets.py --user name --out assets
环境变量 GITHUB_TOKEN 可选，用于抬高 REST API 的速率上限。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime

UA = "oneroomlife-profile-assets/1.0 (+https://github.com/oneroomlife)"

# ── 配色（与 assets/*.svg 的紫粉蓝主题一致）─────────────────────────────────
LIGHT = {
    "levels": ["#eef0f6", "#dccbf7", "#bf9bef", "#9a6ee6", "#7440d6"],
    "text": "#6b7280",
    "muted": "#9aa4b2",
    "track": "#eeecf6",
    "card": "#f7f5fd",
}
DARK = {
    "levels": ["#262a35", "#3a2f63", "#55459e", "#7d63cf", "#a98cf7"],
    "text": "#9aa4b2",
    "muted": "#7b8494",
    "track": "#262a33",
    "card": "#1b1f27",
}
LANG_COLORS = ["#7F52FF", "#3776AB", "#F7DF1E", "#FB7299", "#00A1D6", "#8B7BD8", "#4B8BBE"]
FONT = "'Segoe UI','PingFang SC','Microsoft YaHei','Helvetica Neue',Arial,sans-serif"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ── HTTP ────────────────────────────────────────────────────────────────────
def _curl(url: str, token: str | None = None) -> str:
    """urllib 在某些网络（例如本机被 TLS 拦截）会握手失败，退回系统 curl。"""
    cmd = ["curl", "-sSL", "--max-time", "30", "-A", UA, url]
    if token and "api.github.com" in url:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    import subprocess

    out = subprocess.run(cmd, capture_output=True, check=True)
    return out.stdout.decode("utf-8", "replace")


def fetch(url: str, token: str | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return _curl(url, token)


def fetch_json(url: str, token: str | None = None):
    return json.loads(fetch(url, token))


# ── 数据 ────────────────────────────────────────────────────────────────────
CELL_TAG = re.compile(r"<td\b[^>]*>")
ATTR = {
    "date": re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"'),
    "level": re.compile(r'data-level="(\d)"'),
    "id": re.compile(r'id="contribution-day-component-(\d+)-(\d+)"'),
}
COUNT = re.compile(r">(\d+) contributions? on ")


def contributions(user: str) -> list[dict]:
    """抓 GitHub 的公开贡献日历 HTML，解析出 (周, 星期, 日期, 等级)。"""
    html = fetch(f"https://github.com/users/{user}/contributions")
    cells, week_seen = [], 0
    for tag in CELL_TAG.findall(html):
        m_date, m_level, m_id = ATTR["date"].search(tag), ATTR["level"].search(tag), ATTR["id"].search(tag)
        if not (m_date and m_level and m_id):
            continue
        cells.append(
            {
                "date": m_date.group(1),
                "level": int(m_level.group(1)),
                "week": int(m_id.group(2)),
                "dow": int(m_id.group(1)),
            }
        )
        week_seen = max(week_seen, int(m_id.group(2)) + 1)
    if not cells:
        raise RuntimeError("贡献日历解析失败：没有匹配到任何格子")

    counts = [int(x) for x in COUNT.findall(html)]
    total = sum(counts) if counts else sum(c["level"] for c in cells)
    return cells, total, week_seen


def profile(user: str, token: str | None):
    u = fetch_json(f"https://api.github.com/users/{user}", token)
    repos = fetch_json(f"https://api.github.com/users/{user}/repos?per_page=100&sort=updated", token)
    langs: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            for name, size in fetch_json(repo["languages_url"], token).items():
                langs[name] = langs.get(name, 0) + int(size)
        except Exception:  # 单个仓库失败不影响整体
            continue
    return {
        "stars": sum(r.get("stargazers_count", 0) for r in repos),
        "forks": sum(r.get("forks_count", 0) for r in repos),
        "repos": u.get("public_repos", len(repos)),
        "followers": u.get("followers", 0),
        "langs": langs,
    }


# ── 贡献热力图 ──────────────────────────────────────────────────────────────
def contribution_svg(cells, total: int, weeks: int, theme: dict, dark: bool) -> str:
    pitch, cell, left, top = 19, 14, 34, 24
    width = left + weeks * pitch + 12
    height = top + 7 * pitch + 34

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{total} contributions in the last year">',
        "  <style>"
        f"text{{font-family:{FONT};}}"
        "</style>",
    ]

    # 月份标签
    last_month, placed = None, -2
    for w in range(weeks):
        col = [c for c in cells if c["week"] == w]
        if not col:
            continue
        first = min(col, key=lambda c: c["dow"])
        m = datetime.strptime(first["date"], "%Y-%m-%d").month
        if m != last_month and w - placed >= 3:
            x = left + w * pitch
            parts.append(
                f'  <text x="{x}" y="14" font-size="11.5" fill="{theme["muted"]}">{MONTHS[m - 1]}</text>'
            )
            placed = w
        last_month = m

    # 星期标签（只标 Mon / Wed / Fri）
    for dow, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = top + dow * pitch + cell - 3
        parts.append(f'  <text x="0" y="{y}" font-size="11" fill="{theme["muted"]}">{name}</text>')

    # 格子
    for c in cells:
        x = left + c["week"] * pitch
        y = top + c["dow"] * pitch
        parts.append(
            f'  <rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3.5" '
            f'fill="{theme["levels"][min(c["level"], 4)]}"><title>{c["date"]}</title></rect>'
        )

    # 图例 + 统计
    ly = height - 14
    parts.append(
        f'  <text x="0" y="{ly}" font-size="11.5" fill="{theme["text"]}">{total} contributions in the last year</text>'
    )
    legend_x = width - 12 - (5 * (cell - 2) + 4 * 4) - 62
    parts.append(f'  <text x="{legend_x - 8}" y="{ly}" font-size="11" fill="{theme["muted"]}" text-anchor="end">Less</text>')
    for i, color in enumerate(theme["levels"]):
        parts.append(
            f'  <rect x="{legend_x + i * (cell + 2)}" y="{ly - 11}" width="{cell - 2}" height="{cell - 2}" '
            f'rx="3" fill="{color}"/>'
        )
    parts.append(
        f'  <text x="{legend_x + 5 * (cell + 2) + 4}" y="{ly}" font-size="11" fill="{theme["muted"]}">More</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# ── 数据面板 ────────────────────────────────────────────────────────────────
def stats_svg(data: dict, theme: dict, dark: bool) -> str:
    width, height = 1060, 232
    cards = [
        (data["stars"], "Stars", "收下的星星"),
        (data["forks"], "Forks", "被分走的版本"),
        (data["repos"], "Repositories", "公开仓库"),
        (data["followers"], "Followers", "同行的人"),
    ]
    col_w = width / len(cards)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GitHub stats">',
        f"  <style>text{{font-family:{FONT};}}</style>",
    ]
    for i, (value, label, sub) in enumerate(cards):
        cx = col_w * i + col_w / 2
        parts.append(
            f'  <text x="{cx:.0f}" y="86" font-size="44" font-weight="700" fill="#7f5ade" '
            f'text-anchor="middle">{value}</text>'
        )
        parts.append(
            f'  <text x="{cx:.0f}" y="112" font-size="13" font-weight="600" fill="{theme["text"]}" '
            f'text-anchor="middle">{label}</text>'
        )
        parts.append(
            f'  <text x="{cx:.0f}" y="132" font-size="11" fill="{theme["muted"]}" text-anchor="middle">{sub}</text>'
        )
        if i:
            parts.append(
                f'  <rect x="{col_w * i:.0f}" y="46" width="1" height="96" fill="{theme["track"]}"/>'
            )

    # 语言条
    langs = sorted(data["langs"].items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in langs) or 1
    x, bar_y, bar_h, bar_w = 34.0, 168.0, 12.0, float(width - 68)
    parts.append(f'  <text x="34" y="{bar_y - 10}" font-size="12" font-weight="600" fill="{theme["text"]}">语言构成</text>')
    parts.append(f'  <rect x="{x:.0f}" y="{bar_y:.0f}" width="{bar_w:.0f}" height="{bar_h}" rx="6" fill="{theme["track"]}"/>')
    offset = 0.0
    for i, (name, size) in enumerate(langs):
        w = bar_w * size / total
        parts.append(
            f'  <rect x="{x + offset:.1f}" y="{bar_y:.0f}" width="{max(w, 2):.1f}" height="{bar_h}" '
            f'rx="6" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>'
        )
        offset += w
    lx = 34.0
    for i, (name, size) in enumerate(langs):
        pct = size * 100 / total
        color = LANG_COLORS[i % len(LANG_COLORS)]
        parts.append(f'  <circle cx="{lx + 4:.0f}" cy="204" r="4" fill="{color}"/>')
        text = f"{name} {pct:.1f}%"
        parts.append(f'  <text x="{lx + 14:.0f}" y="208" font-size="11.5" fill="{theme["text"]}">{text}</text>')
        lx += 20 + len(text) * 7.0
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# ── 入口 ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="oneroomlife")
    ap.add_argument("--out", default="assets")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    os.makedirs(args.out, exist_ok=True)

    cells, total, weeks = contributions(args.user)
    data = profile(args.user, token)

    outputs = {
        "contribution-graph.svg": contribution_svg(cells, total, weeks, LIGHT, False),
        "contribution-graph-dark.svg": contribution_svg(cells, total, weeks, DARK, True),
        "stats.svg": stats_svg(data, LIGHT, False),
        "stats-dark.svg": stats_svg(data, DARK, True),
    }
    for name, svg in outputs.items():
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)} bytes)")

    print(
        f"contributions={total} weeks={weeks} stars={data['stars']} forks={data['forks']} "
        f"repos={data['repos']} followers={data['followers']} langs={len(data['langs'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
