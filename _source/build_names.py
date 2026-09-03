# -*- coding: utf-8 -*-
"""locale 에서 한영 전수 조회표를 생성한다 → basics/names.html

    python _source/build_names.py            건조 실행 (크기만 확인)
    python _source/build_names.py --apply    파일 생성

한영 명칭(glossary.html) 은 해설이 붙은 '읽는 표'로 두고,
이 문서는 이름만 담은 '찾는 표'로 나눈다.
"""
import io, os, re, sys, html

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SITE)
KR = os.path.join(ROOT, 'KR')
EN = r'C:\Program Files (x86)\Steam\steamapps\common\Chronicon\locale\EN'

# (표 제목, 파일, 키 정규식, 설명)
# (표 제목, 앵커, 파일, 키 정규식, 설명)
CATS = [
    ('스킬', 'skill', 'skills', r'^skill_(\d+)_name$', '전 클래스 액티브·패시브'),
    ('스킬 트리', 'tree', 'skills', r'^skill_tree_(\d+)_(\d+)$', '5개 클래스 × 4트리 + 마스터리'),
    ('마스터리', 'mastery', 'mastery', r'^mastery_(\d+)_name$', '클래스 트리와 공용 줄'),
    ('아이템', 'item', 'items', r'^item_(\d+)_name$', '장비 · 재료 · 소모품'),
    ('아이템 파워', 'power', 'enchants', r'^enchant_(\d+)_name$', '툴팁 빨간 글씨. 룬 이름이 여기서 나온다'),
    ('버프 · 상태', 'buff', 'buffs', r'^buff_(\d+)_name$', '화면에 뜨는 버프·디버프'),
    ('몬스터', 'monster', 'monsters', r'^monster_(\d+)_name$', ''),
    ('유니크 적', 'unique', 'monsters', r'^unique_(\d+)_name$', '구역별 고유 적'),
    ('적 접두', 'affix', 'monsters', r'^affix_(\d+)$', '정예·챔피언에 붙는 것'),
    ('지역', 'area', 'world', r'^area_(\d+)_name$', ''),
]


def load(p):
    d = {}
    for ln in io.open(p, encoding='utf-8-sig', errors='replace'):
        ln = ln.rstrip('\r\n')
        if '=' in ln and not ln.startswith('['):
            k, _, v = ln.partition('=')
            d[k] = v.strip('"')
    return d


def esc(s):
    return html.escape(s, quote=False)


def main():
    secs, counts = [], []
    for title, anchor, fn, pat, note in CATS:
        pe, pk = os.path.join(EN, fn), os.path.join(KR, fn)
        if not os.path.exists(pe) or not os.path.exists(pk):
            continue
        e, k = load(pe), load(pk)
        rx = re.compile(pat)
        rows = []
        seen = set()
        for key in e:
            if not rx.match(key) or key not in k:
                continue
            ev, kv = e[key].strip(), k[key].strip()
            if not ev or not kv or (ev, kv) in seen:
                continue
            seen.add((ev, kv))
            rows.append((ev, kv))
        rows.sort(key=lambda r: r[0].lower())
        counts.append((title, anchor, len(rows)))
        body = '\n'.join(
            '    <tr><td><span class="mono">%s</span></td><td>%s</td></tr>'
            % (esc(a), esc(b)) for a, b in rows)
        secs.append(
            '<section id="n-%s">\n  <h2>%s <span class="cnt-badge">%d</span></h2>\n'
            '%s  <div class="tw"><table>\n'
            '    <tr><th>영문</th><th>한글패치</th></tr>\n%s\n  </table></div>\n</section>\n'
            % (anchor, title, len(rows),
               ('  <p>%s</p>\n' % note if note else ''), body))

    toc = ' · '.join('<a href="#n-%s">%s</a>' % (a, t) for t, a, _ in counts)
    total = sum(c for _, _, c in counts)

    head = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
<meta name="googlebot" content="noindex, nofollow">
<title>이름 찾기 · 크로니콘 위키</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="../assets/wiki.css">
</head>
<body>
<div class="wrap">

<div class="topbar">
  <a class="brand plain" href="../index.html">크로니콘 <span>위키</span></a>
  <span class="crumb">자료 › 이름 찾기</span>
</div>

<nav class="side"></nav>

<h1>이름 찾기</h1>
<p class="lede">게임 파일에서 뽑은 <strong>한영 전수 대조표 %s개</strong>. 영어 가이드에 나온 이름을 여기서 찾으세요.</p>

<div class="searchbar">
  <input type="search" id="q" placeholder="영문이든 한글이든 입력하세요" autocomplete="off" spellcheck="false" aria-label="문서 내 검색">
  <span class="cnt" id="cnt"></span>
</div>
<p id="none">검색 결과가 없습니다.</p>

<section id="how">
  <h2>이 문서를 쓰는 법</h2>
  <div class="note ok">
    <strong>위 검색창에 넣으면 이 문서 전체에서 찾습니다.</strong> 영문·한글 양방향으로 됩니다.
  </div>
  <p>%s</p>
  <div class="note">
    <strong>해설이 필요하면 <a href="glossary.html">한영 명칭</a>으로 가세요.</strong>
    그쪽은 골라 뽑은 표에 설명과 주의사항이 붙어 있습니다. 이 문서는 <strong>이름만</strong> 담은 조회표입니다.
  </div>
  <p class="src">Chronicon 1.54.1 의 <span class="mono">locale/EN</span> 과 한글패치 <span class="mono">KR/</span> 을 대조해 자동 생성했습니다.
     <span class="mono">_source/build_names.py</span> 로 다시 만들 수 있습니다 <span class="tag data">데이터</span></p>
</section>

''' % ('{:,}'.format(total), toc)

    tail = '''<section id="related">
  <h2>관련 문서</h2>
  <ul>
    <li><a href="glossary.html">한영 명칭</a> — 설명이 붙은 선별표</li>
    <li><a href="../meta/patches.html">패치 동향</a> — 낡은 명칭 판별</li>
  </ul>
</section>

</div>
<a href="#" class="totop">↑ 맨 위</a>
<script src="../assets/wiki.js"></script>
</body>
</html>
'''
    doc = head + '\n'.join(secs) + '\n' + tail
    print('분류별 항목 수')
    for t, _, c in counts:
        print('  %-12s %5d' % (t, c))
    print('  %-12s %5d' % ('합계', total))
    print('\n문서 크기 %.0f KB' % (len(doc.encode('utf-8')) / 1024))
    if '--apply' in sys.argv:
        p = os.path.join(SITE, 'basics', 'names.html')
        io.open(p, 'w', encoding='utf-8', newline='\n').write(doc)
        print('생성: %s' % p)
    else:
        print('(--apply 로 생성)')


if __name__ == '__main__':
    main()
