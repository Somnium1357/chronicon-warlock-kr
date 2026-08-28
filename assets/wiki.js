/* 크로니콘 위키 — 공통 스크립트 */

/* 1. 문서 목록 토글 (모바일). 데스크톱은 CSS가 항상 펼침 */
(function () {
  var nav = document.querySelector('nav.side');
  if (!nav) return;
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'navtoggle';
  btn.setAttribute('aria-expanded', 'false');
  btn.setAttribute('aria-controls', 'wikinav');
  var cur = nav.querySelector('a.cur');
  btn.textContent = '문서 목록' + (cur ? ' — ' + cur.textContent.replace(/^└\s*/, '') : '');
  nav.id = 'wikinav';
  nav.parentNode.insertBefore(btn, nav);
  btn.addEventListener('click', function () {
    var open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', String(open));
  });
})();

/* 2. 문서 내 목차 — h2를 모아 상단에 삽입 (h2가 3개 이상일 때만) */
(function () {
  var sec = document.querySelector('section');
  if (!sec) return;
  var hs = [].slice.call(sec.querySelectorAll('h2'));
  if (hs.length < 3) return;

  var used = {};
  function slug(t, i) {
    var s = t.trim().replace(/\s+/g, '-').replace(/[^\w가-힣ㄱ-ㅎ-]/g, '').slice(0, 40) || ('s' + i);
    while (used[s]) s = s + '-' + i;
    used[s] = 1;
    return s;
  }

  var box = document.createElement('div');
  box.className = 'pagetoc';
  var t = document.createElement('div');
  t.className = 't';
  t.textContent = '이 문서의 목차';
  box.appendChild(t);
  var ol = document.createElement('ol');

  hs.forEach(function (h, i) {
    if (!h.id) h.id = slug(h.textContent, i);
    var li = document.createElement('li');
    var a = document.createElement('a');
    a.href = '#' + h.id;
    // h2 안의 .en 같은 보조 텍스트는 목차에서 제외
    var clone = h.cloneNode(true);
    [].slice.call(clone.querySelectorAll('.en,.tag,.chip,.mono')).forEach(function (x) { x.remove(); });
    a.textContent = clone.textContent.trim();
    li.appendChild(a);
    ol.appendChild(li);

    // 제목 옆 앵커 링크
    if (!h.querySelector('.anchor')) {
      var an = document.createElement('a');
      an.className = 'anchor';
      an.href = '#' + h.id;
      an.textContent = '#';
      an.setAttribute('aria-label', '이 절 링크');
      h.appendChild(an);
    }
  });

  box.appendChild(ol);
  sec.insertBefore(box, sec.firstChild);
})();

/* 3. 문서 내 검색 */
(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var cnt = document.getElementById('cnt');
  var none = document.getElementById('none');
  var secs = [].slice.call(document.querySelectorAll('section'));
  var timer = null;

  function low(el) { return (el.textContent || '').toLowerCase(); }

  function clearMarks() {
    var m = document.querySelectorAll('mark');
    for (var i = 0; i < m.length; i++) {
      var p = m[i].parentNode;
      p.replaceChild(document.createTextNode(m[i].textContent), m[i]);
      p.normalize();
    }
  }

  function markIn(el, n, budget) {
    if (!n || budget <= 0) return budget;
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), arr = [], x;
    while ((x = w.nextNode())) {
      if (!x.nodeValue.trim()) continue;
      var pn = x.parentNode ? x.parentNode.nodeName : '';
      if (pn === 'MARK' || pn === 'SCRIPT' || pn === 'STYLE') continue;
      arr.push(x);
    }
    for (var i = 0; i < arr.length && budget > 0; i++) {
      var nd = arr[i], tx = nd.nodeValue, lo = tx.toLowerCase(), idx = lo.indexOf(n);
      if (idx < 0) continue;
      var f = document.createDocumentFragment(), from = 0;
      while (idx >= 0 && budget > 0) {
        if (idx > from) f.appendChild(document.createTextNode(tx.slice(from, idx)));
        var mk = document.createElement('mark');
        mk.textContent = tx.slice(idx, idx + n.length);
        f.appendChild(mk); budget--;
        from = idx + n.length; idx = lo.indexOf(n, from);
      }
      if (from < tx.length) f.appendChild(document.createTextNode(tx.slice(from)));
      nd.parentNode.replaceChild(f, nd);
    }
    return budget;
  }

  function run() {
    var n = q.value.trim().toLowerCase();
    var h = document.querySelectorAll('.hide');
    for (var i = 0; i < h.length; i++) h[i].classList.remove('hide');
    clearMarks();

    if (!n) { cnt.textContent = ''; none.classList.remove('on'); return; }

    var hits = 0, budget = 300;
    secs.forEach(function (s) {
      var vis = false, blocks = [];
      [].slice.call(s.children).forEach(function (k) {
        blocks.push({ el: k, head: (k.tagName === 'H2' || k.tagName === 'H3' || k.tagName === 'H4') });
      });
      blocks.forEach(function (o) {
        if (o.head) return;
        var el = o.el, ok = false;
        if (el.classList.contains('pagetoc')) { el.classList.add('hide'); return; } // 목차는 검색 대상 제외
        if (el.classList.contains('tw')) {
          var rows = el.querySelectorAll('tr'), rh = 0;
          for (var r = 0; r < rows.length; r++) {
            if (rows[r].querySelector('th')) continue;
            if (low(rows[r]).indexOf(n) >= 0) { rh++; hits++; budget = markIn(rows[r], n, budget); }
            else rows[r].classList.add('hide');
          }
          ok = rh > 0;
        } else if (el.tagName === 'UL' || el.tagName === 'OL') {
          var lh = 0;
          [].slice.call(el.children).forEach(function (li) {
            if (low(li).indexOf(n) >= 0) { lh++; hits++; budget = markIn(li, n, budget); }
            else li.classList.add('hide');
          });
          ok = lh > 0;
        } else if (el.classList.contains('grid')) {
          var gh = 0;
          [].slice.call(el.children).forEach(function (t) {
            if (low(t).indexOf(n) >= 0) { gh++; hits++; budget = markIn(t, n, budget); }
            else t.classList.add('hide');
          });
          ok = gh > 0;
        } else {
          ok = low(el).indexOf(n) >= 0;
          if (ok) { hits++; budget = markIn(el, n, budget); }
        }
        if (!ok) el.classList.add('hide'); else vis = true;
      });
      for (var i2 = 0; i2 < blocks.length; i2++) {
        if (!blocks[i2].head) continue;
        var keep = false;
        for (var j = i2 + 1; j < blocks.length; j++) {
          if (blocks[j].head) break;
          if (!blocks[j].el.classList.contains('hide')) { keep = true; break; }
        }
        if (!keep) blocks[i2].el.classList.add('hide');
      }
      if (!vis) s.classList.add('hide');
    });

    cnt.textContent = hits ? hits + '개' : '';
    none.classList.toggle('on', hits === 0);
  }

  q.addEventListener('input', function () { if (timer) clearTimeout(timer); timer = setTimeout(run, 140); });
  q.addEventListener('keydown', function (e) { if (e.key === 'Escape') { q.value = ''; run(); } });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') { e.preventDefault(); q.focus(); q.select(); }
  });
})();
