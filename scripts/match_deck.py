"""Check whether a deck plan was written for the exact 50 cards in a game."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


def count_cards(lines):
    cards = Counter()
    for line_number, line in enumerate(lines, 1):
        row = line.strip()
        if not row or row.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9]+)\s*[xX×]?\s+(\S+/\S+(?: SP)?)", row)
        if not match or int(match[1]) < 1:
            raise ValueError(f"第 {line_number} 行需要正整数张数和完整官方卡号，读到 {row!r}")
        cards[match[2]] += int(match[1])
    total = sum(cards.values())
    if total != 50:
        raise ValueError(f"完整构筑应有 50 张，实际读到 {total} 张")
    return cards


def plan_cards(path):
    lines = iter(path.read_text(encoding="utf-8-sig").splitlines())
    heading = next((line for line in lines if line.startswith("## ")), "")
    if heading[3:].strip() != "构筑":
        raise ValueError("打法文档第一章应为「构筑」")
    cards = None
    for line in lines:
        if line.startswith("## "):
            break
        if line.strip() != "```text":
            continue
        if cards is not None:
            raise ValueError("「构筑」章只能放一份完整牌表")
        rows = []
        for row in lines:
            if row.strip() == "```":
                break
            rows.append(row)
        else:
            raise ValueError("牌表代码块缺少结束标记")
        cards = count_cards(rows)
    if cards is None:
        raise ValueError("「构筑」章缺少完整牌表的 text 代码块")
    return cards


def current_cards(source, preset_id):
    if source == "-":
        text = sys.stdin.read().lstrip("\ufeff")
    else:
        text = Path(source).read_text(encoding="utf-8-sig")
    if preset_id is None:
        return count_cards(text.splitlines())
    presets = json.loads(text)
    if isinstance(presets, list):
        for preset in presets:
            if isinstance(preset, dict) and preset.get("id") == preset_id:
                listing = preset.get("list")
                if isinstance(listing, dict):
                    return count_cards(f"{count} {number}" for number, count in listing.items())
                raise ValueError(f"预组 {preset_id} 缺少构筑清单")
    raise ValueError(f"在提供的预组文件中找不到 {preset_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="候选打法 Markdown")
    parser.add_argument("source", help="本次导出的牌表、预组 JSON 文件或 -（标准输入）")
    parser.add_argument("--preset", help="从预组 JSON 的指定 ID 读取本次构筑")
    args = parser.parse_args()
    try:
        actual = current_cards(args.source, args.preset)
        expected = plan_cards(args.plan)
    except (OSError, ValueError) as error:
        print(f"无法核对构筑，{error}", file=sys.stderr)
        return 2
    if actual == expected:
        print(f"构筑完全相同，共 {len(actual)} 个卡号、50 张。")
        return 0
    print("构筑不同。")
    for number in sorted(actual.keys() | expected.keys()):
        if actual[number] != expected[number]:
            print(f"{number}　本次 {actual[number]} 张，文档 {expected[number]} 张")
    return 1


if __name__ == "__main__":
    sys.exit(main())
