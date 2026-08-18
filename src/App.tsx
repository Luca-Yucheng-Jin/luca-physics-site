import { useEffect } from 'react';

declare global {
  interface Window {
    MathJax?: {
      typesetPromise?: (elements?: Element[]) => Promise<void>;
    };
  }
}

type Note = {
  number: string;
  subject: string;
  title: string;
  html: string;
  pdf: string;
};

const featuredNotes: Note[] = [
  {
    number: '01',
    subject: 'Long-form essay · Quantum theory',
    title: 'Path Integrals and the Quantum–Statistical Correspondence',
    html: 'notes/path-integral.html',
    pdf: 'output/pdf/path-integral.pdf',
  },
  {
    number: '02',
    subject: 'Advanced QFT · Problem set',
    title: 'Feynman Graphs and Renormalization-Group Calculations',
    html: 'notes/osborn-aqft-ps3.html',
    pdf: 'output/pdf/osborn-aqft-ps3.pdf',
  },
  {
    number: '03',
    subject: 'Renormalization · Study notes',
    title: 'Renormalization Group for \\(\\phi\\)-\\(\\chi\\) Theory',
    html: 'notes/srednicki-rg-phi-chi.html',
    pdf: 'output/pdf/srednicki-rg-phi-chi.pdf',
  },
  {
    number: '04',
    subject: 'General relativity · Problem set',
    title: 'Linearised Gravity and Gravitational Waves',
    html: 'notes/tong-gr-ps4.html',
    pdf: 'output/pdf/tong-gr-ps4.pdf',
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

function FormatLinks({ html, pdf }: Pick<Note, 'html' | 'pdf'>) {
  return (
    <span className="format-links" aria-label="Available formats">
      <a href={html}>HTML <span aria-hidden="true">↗</span></a>
      <a href={pdf}>PDF <span aria-hidden="true">↓</span></a>
    </span>
  );
}

export default function App() {
  useEffect(() => {
    let attempts = 0;
    const root = document.getElementById('root');
    const typeset = () => {
      attempts += 1;
      if (root && window.MathJax?.typesetPromise) {
        void window.MathJax.typesetPromise([root]);
        return true;
      }
      return attempts > 80;
    };

    if (typeset()) return undefined;
    const timer = window.setInterval(() => {
      if (typeset()) window.clearInterval(timer);
    }, 100);
    return () => window.clearInterval(timer);
  }, []);

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
            <h1>Hi, I’m <em>Luca.</em></h1>
            <p className="home-hero__lede">
              This site collects my physics notes, worked problems, and longer write-ups.
              Every note is available to read in HTML or download as a PDF.
            </p>
            <div className="home-hero__actions">
              <a className="primary-link" href="notes.html">Browse notes <span>→</span></a>
              <a className="quiet-link" href="mailto:luca.jin@outlook.com">Email me</a>
            </div>
          </div>
        </section>

        <section className="home-section page-shell" aria-labelledby="selected-notes-title">
          <div className="section-heading">
            <div>
              <p className="kicker">Notes archive · 48 entries</p>
              <h2 id="selected-notes-title">Selected notes.</h2>
            </div>
            <a className="section-heading__link" href="notes.html">All notes <span>→</span></a>
          </div>

          <div className="featured-list">
            {featuredNotes.map((note) => (
              <article className="featured-row" key={note.number}>
                <span className="featured-row__number">{note.number}</span>
                <div className="featured-row__body">
                  <p>{note.subject}</p>
                  <h3>{note.title}</h3>
                </div>
                <FormatLinks html={note.html} pdf={note.pdf} />
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer">
        <span>© 2026 Yucheng (Luca) Jin</span>
        <span><a href="#top">Home</a> · <a href="notes.html">Notes</a> · <a href="mailto:luca.jin@outlook.com">Email</a></span>
      </footer>
    </>
  );
}
