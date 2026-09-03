# -*- coding: utf-8 -*-
"""사이드 목차(nav)를 모든 페이지에 다시 심는다.

nav가 파일마다 하드코딩돼 있어서, 클래스를 추가할 때마다 전 페이지를 손대야 한다.
이 스크립트가 그 일을 대신한다 — 페이지 깊이에 맞춰 상대경로를 계산하고,
현재 페이지에 해당하는 <a>에 class="cur"를 붙인다.

새 클래스를 추가할 때는 아래 NAV 목록만 고치고 이 스크립트를 돌리면 된다.

    python _source/rebuild_nav.py          # 드라이런
    python _source/rebuild_nav.py --apply
"""
import io, os, re, sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (그룹 제목, [(라벨, 경로 또는 None=예정), ...])
NAV = [
    ('시작', [
        ('홈', 'index.html'),
    ]),
    ('게임 기초', [
        ('피해 계산', 'basics/damage.html'),
        ('방어', 'basics/defense.html'),
        ('스킬 · 태그', 'basics/skills.html'),
    ]),
    ('아이템 · 제작', [
        ('아이템 · 드랍', 'basics/items.html'),
        ('제작 · 변환', 'basics/crafting.html'),
    ]),
    ('진행', [
        ('난이도 · 엔드게임', 'basics/endgame.html'),
    ]),
    ('클래스', [
        ('클래스 개요', 'classes/index.html'),
        ('추천 빌드', 'classes/picks.html'),
        ('빌드 가이드 색인', 'classes/build-index.html'),
        ('워록', 'classes/warlock/index.html'),
        ('└ 레벨링', 'classes/warlock/leveling.html'),
        ('└ 성장', 'classes/warlock/progression.html'),
        ('└ 빌드', 'classes/warlock/builds.html'),
        ('템플러', 'classes/templar/index.html'),
        ('└ 레벨링', 'classes/templar/leveling.html'),
        ('└ 성장', 'classes/templar/progression.html'),
        ('버서커', 'classes/berserker/index.html'),
        ('└ 레벨링', 'classes/berserker/leveling.html'),
        ('└ 성장', 'classes/berserker/progression.html'),
        ('워든', 'classes/warden/index.html'),
        ('└ 레벨링', 'classes/warden/leveling.html'),
        ('└ 성장', 'classes/warden/progression.html'),
        ('메카니스트', 'classes/mechanist/index.html'),
    ]),
    ('자료', [
        ('한영 명칭', 'basics/glossary.html'),
        ('이름 찾기', 'basics/names.html'),
        ('출처 · 신뢰도', 'meta/sources.html'),
        ('패치 동향', 'meta/patches.html'),
    ]),
]
NAV_RE = re.compile(r'<nav class="side">.*?</nav>', re.S)


def build(rel_from_site):
    """rel_from_site: 'classes/templar/index.html' 같은 사이트 루트 기준 경로"""
    depth = rel_from_site.count('/')
    root = '../' * depth
    out = ['<nav class="side">']
    for grp, items in NAV:
        out.append('  <div class="grp">%s</div>' % grp)
        out.append('  <ul>')
        for label, path in items:
            if path is None:
                out.append('    <li><a class="soon" href="#">%s</a></li>' % label)
            else:
                cur = ' class="cur"' if path == rel_from_site else ''
                out.append('    <li><a%s href="%s%s">%s</a></li>' % (cur, root, path, label))
        out.append('  </ul>')
    out.append('</nav>')
    return '\n'.join(out)


def main():
    apply = '--apply' in sys.argv
    changed = skipped = 0
    for dirpath, _, files in os.walk(SITE):
        if os.sep + '.git' in dirpath or os.sep + '_source' in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith('.html'):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, SITE).replace(os.sep, '/')
            s = io.open(p, encoding='utf-8').read()
            if '<nav class="side">' not in s:
                print('  nav 없음, 건너뜀: %s' % rel)
                skipped += 1
                continue
            new = NAV_RE.sub(lambda m: build(rel), s, count=1)
            if new == s:
                continue
            print('  갱신: %s' % rel)
            changed += 1
            if apply:
                io.open(p, 'w', encoding='utf-8', newline='\n').write(new)
    print('\n갱신 %d개 · 건너뜀 %d개%s' % (changed, skipped, '' if apply else '  (드라이런 — --apply 필요)'))


main()
