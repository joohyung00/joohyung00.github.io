/* joohyung00.github.io — no dependencies.
   1) dark-mode toggle (localStorage)  2) nav scroll-spy  3) news "show all"
   4) photo carousel (scroll-snap + arrows + dots + autoplay)  5) recent posts from /mypages/index.json */
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

  // 5) recent posts: the list is baked in at build time from the my-page manifest; here it is
  //    refreshed from the live manifest so a newly published post shows up without a rebuild.
  var ps = document.querySelector('[data-posts]');
  if (ps && window.fetch) {
    fetch(ps.getAttribute('data-posts'), { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (m) {
      if (!m || !m.pages || !m.pages.length) return;
      var pages = m.pages.slice().sort(function (a, b) { return (b.created || '').localeCompare(a.created || ''); }).slice(0, 3);
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
