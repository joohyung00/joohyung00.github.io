/* joohyung00.github.io — no dependencies.
   1) dark-mode toggle (localStorage)  2) nav scroll-spy (only if the nav has #links)  3) news "show all"
   4) photo carousel (scroll-snap + arrows + dots + autoplay)  5) recent posts from /mypages/index.json
   6) slide viewer on talks/<key>/ and seminars/<key>/ (scroll-snap track + arrows + keys + thumbnail rail + fullscreen + #sN links) */
(function () {
  var html = document.documentElement;

  // 1) theme toggle
  var tb = document.querySelector('.themeToggle');
  function paintToggle() { if (tb) tb.textContent = html.getAttribute('data-mode') === 'dark' ? '☀' : '☾'; }
  if (tb) tb.addEventListener('click', function () {
    var m = html.getAttribute('data-mode') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-mode', m);
    try { localStorage.setItem('mode', m); } catch (e) {}
    paintToggle();
  });
  paintToggle();

  // 2) scroll-spy
  var links = [].slice.call(document.querySelectorAll('.nav nav a[href^="#"]'));
  var secs = links.map(function (a) { return document.querySelector(a.getAttribute('href')); }).filter(Boolean);
  if (secs.length && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id); });
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    secs.forEach(function (s) { io.observe(s); });
  }

  // 3) news show-all (collapsed only when JS runs, so no-JS readers see everything)
  var news = document.querySelector('.news');
  var moreBtn = document.querySelector('[data-toggle-news]');
  if (news && moreBtn) {
    news.classList.add('collapsed');
    var label = moreBtn.textContent;
    moreBtn.addEventListener('click', function () {
      var open = news.classList.toggle('collapsed');
      moreBtn.textContent = open ? label : 'show less ▴';
    });
  }

  // 4) carousel
  document.querySelectorAll('[data-carousel]').forEach(function (c) {
    var track = c.querySelector('.track'), slides = [].slice.call(track.children), dots = c.querySelector('.dots');
    if (slides.length < 2) { c.querySelectorAll('.arrow,.dots').forEach(function (x) { x.hidden = true; }); return; }
    var idx = 0, timer;
    slides.forEach(function (_, i) {
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-label', 'Photo ' + (i + 1));
      b.addEventListener('click', function () { go(i); restart(); }); dots.appendChild(b);
    });
    function paint() { [].forEach.call(dots.children, function (d, i) { d.classList.toggle('on', i === idx); }); }
    function go(i) { idx = (i + slides.length) % slides.length; track.scrollTo({ left: slides[idx].offsetLeft - track.offsetLeft, behavior: 'smooth' }); paint(); }
    function restart() { clearInterval(timer); timer = setInterval(function () { go(idx + 1); }, 6000); }
    c.querySelector('.prev').addEventListener('click', function () { go(idx - 1); restart(); });
    c.querySelector('.next').addEventListener('click', function () { go(idx + 1); restart(); });
    track.addEventListener('scroll', function () {            // keep dots in sync with manual swipes
      var x = track.scrollLeft, best = 0, bd = 1e9;
      slides.forEach(function (s, i) { var d = Math.abs(s.offsetLeft - track.offsetLeft - x); if (d < bd) { bd = d; best = i; } });
      if (best !== idx) { idx = best; paint(); }
    }, { passive: true });
    track.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') { go(idx + 1); restart(); } if (e.key === 'ArrowLeft') { go(idx - 1); restart(); } });
    c.addEventListener('mouseenter', function () { clearInterval(timer); });
    c.addEventListener('mouseleave', restart);
    paint(); restart();
  });

  // 6) slide viewer (talks/<key>/)
  [].forEach.call(document.querySelectorAll('[data-viewer]'), function (v) {
    var track = v.querySelector('.track'), figs = [].slice.call(track.children), n = figs.length;
    var count = v.querySelector('.count b'), rail = v.querySelector('.rail');
    var thumbs = rail ? [].slice.call(rail.children) : [], idx = 0, lock = false;
    function warm(i) { var f = figs[i]; if (f) { var im = f.querySelector('img'); if (im && im.loading === 'lazy') im.loading = 'eager'; } }
    function paint() {
      if (count) count.textContent = idx + 1;
      thumbs.forEach(function (b, i) { b.classList.toggle('on', i === idx); });
      var b = thumbs[idx];
      if (b && rail) rail.scrollLeft = b.offsetLeft - rail.offsetLeft - rail.clientWidth / 2 + b.clientWidth / 2;
      warm(idx + 1); warm(idx + 2); warm(idx - 1);
      if (history.replaceState && (!location.hash || /^#s\d+$/.test(location.hash))) history.replaceState(null, '', '#s' + (idx + 1));
    }
    function go(i, instant) {
      var prev = idx;
      idx = Math.max(0, Math.min(n - 1, i)); lock = true;
      track.scrollTo({ left: figs[idx].offsetLeft, behavior: (instant || Math.abs(idx - prev) > 3) ? 'auto' : 'smooth' });  // long jumps: no animation
      paint(); setTimeout(function () { lock = false; }, 450);
    }
    v.querySelector('.prev').addEventListener('click', function () { go(idx - 1); });
    v.querySelector('.next').addEventListener('click', function () { go(idx + 1); });
    thumbs.forEach(function (b) { b.addEventListener('click', function () { go(+b.getAttribute('data-i')); }); });
    var lastW = track.clientWidth;
    track.addEventListener('scroll', function () {
      if (lock) return;
      if (track.clientWidth !== lastW) { lastW = track.clientWidth; track.scrollLeft = figs[idx].offsetLeft; return; }  // re-layout, not the user
      var x = track.scrollLeft, best = 0, bd = 1e9;
      figs.forEach(function (f, i) { var d = Math.abs(f.offsetLeft - x); if (d < bd) { bd = d; best = i; } });
      if (best !== idx) { idx = best; paint(); }
    }, { passive: true });
    document.addEventListener('keydown', function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); go(idx + 1); }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); go(idx - 1); }
      else if (e.key === 'Home') { e.preventDefault(); go(0); }
      else if (e.key === 'End') { e.preventDefault(); go(n - 1); }
    });
    var fs = v.querySelector('.fs');
    if (fs) {
      if (!track.requestFullscreen) fs.hidden = true;
      fs.addEventListener('click', function () { if (document.fullscreenElement) document.exitFullscreen(); else track.requestFullscreen(); });
      document.addEventListener('fullscreenchange', function () { setTimeout(function () { go(idx, true); }, 80); });
    }
    window.addEventListener('resize', function () { lastW = track.clientWidth; lock = true; track.scrollLeft = figs[idx].offsetLeft; setTimeout(function () { lock = false; }, 150); });
    var m = /^#s(\d+)$/.exec(location.hash);
    if (m) go(+m[1] - 1, true); else paint();
  });

  // 5) recent posts: the list is baked in at build time from the my-page manifest; here it is
  //    refreshed from the live manifest so a newly published post shows up without a rebuild.
  var ps = document.querySelector('[data-posts]');
  if (ps && window.fetch) {
    fetch(ps.getAttribute('data-posts'), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (m) {
      if (!m || !m.pages) return;
      var skip = (ps.getAttribute('data-posts-exclude') || '').split(',').filter(Boolean);   // profile.yml posts_exclude
      var pages = m.pages.filter(function (p) { return skip.indexOf(p.slug) < 0; });
      if (!pages.length) return;
      pages = pages.sort(function (a, b) { return (b.created || '').localeCompare(a.created || ''); }).slice(0, 3);
      var box = ps.querySelector('.postlist');
      box.innerHTML = '';
      pages.forEach(function (p) {
        var d = (p.created || '').slice(0, 10);
        var ex = (p.excerpt || '').replace(/\s+/g, ' ').trim(); if (ex.length > 140) ex = ex.slice(0, 140) + '…';
        var el = document.createElement('div'); el.className = 'post';
        el.innerHTML = '<span class="d"></span><div><a class="t"></a><div class="x"></div></div>';
        el.querySelector('.d').textContent = d;
        var a = el.querySelector('a'); a.href = p.url; a.textContent = p.title || p.slug;
        el.querySelector('.x').textContent = ex;
        box.appendChild(el);
      });
      ps.hidden = false;
    }).catch(function () {});
  }
})();
