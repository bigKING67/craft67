(() => {
  const root = document.documentElement;
  const themeButton = document.querySelector('[data-theme-toggle]');
  const progress = document.querySelector('.reading-progress span');
  const nav = document.querySelector('[data-section-nav]');
  const navToggle = document.querySelector('[data-nav-toggle]');
  const navToggleLabel = document.querySelector('[data-nav-toggle-label]');
  const links = [...document.querySelectorAll('.section-nav a[href^="#"]')];
  const sections = links
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

  if (themeButton) {
    themeButton.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      themeButton.setAttribute('aria-pressed', String(next === 'dark'));
      themeButton.querySelector('span').textContent = next === 'dark' ? '日间阅读' : '夜间阅读';
    });
  }

  if (nav && navToggle) {
    const closeNav = () => {
      nav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    };
    navToggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(open));
    });
    links.forEach((link) => {
      link.addEventListener('click', () => {
        closeNav();
      });
    });
    nav.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        closeNav();
        navToggle.focus();
      }
    });
  }

  const update = () => {
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = scrollable > 0 ? Math.min(1, window.scrollY / scrollable) : 0;
    if (progress) progress.style.transform = `scaleX(${ratio})`;

    let current = sections[0];
    for (const section of sections) {
      if (section.getBoundingClientRect().top <= 148) current = section;
    }
    links.forEach((link) => {
      const active = current && link.getAttribute('href') === `#${current.id}`;
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
      if (active && navToggleLabel) {
        navToggleLabel.textContent = `目录 · ${link.textContent.trim()}`;
      }
    });
  };

  let scheduled = false;
  const scheduleUpdate = () => {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(() => {
      scheduled = false;
      update();
    });
  };

  root.classList.add('js');
  update();
  document.addEventListener('scroll', scheduleUpdate, { passive: true });
  window.addEventListener('resize', scheduleUpdate, { passive: true });
})();
