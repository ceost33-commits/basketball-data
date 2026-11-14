"""배트맨토토 프로토 승부식 적중결과 DOM 추출 원자료(raw/*.json)를 정규화해 data/matches.json을 만든다.

원칙
- 확정 수치만 사용한다(배트맨토토 모바일 적중결과 DOM + orgDetlBody).
- 취소된 회차 중복분은 같은 경기번호의 '정산본'으로 대체한다.
- 핸디캡 기준점이 여러 번 변동된 경기는 마지막(마감) 회차를 기준점으로 쓰고, 변동 이력을 남긴다.
- 핸디캡 표기는 마핸/플핸 두 가지만 쓴다.
"""
import json
import os
import re
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "raw")
OUT = os.path.join(BASE, "data", "matches.json")

FILES = ["rounds_117_118.json", "rounds_119_129.json", "rounds_127_128.json", "rounds_130_134.json", "rounds_135.json"]


def parse_date(s):
    # "26.11.14 (토) 14:00" -> "2026-11-14 14:00"
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{2})", s)
    t = re.search(r"(\d{2}):(\d{2})", s)
    return f"20{m.group(1)}-{m.group(2)}-{m.group(3)} {t.group(1)}:{t.group(2)}" if t else f"20{m.group(1)}-{m.group(2)}-{m.group(3)}"


def num(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


def parse_line(pt):
    # "H +1.5" -> 1.5, "H -6.5" -> -6.5
    m = re.search(r"([+-])\s*(\d+(?:\.\d+)?)", pt or "")
    if not m:
        return None
    v = float(m.group(2))
    return -v if m.group(1) == "-" else v


def score_pair(v):
    m = re.match(r"(\d+):(\d+)$", (v or "").strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def main():
    rounds = {}
    for fn in FILES:
        with open(os.path.join(RAW, fn), encoding="utf-8") as f:
            d = json.load(f)
        for k, v in d.items():
            if k.isdigit():
                rounds.setdefault(k, []).extend(v)

    # 경기번호 -> 게임(정산본 우선) 및 회차 기록
    games = {}
    for ts in sorted(rounds):
        for g in rounds[ts]:
            x = g["x"]
            sp = next((i for i in x if i[0] == "sp"), None)
            if sp is None:
                continue
            cancelled = sp[2] == "취소"
            rec = games.get(g["s"])
            if rec is None:
                games[g["s"]] = {"g": g, "ts": ts, "cancelled": cancelled}
            elif rec["cancelled"] and not cancelled:
                games[g["s"]] = {"g": g, "ts": ts, "cancelled": False}
            elif not rec["cancelled"] and not cancelled:
                # 같은 경기가 두 회차에 정상 표기된 경우: 먼저 나온 회차 유지
                pass

    mens, womens, skipped = [], [], []
    for seq, item in games.items():
        g, ts = item["g"], item["ts"]
        x = g["x"]
        sp = next((i for i in x if i[0] == "sp"), None)
        if sp is None:
            continue
        if item["cancelled"] or sp[2] in ("취소", "") or "-" == sp[3]:
            skipped.append((seq, g["d"], g["h"], g["a"], sp[2]))
            continue
        sc = score_pair(sp[3])
        if not sc:
            skipped.append((seq, g["d"], g["h"], g["a"], "no-score"))
            continue
        hs, as_ = sc
        if hs == as_:
            skipped.append((seq, g["d"], g["h"], g["a"], "draw"))
            continue

        home_odds, away_odds = num(sp[5]), num(sp[6])
        winner = "HOME" if sp[2] == "승" else "AWAY"
        if home_odds is not None and away_odds is not None:
            favorite = "HOME" if home_odds <= away_odds else "AWAY"
        else:
            favorite = None
        hit_odds = num(sp[4])
        hit_type = None
        if favorite:
            hit_type = "정배" if favorite == winner else "역배"

        # 핸디캡: 마지막(마감) 라인 사용
        hcs = [i for i in x if i[0] == "hc" and i[2] in ("승", "패") and parse_line(i[1]) is not None]
        handicap = None
        if hcs:
            last = hcs[-1]
            std = parse_line(last[1])
            cover = last[2] == "승"          # 홈팀이 기준점을 넘겼는가
            if std < 0:
                mh = "마핸" if cover else "플핸"
            else:
                mh = "플핸" if cover else "마핸"
            handicap = {
                "match_no": seq,
                "standard": std,              # 홈 기준 부호 있는 기준점
                "home_odds": num(last[5]),
                "away_odds": num(last[6]),
                "home_cover": cover,
                "result": mh,                 # 마핸 / 플핸
                "hit_odds": num(last[4]),
                "line_count": len(hcs),
                "line_history": [{"standard": parse_line(i[1]), "cover": i[2] == "승", "hit_odds": num(i[4])} for i in hcs],
            }

        # 언더오버: 마지막(마감) 라인 사용
        uos = [i for i in x if i[0] == "uo" and i[2] in ("오버", "언더")]
        under_over = None
        if uos:
            last = uos[-1]
            line = None
            mm = re.search(r"U/O\s*([\d.]+)", last[1] or "")
            if mm:
                line = float(mm.group(1))
            under_over = {
                "match_no": seq,
                "standard": line,
                "over_odds": num(last[6]),
                "under_odds": num(last[5]),
                "total": int(last[3]) if (last[3] or "").isdigit() else None,
                "result": "OVER" if last[2] == "오버" else "UNDER",
                "hit_odds": num(last[4]),
                "line_count": len(uos),
            }

        w5 = next((i for i in x if i[0] == "w5"), None)
        rec = {
            "id": f"{'M' if g['l'] == 'KBL' else 'W'}{seq}",
            "seq": seq,
            "date": parse_date(g["d"]),
            "round": f"프로토 승부식 {int(ts[-3:])}회차",
            "round_ts": int(ts),
            "league": g["l"],
            "home": g["h"],
            "away": g["a"],
            "status": "종료",
            "home_score": hs,
            "away_score": as_,
            "score": f"{hs}:{as_}",
            "margin": hs - as_,
            "total_points": hs + as_,
            "win_lose": {
                "match_no": seq,
                "home_odds": home_odds,
                "away_odds": away_odds,
                "winner": winner,
                "favorite": favorite,
                "hit_odds": hit_odds,
                "hit_type": hit_type,
            },
            "handicap": handicap,
            "under_over": under_over,
            "w5": None if w5 is None or w5[2] not in ("승", "5", "패") else {"match_no": seq, "result": w5[2]},
        }
        (mens if g["l"] == "KBL" else womens).append(rec)

    key = lambda r: (r["date"], r["seq"])
    mens.sort(key=key)
    womens.sort(key=key)

    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "m.betman.co.kr 프로토 승부식 적중결과 (winrstDetl.do) DOM",
        "labels": {
            "handicap": "마핸/플핸 (홈 기준 '-' 핸디캡 팀이 기준점을 넘기면 마핸, '+' 핸디캡 팀이 지켜내면 플핸)",
            "hit_type": "정배 = 마감 배당이 낮은 팀 적중 / 역배 = 마감 배당이 높은 팀 적중",
        },
        "mens": mens,
        "womens": womens,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] {OUT}")
    print(f"KBL {len(mens)}경기: {mens[0]['date']} ~ {mens[-1]['date']}")
    if womens:
        print(f"WKBL {len(womens)}경기: {womens[0]['date']} ~ {womens[-1]['date']}")
    print(f"제외(취소/무효) {len(skipped)}건")
    # 검증용 요약
    for name, arr in (("KBL", mens), ("WKBL", womens)):
        fav = sum(1 for r in arr if r["win_lose"]["hit_type"] == "정배")
        over = sum(1 for r in arr if r["under_over"] and r["under_over"]["result"] == "OVER")
        ma = sum(1 for r in arr if r["handicap"] and r["handicap"]["result"] == "마핸")
        multi = sum(1 for r in arr if r["handicap"] and r["handicap"]["line_count"] > 1)
        print(f"  {name}: 정배 {fav} 역배 {len(arr)-fav} | 오버 {over} 언더 {len(arr)-over} | 마핸 {ma} 플핸 {len(arr)-ma} | 핸디 변동 {multi}경기")
    dates = sorted({r["date"][:10] for r in mens})
    print("KBL 경기일수:", len(dates), dates[0], "~", dates[-1])


if __name__ == "__main__":
    main()
