type Subject = {
  number: string;
  title: string;
  count: number;
  href: string;
};

const subjects: Subject[] = [
  {
    number: '01',
    title: 'Quantum Field Theory',
    count: 20,
    href: 'notes-qft.html',
  },
  {
    number: '02',
    title: 'General Relativity',
    count: 4,
    href: 'notes-advanced.html',
  },
  {
    number: '03',
    title: 'Quantum Mechanics',
    count: 3,
    href: 'notes-qm.html',
  },
  {
    number: '04',
    title: 'Electrodynamics',
    count: 8,
    href: 'notes-ed.html',
  },
  {
    number: '05',
    title: 'Mathematical Methods',
    count: 6,
    href: 'notes-mm.html',
  },
  {
    number: '06',
    title: 'Differential Equations',
    count: 3,
    href: 'notes-de.html',
  },
  {
    number: '07',
    title: 'Thermodynamics & Statistical Physics',
    count: 4,
    href: 'notes-tdsp.html',
  },
];

function toggleTheme(event: React.MouseEvent<HTMLButtonElement>) {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  event.currentTarget.setAttribute(
    'aria-label',
    next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme',
  );

  const themeMeta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  themeMeta?.setAttribute('content', next === 'dark' ? '#15120e' : '#f5f1e7');
  try { window.localStorage.setItem('luca-theme', next); } catch { /* storage is optional */ }
}

function adjustFontScale(delta: number) {
  const root = document.documentElement;
  const inlineScale = Number.parseFloat(root.style.getPropertyValue('--font-scale'));
  let storedScale = Number.NaN;
  try { storedScale = Number.parseFloat(window.localStorage.getItem('luca-font-scale') || ''); } catch { /* storage is optional */ }
  const current = Number.isFinite(inlineScale) ? inlineScale : Number.isFinite(storedScale) ? storedScale : 1;
  const next = Math.round(Math.min(1.5, Math.max(0.7, current + delta)) * 10) / 10;
  root.style.setProperty('--font-scale', String(next));
  try { window.localStorage.setItem('luca-font-scale', String(next)); } catch { /* storage is optional */ }
}

export default function App() {
  return (
    <>
      <header className="topbar" id="top">
        <a className="topbar__brand" href="#top">Luca Jin <small>Physics · Imperial</small></a>
        <nav className="topbar__nav" aria-label="Primary navigation">
          <a className="is-active" href="#top">Home</a>
          <a href="notes.html">Notes</a>
          <a href="mailto:luca.jin@outlook.com">Contact</a>
          <button className="font-toggle" type="button" data-font-size="dec" aria-label="Decrease font size" onClick={() => adjustFontScale(-0.1)}>A<span className="font-toggle__small">−</span></button>
          <button className="font-toggle" type="button" data-font-size="inc" aria-label="Increase font size" onClick={() => adjustFontScale(0.1)}>A<span className="font-toggle__large">+</span></button>
          <button className="theme-toggle" type="button" data-theme-toggle aria-label="Switch colour theme" onClick={toggleTheme}>
            <svg className="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" /></svg>
            <svg className="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></svg>
          </button>
        </nav>
      </header>

      <main>
        <section className="home-hero page-shell">
          <div className="home-hero__copy">
            <p className="kicker">Physics with Theoretical Physics · Imperial College London</p>
            <h1>I’m Yucheng <em>(Luca) Jin.</em></h1>
            <p className="home-hero__lede">
              I’m a third-year theoretical physics student at Imperial College London.
              This site collects my notes, worked problems, and longer write-ups,
              each available in HTML and PDF.
            </p>
            <div className="home-hero__actions">
              <a className="primary-link" href="notes.html">Browse notes <span>→</span></a>
              <a className="quiet-link" href="mailto:luca.jin@outlook.com">Email me</a>
            </div>
          </div>
        </section>

        <section className="home-section page-shell" aria-labelledby="subjects-title">
          <div className="section-heading">
            <div>
              <p className="kicker">Seven subjects · 48 notes</p>
              <h2 id="subjects-title">Notes by subject.</h2>
            </div>
            <a className="section-heading__link" href="notes.html">All notes <span>→</span></a>
          </div>

          <nav className="subject-list" aria-label="Notes by subject">
            {subjects.map((subject) => (
              <a className="subject-row" href={subject.href} key={subject.number}>
                <span className="subject-row__number">{subject.number}</span>
                <h3>{subject.title}</h3>
                <span className="subject-row__count">{subject.count} notes</span>
                <span className="subject-row__arrow" aria-hidden="true">→</span>
              </a>
            ))}
          </nav>
        </section>
      </main>

      <footer className="footer">
        <span>© 2026 Yucheng (Luca) Jin</span>
        <span><a href="#top">Home</a> · <a href="notes.html">Notes</a> · <a href="mailto:luca.jin@outlook.com">Email</a></span>
      </footer>
    </>
  );
}
