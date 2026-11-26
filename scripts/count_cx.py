"""Count visible climaxes in a ws-bot/1 seat observation using only that seat's evidence."""

import argparse
import json
import sys
from math import comb


def read_result(path):
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
    if "error" in data:
        raise ValueError(str(data["error"]))
    result = data.get("result", data)
    if "content" in result:
        text = result["content"][0]["text"]
        if result.get("isError"):
            raise ValueError(text)
        return json.loads(text)
    return result


def outside_cards(obs, seat):
    player = obs["players"][seat]
    for zone in ("wr", "clock", "level", "memory", "hand"):
        for card in player[zone]:
            yield zone, card
    if player["climax"]:
        yield "climax", player["climax"]
    for slot, character in enumerate(player["stage"]):
        if character:
            yield f"stage[{slot}]", character["card"]
            for card in character["markers"]:
                yield f"stage[{slot}].markers", card

    # A look or show can display a card that is still in its deck.
    window = obs.get("resolution") or {}
    if window.get("kind") in ("trig", "dmg", "dmgBoth"):
        for card in window["cards"]:
            owner = card.get("p") if window["kind"] == "dmgBoth" else window.get("p")
            if owner == seat:
                yield window["kind"], card


def count_cx(state, catalog, seat=None, total_cx=None, damage=None):
    obs = state.get("obs")
    if not obs:
        raise ValueError("当前状态还没有棋盘")
    if seat is None:
        seat = 1 - obs["seat"]
    deck = obs["players"][seat]["deck"]
    if not 0 <= deck <= 50 or total_cx is not None and not 0 <= total_cx <= 8:
        raise ValueError("按标准 50 张牌组计算，总高潮数应在 0 至 8 之间")

    seen, missing = set(), set()
    climaxes = []
    for zone, card in outside_cards(obs, seat):
        uid, card_id = card["u"], card["id"]
        if uid <= 0 or card_id == "_" or card.get("hidden") or uid in seen:
            continue
        kind = (catalog.get(card_id) or {}).get("type")
        if kind not in ("C", "E", "X"):
            missing.add(card_id)
            continue
        seen.add(uid)
        if kind == "X":
            climaxes.append({"u": uid, "id": card_id, "zone": zone})

    unknown_outside = 50 - deck - len(seen)
    outside_cx = len(climaxes)
    high = min(deck, (8 if total_cx is None else total_cx) - outside_cx)
    low = 0 if total_cx is None else max(0, total_cx - outside_cx - unknown_outside)
    if unknown_outside < 0 or low > high:
        raise ValueError("数量与该席的 50 张牌不符，请核对快照、总潮数及跨席移牌")
    result = {
        "seat": seat, "deck": deck, "knownOutsideCx": climaxes,
        "unknownOutsideCards": unknown_outside, "deckCxRange": [low, high],
        "lookupIds": sorted(missing),
    }
    if damage is not None:
        if damage < 0:
            raise ValueError("伤害应为非负整数")
        result["damage"] = damage
        if damage > deck:
            result["cancelPctIfRandom"] = None
            result["note"] = "这包伤害可能跨重洗，单副牌库的公式不适用"
        else:
            ways = comb(deck, damage)
            result["cancelPctIfRandom"] = [
                round(100 * (ways - comb(deck - k, damage)) / ways, 2) for k in (low, high)
            ]
    return result


def main():
    parser = argparse.ArgumentParser(description="根据可见快照估算当前牌库的潮数与普通伤害取消率")
    parser.add_argument("state", help="ws_game_state、ws_start_game 或 ws_play 的 JSON，- 表示标准输入")
    parser.add_argument("info", nargs="*", help="补充的 ws_card_info JSON 文件")
    parser.add_argument("--seat", type=int, choices=(0, 1), help="默认分析对手")
    parser.add_argument("--total-cx", type=int, help="原牌组已确认的总高潮数，缺省只用上限 8")
    parser.add_argument("--damage", type=int, help="单次普通伤害的点数")
    args = parser.parse_args()
    try:
        state = read_result(args.state)
        cards = dict(state["cards"])
        for path in args.info:
            cards.update({k: v for k, v in read_result(path)["cards"].items() if v})
        summary = count_cx(state, cards, args.seat, args.total_cx, args.damage)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        parser.exit(2, f"{parser.prog} — {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
