/* Living Thing — loading sequence: germinate → bloom → ink → reveal */
(function () {
  const loader = document.getElementById('loader');
  const caption = document.getElementById('loader-caption');
  const video = document.getElementById('loader-video');
  const body = document.body;

  const params = new URLSearchParams(location.search);
  const force = params.has('loader');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const seen = sessionStorage.getItem('lt-seen') && !force;

  function finish() {
    loader.classList.add('gone');
    loader.setAttribute('aria-hidden', 'true');
    body.classList.remove('lock', 'preload');
    body.classList.add('loaded');
    sessionStorage.setItem('lt-seen', '1');
  }

  if (seen) {
    finish();
    return;
  }

  body.classList.add('lock');

  // caption phases while the organism morphs
  const phases = ['( GERMINATE )', '( BLOOM )'];
  let phase = 0;
  const phaseTimer = setInterval(() => {
    phase += 1;
    if (phase < phases.length) caption.textContent = phases[phase];
  }, 1100);

  function zoomIn() {
    clearInterval(phaseTimer);
    caption.textContent = '( INK )';

    if (reduced) {
      // no zoom — quiet fade instead
      loader.classList.add('reveal');
      setTimeout(finish, 700);
      return;
    }

    loader.classList.add('zoom');

    loader.querySelector('.loader-stage').addEventListener(
      'transitionend',
      () => {
        loader.classList.add('ink'); // full black screen
        setTimeout(() => {
          loader.classList.add('reveal');
          body.classList.remove('preload');
          body.classList.add('loaded');
          setTimeout(finish, 750);
        }, 420);
      },
      { once: true }
    );
  }

  // start the zoom once the video has actually been seen morphing a moment
  const MIN_SHOW = reduced ? 900 : 2600;
  const t0 = performance.now();

  function armZoom() {
    const elapsed = performance.now() - t0;
    setTimeout(zoomIn, Math.max(0, MIN_SHOW - elapsed));
  }

  if (video.readyState >= 2) {
    armZoom();
  } else {
    video.addEventListener('canplay', armZoom, { once: true });
    // safety net if the video never loads
    setTimeout(zoomIn, 5000);
  }
})();

/* Corner mark — rises into the top-left once the hero mark scrolls away */
(function () {
  const mark = document.getElementById('corner-mark');
  const heroMark = document.querySelector('.hero-mark');
  const why = document.querySelector('.why');
  if (!mark || !heroMark) return;

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        mark.classList.toggle('show', !entry.isIntersecting);
      });
    },
    { threshold: 0 }
  );
  io.observe(heroMark);

  // invert the mark while it floats over the ink sections (hero, why, footer)
  const hero = document.querySelector('.hero');
  function checkDark() {
    const overHero = hero && hero.getBoundingClientRect().bottom > 68;
    const overWhy = why && why.getBoundingClientRect().top < 68;
    mark.classList.toggle('on-dark', overHero || overWhy);
  }
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(() => {
        checkDark();
        ticking = false;
      });
    }
  }, { passive: true });
  checkDark();
})();

/* Gentle scroll reveals */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const targets = document.querySelectorAll(
    '.belief, .service-rows li, .case, .why h2, .why-body'
  );

  targets.forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(18px)';
    el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
  });

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'none';
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  targets.forEach((el) => io.observe(el));
})();
