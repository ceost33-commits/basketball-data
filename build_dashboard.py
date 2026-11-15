"""KBL·WKBL 배트맨토토 누적 통계 대시보드 빌더 (단일 index.html, 무자바스크립트·모바일 노스크롤).

- 데이터: data/matches.json (배트맨토토 프로토 승부식 적중결과 DOM 확정 수치만)
- 뷰: 남자부(KBL)/여자부(WKBL) × 전체/구단별, 순수 CSS 라디오 전환
- 지표: 승패, 정배/역배, 마핸/플핸, 언더/오버, 승5패, 연속 스트릭
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "matches.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "index.html")

with open(DATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

TEAM_INFO = {
    # betman 표기: (표시명, 풀네임, 포인트색)
    "부산KCC": ("KCC", "부산 KCC 이지스", "#ef4444"),
    "창원LG": ("LG", "창원 LG 세이커스", "#dc2626"),
    "고양소노": ("소노", "고양 소노 스카이거너스", "#f59e0b"),
    "한국가스": ("가스공사", "대구 한국가스공사 페가수스", "#38bdf8"),
    "안양정관": ("정관장", "안양 정관장 레드부스터스", "#fb7185"),
    "울산모비": ("현대모비스", "울산 현대모비스 피버스", "#22d3ee"),
    "원주DB": ("DB", "원주 DB 프로미", "#60a5fa"),
    "KT소닉붐": ("KT", "수원 KT 소닉붐", "#a3a3a3"),
    "서울SK": ("SK", "서울 SK 나이츠", "#f87171"),
    "서울삼성": ("삼성", "서울 삼성 썬더스", "#818cf8"),
    "KB스타즈": ("KB", "청주 KB 스타즈", "#fbbf24"),
    "BNK썸": ("BNK", "부산 BNK 썸", "#f43f5e"),
    "삼성생명": ("삼성생명", "용인 삼성생명 블루밍스", "#38bdf8"),
    "우리은행": ("우리은행", "아산 우리은행 우리WON", "#60a5fa"),
    "하나은행": ("하나은행", "부천 하나은행", "#34d399"),
    "신한은행": ("신한은행", "인천 신한은행 에스버드", "#818cf8"),
}


def short(team):
    return TEAM_INFO.get(team, (team, team, "#64748b"))[0]


def color(team):
    return TEAM_INFO.get(team, (team, team, "#64748b"))[2]


def full(team):
    return TEAM_INFO.get(team, (team, team, "#64748b"))[1]


def teams_of(matches):
    order = []
    for m in matches:
        for t in (m["home"], m["away"]):
            if t not in order:
                order.append(t)
    return order


def won(m, team):
    return (m["win_lose"]["winner"] == "HOME") == (m["home"] == team)


def team_matches(matches, team):
    return [m for m in matches if team in (m["home"], m["away"])]


def streaks(flags):
    """최근 경기부터 이어진 같은 값의 길이"""
    if not flags:
        return None, 0
    first = flags[-1]
    n = 0
    for f in reversed(flags):
        if f == first:
            n += 1
        else:
            break
    return first, n


def pct(a, b):
    return round(a / b * 100) if b else 0


def odds_txt(v):
    if v is None:
        return "-"
    return f"{v:.2f}"


# ---------------------------------------------------------------- 뱃지/카드

def badge(text, kind):
    return f'<span class="bdg bdg-{kind}">{text}</span>'


def match_card(m, idx=None, focus=None):
    is_done = m.get("status") == "종료"
    wl = m.get("win_lose") or {}
    hcp = m.get("handicap")
    uo = m.get("under_over")
    w5 = m.get("w5")

    if not is_done:
        home_cls = "side" + (" focus" if focus == m["home"] else "")
        away_cls = "side" + (" focus" if focus == m["away"] else "")
        badges = [badge("🕒 발매중", "w5-mid")]
        if wl.get("home_odds") is not None:
            badges.append(badge(f"승 {odds_txt(wl.get('home_odds'))} · 패 {odds_txt(wl.get('away_odds'))}", "fav"))
        if hcp and hcp.get("standard") is not None:
            std = hcp["standard"]
            sign = "+" if std > 0 else ""
            badges.append(badge(f"H {sign}{std} ({odds_txt(hcp.get('home_odds'))}/{odds_txt(hcp.get('away_odds'))})", "ma"))
        if uo and uo.get("standard") is not None:
            badges.append(badge(f"U/O {uo['standard']} ({odds_txt(uo.get('under_odds'))}/{odds_txt(uo.get('over_odds'))})", "under"))
        if w5 and w5.get("win_odds") is not None:
            badges.append(badge(f"승5패 {odds_txt(w5.get('win_odds'))}/{odds_txt(w5.get('draw5_odds'))}/{odds_txt(w5.get('lose_odds'))}", "w5-mid"))
        return f"""
      <article class="mcard">
        <div class="mcard-top">
          <span class="mno">예정</span>
          <span class="mdate">{m['date'][5:10]} {m['date'][11:]} · {m['round'].replace('프로토 승부식 ', '')}</span>
          <span class="mseq">#{m['seq']}</span>
        </div>
        <div class="mcard-main">
          <div class="{home_cls}">
            <span class="tname" style="color:{color(m['home'])}">{short(m['home'])}</span>
            <span class="tscore">-</span>
          </div>
          <span class="vs">vs</span>
          <div class="{away_cls}">
            <span class="tscore">-</span>
            <span class="tname" style="color:{color(m['away'])}">{short(m['away'])}</span>
          </div>
        </div>
        <div class="mcard-badges">{''.join(badges)}</div>
      </article>"""

    res_home = wl["winner"] == "HOME"
    ht = wl["hit_type"] or ""
    hs, as_ = m["home_score"], m["away_score"]

    home_cls = "side win" if res_home else "side"
    away_cls = "side" if res_home else "side win"
    if focus == m["home"]:
        home_cls += " focus"
    if focus == m["away"]:
        away_cls += " focus"

    badges = []
    badges.append(badge(f"{'홈승' if res_home else '원정승'}", "win"))
    if ht == "정배":
        badges.append(badge(f"🎯 정배 {odds_txt(m['win_lose']['hit_odds'])}", "fav"))
    elif ht == "역배":
        badges.append(badge(f"⚡ 역배 {odds_txt(m['win_lose']['hit_odds'])}", "dog"))
    if hcp:
        std = hcp["standard"]
        sign = "+" if std > 0 else ""
        cls = "ma" if hcp["result"] == "마핸" else "pl"
        badges.append(badge(f"{hcp['result']} {sign}{std}", cls))
    if uo and uo["standard"] is not None:
        cls = "over" if uo["result"] == "OVER" else "under"
        badges.append(badge(f"{'오버' if uo['result']=='OVER' else '언더'} {uo['standard']}", cls))
    if w5:
        cls = {"승": "w5-win", "5": "w5-mid", "패": "w5-lose"}[w5["result"]]
        badges.append(badge(f"승5패 {w5['result']}", cls))

    no = f'<span class="mno">{idx}</span>' if idx else ""
    return f"""
      <article class="mcard">
        <div class="mcard-top">
          {no}
          <span class="mdate">{m['date'][5:10]} {m['date'][11:]} · {m['round'].replace('프로토 승부식 ', '')}</span>
          <span class="mseq">#{m['seq']}</span>
        </div>
        <div class="mcard-main">
          <div class="{home_cls}">
            <span class="tname" style="color:{color(m['home'])}">{short(m['home'])}</span>
            <span class="tscore">{hs}</span>
          </div>
          <span class="vs">:</span>
          <div class="{away_cls}">
            <span class="tscore">{as_}</span>
            <span class="tname" style="color:{color(m['away'])}">{short(m['away'])}</span>
          </div>
        </div>
        <div class="mcard-badges">{''.join(badges)}</div>
      </article>"""


def ohlc_row(m, idx):
    """전체 뷰 누계 표 한 줄"""
    wl = m.get("win_lose") or {}
    hcp = m.get("handicap")
    uo = m.get("under_over")
    if m.get("status") != "종료":
        hc = "-"
        if hcp and hcp.get("standard") is not None:
            std = hcp["standard"]
            hc = f"H{'' if std < 0 else '+'}{std}"
        uo_t = f"{uo['standard']}" if uo and uo.get("standard") is not None else "-"
        odds_s = f"{odds_txt(wl.get('home_odds'))}/{odds_txt(wl.get('away_odds'))}"
        return f"""
        <tr>
          <td class="c-idx">예정</td>
          <td class="c-date">{m['date'][5:10]}</td>
          <td class="c-team"><b style="color:{color(m['home'])}">{short(m['home'])}</b> <span class="vsx">vs</span> <b style="color:{color(m['away'])}">{short(m['away'])}</b></td>
          <td class="c-score">-<span class="vsx">:</span>-</td>
          <td class="c-res">예정</td>
          <td class="c-fav"><span class="mini">{odds_s}</span></td>
          <td class="c-hc">{hc}</td>
          <td class="c-uo">{uo_t}</td>
        </tr>"""
    ht = wl["hit_type"] or ""
    res = "홈" if wl["winner"] == "HOME" else "원정"
    hc = "-"
    if hcp:
        std = hcp["standard"]
        hc = f"{hcp['result']}{'' if std < 0 else '+'}{std}"
    uo_t = "-"
    if uo and uo["standard"] is not None:
        uo_t = f"{'O' if uo['result']=='OVER' else 'U'}{uo['standard']}"
    return f"""
        <tr>
          <td class="c-idx">{idx}</td>
          <td class="c-date">{m['date'][5:10]}</td>
          <td class="c-team"><b style="color:{color(m['home'])}">{short(m['home'])}</b> <span class="vsx">vs</span> <b style="color:{color(m['away'])}">{short(m['away'])}</b></td>
          <td class="c-score">{m['home_score']}<span class="vsx">:</span>{m['away_score']}</td>
          <td class="c-res">{res}</td>
          <td class="c-fav">{'🎯' if ht=='정배' else '⚡'}<span class="mini">{ht}</span></td>
          <td class="c-hc">{hc}</td>
          <td class="c-uo">{uo_t}</td>
        </tr>"""


# ---------------------------------------------------------------- 통계

def global_stats(matches):
    matches = [m for m in matches if m.get("status") == "종료"]
    n = len(matches)
    fav = sum(1 for m in matches if m["win_lose"]["hit_type"] == "정배")
    over = sum(1 for m in matches if m["under_over"] and m["under_over"]["result"] == "OVER")
    ma = sum(1 for m in matches if m["handicap"] and m["handicap"]["result"] == "마핸")
    pts = [m["total_points"] for m in matches]
    fav_seq, fav_n = streaks([m["win_lose"]["hit_type"] == "정배" for m in matches])
    uo_seq, uo_n = streaks([m["under_over"]["result"] == "OVER" if m["under_over"] else False for m in matches])
    return {
        "n": n,
        "fav_rate": pct(fav, n),
        "over_rate": pct(over, n),
        "ma_rate": pct(ma, n),
        "avg_total": round(sum(pts) / n, 1) if n else 0,
        "fav_streak": ("정배" if fav_seq else "역배", fav_n),
        "uo_streak": ("오버" if uo_seq else "언더", uo_n),
    }


def team_stats(matches, team):
    tms = [m for m in team_matches(matches, team) if m.get("status") == "종료"]
    n = len(tms)
    w = sum(1 for m in tms if won(m, team))
    fav_flags = [m["win_lose"]["hit_type"] == "정배" for m in tms]
    fav_hits = sum(fav_flags)
    # 그 구단이 뛴 경기에서 정배가 이긴 비율 = 정배 적중률
    when_fav = [m for m in tms if (m["win_lose"]["favorite"] == ("HOME" if m["home"] == team else "AWAY"))]
    when_dog = [m for m in tms if m not in when_fav]
    wf = sum(1 for m in when_fav if won(m, team))
    wd = sum(1 for m in when_dog if won(m, team))
    hc = [m["handicap"] for m in tms if m["handicap"]]
    ma = sum(1 for h in hc if h["result"] == "마핸")
    uo = [m["under_over"] for m in tms if m["under_over"] and m["under_over"]["standard"] is not None]
    ov = sum(1 for u in uo if u["result"] == "OVER")
    fav_seq, fav_n = streaks(fav_flags)
    ma_seq, ma_n = streaks([h["result"] == "마핸" for h in hc])
    uo_seq, uo_n = streaks([u["result"] == "OVER" for u in uo])
    wl_seq, wl_n = streaks([won(m, team) for m in tms])
    last5 = tms[-5:]
    pts_for = sum(m["home_score"] if m["home"] == team else m["away_score"] for m in tms)
    pts_ag = sum(m["away_score"] if m["home"] == team else m["home_score"] for m in tms)
    return {
        "n": n, "w": w, "l": n - w, "win_rate": pct(w, n),
        "avg_for": round(pts_for / n, 1) if n else 0,
        "avg_ag": round(pts_ag / n, 1) if n else 0,
        "fav_hits": fav_hits, "fav_rate": pct(fav_hits, n),
        "fav_streak": ("정배" if fav_seq else "역배", fav_n),
        "when_fav": (wf, len(when_fav)), "when_dog": (wd, len(when_dog)),
        "ma_rate": pct(ma, len(hc)), "ma_streak": ("마핸" if ma_seq else "플핸", ma_n),
        "over_rate": pct(ov, len(uo)), "uo_streak": ("오버" if uo_seq else "언더", uo_n),
        "wl_streak": ("연승" if wl_seq else "연패", wl_n),
        "last5": last5,
        "fav_list": fav_flags,
    }


def team_panel(matches, teams, prefix):
    labels = []
    for i, t in enumerate(teams):
        st = team_stats(matches, t)
        labels.append(f"""
          <label class="tbtn" for="t-{prefix}-{i}" style="--tc:{color(t)}">
            <span class="tbtn-name">{short(t)}</span>
            <span class="tbtn-rec">{st['w']}승 {st['l']}패</span>
          </label>""")
    return f"""
      <div class="tpanel">
        <div class="tpanel-head">구단을 터치하면 누적 지표가 열립니다 <b>{len(teams)}개 구단</b></div>
        <div class="tgrid">{''.join(labels)}</div>
      </div>"""


def last5_dots(tms, team):
    out = []
    for m in tms:
        win = won(m, team)
        cls = "dot-win" if win else "dot-lose"
        opp = m["away"] if m["home"] == team else m["home"]
        out.append(f'<span class="dot {cls}" title="{short(opp)}">{short(opp)}</span>')
    return ''.join(out)


def stat_box(label, value, sub, cls):
    return f"""
        <div class="sbox {cls}">
          <span class="sbox-l">{label}</span>
          <span class="sbox-v">{value}</span>
          <span class="sbox-s">{sub}</span>
        </div>"""


def team_view(matches, team, idx, prefix, all_count):
    st = team_stats(matches, team)
    tms = team_matches(matches, team)
    done_n = sum(1 for m in tms if m.get("status") == "종료")
    rows = []
    done_idx = done_n
    for m in reversed(tms):
        if m.get("status") == "종료":
            rows.append(match_card(m, done_idx, focus=team))
            done_idx -= 1
        else:
            rows.append(match_card(m, None, focus=team))
    fav_lbl = f"{st['fav_streak'][1]}연속 {st['fav_streak'][0]}"
    ma_lbl = f"{st['ma_streak'][1]}연속 {st['ma_streak'][0]}"
    uo_lbl = f"{st['uo_streak'][1]}연속 {st['uo_streak'][0]}"
    wl_lbl = f"{st['wl_streak'][1]}연속 {st['wl_streak'][0]}"
    return f"""
      <section class="view team-view" id="tv-{prefix}-{idx}">
        <div class="team-head">
          <div class="team-head-l">
            <span class="team-bar" style="background:{color(team)}"></span>
            <div>
              <div class="team-title">{full(team)}</div>
              <div class="team-sub">{'KBL' if prefix=='m' else 'WKBL'} · 최근 {st['n']}경기 누적</div>
            </div>
          </div>
          <div class="team-rec">
            <b>{st['w']}</b>승 <b>{st['l']}</b>패
            <span>{st['win_rate']}%</span>
          </div>
        </div>
        <div class="streak-strip">
          <span class="strip-item">{wl_lbl}</span>
          <span class="strip-item {'s-fav' if st['fav_streak'][0]=='정배' else 's-dog'}">{fav_lbl}</span>
          <span class="strip-item {'s-ma' if st['ma_streak'][0]=='마핸' else 's-pl'}">{ma_lbl}</span>
          <span class="strip-item {'s-over' if st['uo_streak'][0]=='오버' else 's-under'}">{uo_lbl}</span>
        </div>
        <div class="sgrid">
          {stat_box('정배 적중률', f"{st['fav_rate']}%", f"정배 {st['fav_hits']}/{st['n']}", 'c-fav')}
          {stat_box('정배시 전적', f"{st['when_fav'][0]}승 {st['when_fav'][1]-st['when_fav'][0]}패", '마감 배당 낮은 팀', 'c-fav2')}
          {stat_box('역배시 전적', f"{st['when_dog'][0]}승 {st['when_dog'][1]-st['when_dog'][0]}패", '마감 배당 높은 팀', 'c-dog')}
          {stat_box('마핸 달성률', f"{st['ma_rate']}%", '핸디캡 적중', 'c-ma')}
          {stat_box('오버 비율', f"{st['over_rate']}%", '총득점 기준', 'c-over')}
          {stat_box('평균 득실', f"{st['avg_for']}", f"실점 {st['avg_ag']}", 'c-avg')}
        </div>
        <div class="last5">{last5_dots(st['last5'], team)}</div>
        <div class="list-head">경기별 누적 <span>{st['n']}경기</span></div>
        <div class="scroll">
          {''.join(rows)}
        </div>
      </section>"""


def overall_view(matches, prefix, title, sub):
    st = global_stats(matches)
    done_idx = sum(1 for m in matches if m.get("status") == "종료")
    row_list = []
    for m in reversed(matches):
        if m.get("status") == "종료":
            row_list.append(ohlc_row(m, done_idx))
            done_idx -= 1
        else:
            row_list.append(ohlc_row(m, None))
    rows = ''.join(row_list)
    fav_streak = f"{st['fav_streak'][1]}연속 {st['fav_streak'][0]}"
    uo_streak = f"{st['uo_streak'][1]}연속 {st['uo_streak'][0]}"
    return f"""
      <section class="view all-view" id="v-{prefix}-all">
        <div class="sgrid">
          {stat_box('누적 경기', f"{st['n']}", title, 'c-n')}
          {stat_box('정배 적중률', f"{st['fav_rate']}%", '마감 배당 낮은 팀 승', 'c-fav')}
          {stat_box('마핸 달성률', f"{st['ma_rate']}%", '핸디캡 적중', 'c-ma')}
          {stat_box('오버 비율', f"{st['over_rate']}%", '총득점 기준', 'c-over')}
          {stat_box('평균 총득점', f"{st['avg_total']}", '양팀 합계', 'c-avg')}
          {stat_box('연속 흐름', fav_streak, uo_streak, 'c-flow')}
        </div>
        <div class="tbl-wrap">
          <div class="tbl-head"><span>최신 경기 위 · 개막전(#1) 아래</span><span>{sub}</span></div>
          <div class="scroll">
            <table class="tbl">
              <thead>
                <tr><th>#</th><th>날짜</th><th>대진</th><th>스코어</th><th>승</th><th>정배</th><th>핸디</th><th>U/O</th></tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
        </div>
      </section>"""


def build():
    mens = data["mens"]
    womens = data["womens"]
    m_teams = teams_of(mens)
    w_teams = teams_of(womens)

    radios = ['<input type="radio" name="lg" id="lg-m" checked><input type="radio" name="lg" id="lg-w">']
    radios.append('<input type="radio" name="view-m" id="vm-all" checked><input type="radio" name="view-m" id="vm-team">')
    radios.append('<input type="radio" name="view-w" id="vw-all" checked><input type="radio" name="view-w" id="vw-team">')
    for i in range(len(m_teams)):
        radios.append(f'<input type="radio" name="team-m" id="t-m-{i}"{" checked" if i == 0 else ""}>')
    for i in range(len(w_teams)):
        radios.append(f'<input type="radio" name="team-w" id="t-w-{i}"{" checked" if i == 0 else ""}>')

    css_dyn = []
    for i in range(len(m_teams)):
        css_dyn.append(f"#t-m-{i}:checked ~ .s-m #tv-m-{i}{{display:flex}}")
        css_dyn.append(f"#t-m-{i}:checked ~ .s-m label[for='t-m-{i}']{{background:var(--bg-card-hover);border-color:{color(m_teams[i])}}}")
    for i in range(len(w_teams)):
        css_dyn.append(f"#t-w-{i}:checked ~ .s-w #tv-w-{i}{{display:flex}}")
        css_dyn.append(f"#t-w-{i}:checked ~ .s-w label[for='t-w-{i}']{{background:var(--bg-card-hover);border-color:{color(w_teams[i])}}}")

    m_team_views = ''.join(team_view(mens, t, i, "m", len(mens)) for i, t in enumerate(m_teams))
    w_team_views = ''.join(team_view(womens, t, i, "w", len(womens)) for i, t in enumerate(w_teams))

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#070a10">
<title>KBL·WKBL 배트맨토토 누적 대시보드</title>
<style>
  :root {{
    --bg-main:#070a10; --bg-card:#121927; --bg-card-hover:#192336; --border-color:#1e2c40;
    --text-white:#f8fafc; --text-muted:#94a3b8; --text-sub:#64748b;
    --primary:#38bdf8; --primary-dark:#0284c7; --primary-light:rgba(56,189,248,.15);
    --success:#34d399; --success-bg:rgba(52,211,153,.15);
    --warning:#fbbf24; --warning-bg:rgba(251,191,36,.15);
    --danger:#f87171; --danger-bg:rgba(248,113,113,.15);
    --purple:#c084fc; --purple-bg:rgba(192,132,252,.15);
  }}
  * {{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
  html, body {{ margin:0; padding:0; height:100%; overflow:hidden; }}
  body {{
    background:radial-gradient(1200px 600px at 50% -10%, #0d1626 0%, var(--bg-main) 60%);
    color:var(--text-white);
    font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Pretendard','Malgun Gothic',sans-serif;
    letter-spacing:-.02em;
  }}
  .app {{ height:100dvh; display:flex; flex-direction:column; max-width:720px; margin:0 auto; padding:calc(env(safe-area-inset-top) + 8px) 10px calc(env(safe-area-inset-bottom) + 8px); }}
  input[type=radio] {{ position:absolute; width:1px; height:1px; opacity:0; pointer-events:none; }}

  header.top {{ flex:0 0 auto; padding:2px 2px 8px; }}
  .title-row {{ display:flex; align-items:center; gap:8px; }}
  .ball {{ font-size:19px; filter:drop-shadow(0 0 8px rgba(56,189,248,.5)); }}
  h1 {{ margin:0; font-size:17px; font-weight:800; letter-spacing:-.03em; }}
  h1 span {{ color:var(--primary); }}
  .meta {{ display:flex; gap:8px; margin-top:3px; font-size:10px; color:var(--text-sub); }}
  .meta b {{ color:var(--text-muted); font-weight:600; }}

  .tabs {{ display:flex; gap:6px; flex:0 0 auto; margin-bottom:6px; }}
  .tab {{ flex:1; text-align:center; padding:9px 6px; border-radius:11px; border:1px solid var(--border-color);
         background:var(--bg-card); color:var(--text-muted); font-size:12.5px; font-weight:700; transition:.15s; }}
  .tab small {{ display:block; font-size:9px; font-weight:600; color:var(--text-sub); margin-top:1px; }}
  #lg-m:checked ~ .tabs label[for=lg-m],
  #lg-w:checked ~ .tabs label[for=lg-w] {{ background:linear-gradient(180deg, rgba(56,189,248,.22), rgba(56,189,248,.06)); border-color:var(--primary); color:#e0f2fe; }}

  .sub-tabs {{ display:flex; gap:6px; flex:0 0 auto; margin-bottom:6px; }}
  .sub-tab {{ flex:1; text-align:center; padding:7px 6px; border-radius:9px; border:1px solid var(--border-color);
             background:rgba(18,25,39,.7); color:var(--text-sub); font-size:11.5px; font-weight:700; }}
  #vm-all:checked ~ .s-m .sub-tabs label[for=vm-all],
  #vm-team:checked ~ .s-m .sub-tabs label[for=vm-team],
  #vw-all:checked ~ .s-w .sub-tabs label[for=vw-all],
  #vw-team:checked ~ .s-w .sub-tabs label[for=vw-team] {{ background:var(--primary-light); border-color:rgba(56,189,248,.6); color:var(--text-white); }}

  .s-m, .s-w {{ display:none; flex:1 1 auto; min-height:0; flex-direction:column; }}
  #lg-m:checked ~ .s-m, #lg-w:checked ~ .s-w {{ display:flex; }}

  .view {{ display:none; flex:1 1 auto; min-height:0; flex-direction:column; gap:6px; }}
  #vm-all:checked ~ .s-m #v-m-all,
  #vw-all:checked ~ .s-w #v-w-all {{ display:flex; }}
  #vm-all:checked ~ .s-m .team-area, #vw-all:checked ~ .s-w .team-area {{ display:none; }}
  .team-area {{ display:none; flex:1 1 auto; min-height:0; flex-direction:column; gap:5px; }}
  #vm-team:checked ~ .s-m .team-area,
  #vw-team:checked ~ .s-w .team-area {{ display:flex; }}

  /* 전체 뷰 */
  .sgrid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:6px; flex:0 0 auto; }}
  .sbox {{ background:var(--bg-card); border:1px solid var(--border-color); border-radius:11px; padding:8px 8px 7px; display:flex; flex-direction:column; gap:1px; }}
  .sbox-l {{ font-size:9.5px; color:var(--text-sub); font-weight:700; }}
  .sbox-v {{ font-size:15px; font-weight:800; letter-spacing:-.03em; }}
  .sbox-s {{ font-size:9px; color:var(--text-sub); }}
  .c-fav .sbox-v, .c-fav2 .sbox-v {{ color:var(--success); }}
  .c-dog .sbox-v {{ color:var(--danger); }}
  .c-ma .sbox-v {{ color:var(--purple); }}
  .c-over .sbox-v {{ color:var(--warning); }}
  .c-n .sbox-v, .c-avg .sbox-v, .c-flow .sbox-v {{ color:var(--primary); }}
  .c-flow .sbox-v {{ font-size:13px; }}

  .tbl-wrap {{ flex:1 1 auto; min-height:0; display:flex; flex-direction:column; background:var(--bg-card);
              border:1px solid var(--border-color); border-radius:12px; overflow:hidden; }}
  .tbl-head {{ display:flex; justify-content:space-between; align-items:center; padding:7px 10px; font-size:10px;
               color:var(--text-muted); border-bottom:1px solid var(--border-color); background:rgba(13,22,38,.6); }}
  .tbl-head span:first-child {{ font-weight:800; color:var(--text-white); font-size:10.5px; }}
  .scroll {{ flex:1 1 auto; min-height:0; overflow-y:auto; -webkit-overflow-scrolling:touch; }}
  table.tbl {{ width:100%; border-collapse:collapse; font-size:11px; }}
  table.tbl thead th {{ position:sticky; top:0; z-index:2; background:#0f1724; color:var(--text-sub); font-size:9px;
                        font-weight:700; padding:5px 3px; text-align:center; border-bottom:1px solid var(--border-color); }}
  table.tbl td {{ padding:6px 3px; text-align:center; border-bottom:1px solid rgba(30,44,64,.55); }}
  table.tbl tr:nth-child(odd) td {{ background:rgba(25,35,54,.35); }}
  .c-idx {{ color:var(--text-sub); font-size:9.5px; width:24px; }}
  .c-date {{ color:var(--text-muted); font-size:9.5px; white-space:nowrap; }}
  .c-team {{ text-align:left !important; font-size:10.5px; white-space:nowrap; }}
  .c-team b {{ font-weight:800; }}
  .vsx {{ color:var(--text-sub); font-size:8.5px; margin:0 1px; }}
  .c-score {{ font-weight:800; font-size:11px; }}
  .c-res {{ font-size:10px; color:var(--text-muted); }}
  .c-fav {{ font-size:10px; white-space:nowrap; }}
  .c-fav .mini {{ font-size:9.5px; font-weight:700; }}
  .c-hc {{ font-size:9.5px; color:var(--purple); white-space:nowrap; }}
  .c-uo {{ font-size:9.5px; color:var(--warning); white-space:nowrap; }}

  /* 구단 패널 */
  .tpanel-head {{ font-size:10px; color:var(--text-sub); margin:2px 2px 6px; }}
  .tpanel-head b {{ color:var(--text-muted); }}
  .tgrid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:5px; }}
  .tbtn {{ background:var(--bg-card); border:1px solid var(--border-color); border-radius:9px; padding:6px 2px;
           text-align:center; box-shadow:inset 0 -2px 0 0 var(--tc); }}
  .tbtn-name {{ display:block; font-size:10px; font-weight:800; color:var(--text-white); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .tbtn-rec {{ display:block; font-size:8.5px; color:var(--text-sub); margin-top:1px; }}

  .team-view {{ gap:5px; }}
  .team-head {{ display:flex; align-items:center; justify-content:space-between; background:var(--bg-card);
               border:1px solid var(--border-color); border-radius:12px; padding:9px 10px; flex:0 0 auto; }}
  .team-head-l {{ display:flex; align-items:center; gap:8px; min-width:0; }}
  .team-bar {{ width:4px; height:30px; border-radius:3px; flex:0 0 auto; }}
  .team-title {{ font-size:13.5px; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .team-sub {{ font-size:9px; color:var(--text-sub); }}
  .team-rec {{ font-size:10.5px; color:var(--text-muted); white-space:nowrap; }}
  .team-rec b {{ font-size:14px; color:var(--text-white); }}
  .team-rec span {{ display:block; text-align:right; font-size:9px; color:var(--primary); font-weight:700; }}

  .streak-strip {{ display:flex; gap:4px; flex:0 0 auto; }}
  .strip-item {{ flex:1; text-align:center; font-size:9.5px; font-weight:800; padding:5px 2px; border-radius:8px;
                background:rgba(18,25,39,.9); border:1px solid var(--border-color); color:var(--text-muted); white-space:nowrap; }}
  .s-fav {{ color:var(--success); border-color:rgba(52,211,153,.5); background:var(--success-bg); }}
  .s-dog {{ color:var(--danger); border-color:rgba(248,113,113,.5); background:var(--danger-bg); }}
  .s-ma {{ color:var(--purple); border-color:rgba(192,132,252,.5); background:var(--purple-bg); }}
  .s-pl {{ color:#f0abfc; border-color:rgba(240,171,252,.4); background:rgba(240,171,252,.12); }}
  .s-over {{ color:var(--warning); border-color:rgba(251,191,36,.5); background:var(--warning-bg); }}
  .s-under {{ color:#93c5fd; border-color:rgba(147,197,253,.45); background:rgba(147,197,253,.12); }}

  .c-last {{ justify-content:center; }}
  .last5 {{ display:flex; gap:4px; flex:0 0 auto; padding:0 2px; }}
  .dot {{ flex:1; text-align:center; font-size:9px; font-weight:700; padding:4px 2px; border-radius:7px; white-space:nowrap; overflow:hidden; }}
  .dot-win {{ background:var(--success-bg); color:var(--success); border:1px solid rgba(52,211,153,.35); }}
  .dot-lose {{ background:var(--danger-bg); color:var(--danger); border:1px solid rgba(248,113,113,.3); }}

  .list-head {{ font-size:10px; color:var(--text-sub); padding:1px 3px; flex:0 0 auto; }}
  .list-head span {{ color:var(--text-muted); }}

  /* 경기 카드 */
  .mcard {{ background:var(--bg-card); border:1px solid var(--border-color); border-radius:11px; padding:8px 10px; margin-bottom:6px; }}
  .mcard-top {{ display:flex; align-items:center; gap:6px; font-size:9px; color:var(--text-sub); margin-bottom:4px; }}
  .mno {{ background:var(--primary-light); color:var(--primary); font-weight:800; border-radius:6px; padding:1px 6px; font-size:9px; }}
  .mdate {{ color:var(--text-muted); }}
  .mseq {{ margin-left:auto; font-size:8.5px; color:#334155; }}
  .mcard-main {{ display:flex; align-items:center; justify-content:center; gap:8px; padding:2px 0 4px; }}
  .side {{ display:flex; align-items:center; gap:6px; flex:1; justify-content:flex-end; opacity:.72; }}
  .side.win {{ opacity:1; }}
  .side.focus {{ filter:drop-shadow(0 0 6px rgba(56,189,248,.35)); }}
  .side:last-child {{ justify-content:flex-start; }}
  .tname {{ font-size:13px; font-weight:800; }}
  .tscore {{ font-size:17px; font-weight:900; letter-spacing:-.04em; }}
  .side.win .tscore {{ color:var(--text-white); }}
  .side:not(.win) .tscore {{ color:var(--text-sub); }}
  .vs {{ color:var(--text-sub); font-size:11px; }}
  .mcard-badges {{ display:flex; flex-wrap:wrap; gap:4px; }}
  .bdg {{ font-size:9px; font-weight:700; padding:2px 6px; border-radius:6px; white-space:nowrap; }}
  .bdg-win {{ background:var(--primary-light); color:var(--primary); }}
  .bdg-fav {{ background:var(--success-bg); color:var(--success); }}
  .bdg-dog {{ background:var(--danger-bg); color:var(--danger); }}
  .bdg-ma {{ background:var(--purple-bg); color:var(--purple); }}
  .bdg-pl {{ background:rgba(240,171,252,.13); color:#f0abfc; }}
  .bdg-over {{ background:var(--warning-bg); color:var(--warning); }}
  .bdg-under {{ background:rgba(147,197,253,.13); color:#93c5fd; }}
  .bdg-w5-win {{ background:rgba(52,211,153,.1); color:#6ee7b7; }}
  .bdg-w5-mid {{ background:rgba(148,163,184,.14); color:#cbd5e1; }}
  .bdg-w5-lose {{ background:rgba(248,113,113,.1); color:#fca5a5; }}

  footer {{ flex:0 0 auto; padding:6px 3px 0; font-size:8.5px; color:#334155; line-height:1.35; }}
  footer b {{ color:var(--text-sub); }}

  {''.join(css_dyn)}
</style>
</head>
<body>
<div class="app">
  {''.join(radios)}

  <header class="top">
    <div class="title-row"><span class="ball">🏀</span><h1>KBL·WKBL <span>배트맨토토</span> 누적</h1></div>
    <div class="meta">
      <span>개막 <b>KBL 10.03</b> · <b>WKBL 11.01</b></span>
      <span>·</span>
      <span>경기 <b>{len(mens)+len(womens)}</b>건</span>
      <span>·</span>
      <span>갱신 <b>{data['last_updated'][5:]}</b></span>
    </div>
  </header>

  <div class="tabs">
    <label class="tab" for="lg-m">남자부 KBL<small>10개 구단 · {len(mens)}경기</small></label>
    <label class="tab" for="lg-w">여자부 WKBL<small>6개 구단 · {len(womens)}경기</small></label>
  </div>

  <div class="s-m">
    <div class="sub-tabs">
      <label class="sub-tab" for="vm-all">전체</label>
      <label class="sub-tab" for="vm-team">구단별</label>
    </div>
    {overall_view(mens, "m", "KBL", "마감 배당 기준")}
    <div class="team-area">
    {team_panel(mens, m_teams, "m")}
    {m_team_views}
    </div>
  </div>

  <div class="s-w">
    <div class="sub-tabs">
      <label class="sub-tab" for="vw-all">전체</label>
      <label class="sub-tab" for="vw-team">구단별</label>
    </div>
    {overall_view(womens, "w", "WKBL", "마감 배당 기준")}
    <div class="team-area">
    {team_panel(womens, w_teams, "w")}
    {w_team_views}
    </div>
  </div>

  <footer>
    출처 <b>m.betman.co.kr 프로토 승부식 적중결과</b>의 확정 수치만 사용했습니다. 핸디캡은 홈 기준 마감 기준점이며,
    '-' 기준점 팀이 넘기면 <b>마핸</b>, '+' 기준점 팀이 지켜내면 <b>플핸</b>입니다. 정배는 마감 배당이 낮은 팀 적중입니다.
  </footer>
</div>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {OUTPUT_HTML} ({len(html):,} bytes)")
    print(f"  KBL {len(mens)}경기 · 구단 {len(m_teams)} · WKBL {len(womens)}경기 · 구단 {len(w_teams)}")


if __name__ == "__main__":
    build()
