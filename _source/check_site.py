# -*- coding: utf-8 -*-
"""사이트 무결성 검사 — HTML 파싱 · 내부 링크 · 자산 경로 · 필수 요소."""
import io, os, re, sys
from html.parser import HTMLParser

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'col'}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errs = []
        self.links = []
        self.ids = set()
        self.has = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))
        if tag == 'a' and a.get('href'):
            self.links.append((a['href'], self.getpos()[0]))
        if tag in ('link', 'script') and (a.get('href') or a.get('src')):
            self.links.append((a.get('href') or a.get('src'), self.getpos()[0]))
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'nav' and 'side' in a.get('class', ''):
            self.has.add('nav')
        if tag == 'input' and a.get('id') == 'q':
            self.has.add('search')

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errs.append('%d행: 닫는 </%s>에 대응하는 여는 태그 없음' % (self.getpos()[0], tag))
            return
        t, ln = self.stack.pop()
        if t != tag:
            self.errs.append('%d행: </%s> 인데 열려 있던 건 <%s> (%d행)' % (self.getpos()[0], tag, t, ln))


def main():
    problems = []
    pages = []
    for dirpath, _, files in os.walk(SITE):
        if os.sep + '.git' in dirpath or os.sep + '_source' in dirpath:
            continue
        for fn in sorted(files):
            if fn.endswith('.html'):
                pages.append(os.path.join(dirpath, fn))

    idmap, anchors = {}, []

    for p in pages:
        rel = os.path.relpath(p, SITE).replace(os.sep, '/')
        s = io.open(p, encoding='utf-8').read()
        par = P()
        par.feed(s)
        for e in par.errs:
            problems.append('[%s] %s' % (rel, e))
        if par.stack:
            problems.append('[%s] 안 닫힌 태그: %s'
                            % (rel, ', '.join('<%s>(%d행)' % t for t in par.stack)))
        for need, label in [('nav', '사이드 목차'), ('search', '문서 내 검색창')]:
            if need not in par.has:
                problems.append('[%s] %s 없음' % (rel, label))
        for key in ['assets/wiki.css', 'assets/wiki.js']:
            if key not in s:
                problems.append('[%s] %s 링크 없음' % (rel, key))
        if 'noindex' not in s:
            problems.append('[%s] robots noindex 메타 없음' % rel)

        # id 수집 · 중복 검사 — 같은 id 가 둘이면 앵커 링크가 엉뚱한 데로 간다
        ids = re.findall(r'\sid="([^"]+)"', s)
        idmap[p] = set(ids)
        for i in sorted(set(ids)):
            if ids.count(i) > 1:
                problems.append('[%s] id="%s" 가 %d번 중복' % (rel, i, ids.count(i)))

        base = os.path.dirname(p)
        for href, ln in par.links:
            if href.startswith(('http://', 'https://', 'mailto:', '#')) or not href:
                continue
            tgt, _, frag = href.partition('#')
            if not tgt:
                continue
            full = os.path.normpath(os.path.join(base, tgt))
            if not os.path.exists(full):
                problems.append('[%s] %d행 깨진 링크: %s' % (rel, ln, href))
            elif frag:
                anchors.append((rel, ln, href, full, frag))

    for rel, ln, href, full, frag in anchors:
        if full in idmap and frag not in idmap[full]:
            problems.append('[%s] %d행 없는 앵커: %s' % (rel, ln, href))

    print('페이지 %d개 검사' % len(pages))
    for p in sorted(pages):
        print('  ' + os.path.relpath(p, SITE).replace(os.sep, '/'))
    print()
    if not problems:
        print('✅ 문제 없음')
        return 0
    print('❌ 문제 %d건' % len(problems))
    for x in problems:
        print('  ' + x)
    return 1


sys.exit(main())
