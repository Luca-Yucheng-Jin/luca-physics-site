import { useEffect } from 'react';

declare global {
  interface Window {
    MathJax?: {
      typesetPromise?: (elements?: Element[]) => Promise<void>;
    };
  }
}

type Work = {
  number: string;
  subject: string;
  title: string;
  html: string;
  pdf: string;
};

const featuredWorks: Work[] = [
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

const researchProjects = [
  {
    title: 'Optical Optimization of Semitransparent Perovskite Devices',
    meta: 'Fudan University · Research internship · 2025',
    html: 'research/perovskite-devices.html',
    pdf: 'output/pdf/research-perovskite-devices.pdf',
  },
  {
    title: 'Validating the Higgs Boson',
    meta: 'Imperial College London · Statistical analysis · 2025',
    html: 'research/higgs-validation.html',
    pdf: 'output/pdf/research-higgs-validation.pdf',
  },
  {
    title: 'The Kelvin Water Dropper',
    meta: 'Imperial College London · Modelling project · 2025',
    html: 'research/kelvin-water-dropper.html',
    pdf: 'output/pdf/research-kelvin-water-dropper.pdf',
  },
];

function FormatLinks({ html, pdf }: Pick<Work, 'html' | 'pdf'>) {
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
      <header className="site-header">
        <a className="site-wordmark" href="#top">Luca Jin</a>
        <nav aria-label="Primary navigation">
          <a href="notes.html">Work</a>
          <a href="research.html">Research</a>
          <a href="#about">About</a>
          <a href="mailto:luca.jin@outlook.com">Contact</a>
        </nav>
        <span className="site-header__meta">Physics · Imperial College London</span>
      </header>

      <main id="top">
        <section className="home-hero page-shell">
          <div className="home-hero__copy">
            <p className="kicker">Yucheng (Luca) Jin · Theoretical physics</p>
            <h1>Physics,<br /><em>worked out.</em></h1>
            <p className="home-hero__lede">
              Derivations, calculations, and <strong>research</strong>—written to be inspected.
            </p>
            <div className="home-hero__actions">
              <a className="primary-link" href="notes.html">Browse 48 works <span>→</span></a>
              <a className="quiet-link" href="research.html">Research</a>
            </div>
          </div>
          <aside className="archive-cover" aria-label="Archive summary">
            <span className="archive-cover__eyebrow">Public archive · 2026</span>
            <strong>48</strong>
            <em>works</em>
            <dl>
              <div><dt>Subjects</dt><dd>07</dd></div>
              <div><dt>Editions</dt><dd>HTML + PDF</dd></div>
            </dl>
          </aside>
        </section>

        <section className="home-section page-shell" aria-labelledby="selected-work-title">
          <div className="section-heading">
            <div>
              <p className="kicker">Archive · 48 works</p>
              <h2 id="selected-work-title">Selected work.</h2>
            </div>
            <a className="section-heading__link" href="notes.html">All 48 works <span>→</span></a>
          </div>

          <div className="featured-list">
            {featuredWorks.map((work) => (
              <article className="featured-row" key={work.number}>
                <span className="featured-row__number">{work.number}</span>
                <div className="featured-row__body">
                  <p>{work.subject}</p>
                  <h3>{work.title}</h3>
                </div>
                <FormatLinks html={work.html} pdf={work.pdf} />
              </article>
            ))}
          </div>
        </section>

        <section className="home-section home-section--tint" aria-labelledby="research-title">
          <div className="page-shell">
            <div className="section-heading">
              <div>
                <p className="kicker">Research and projects</p>
                <h2 id="research-title">Research.</h2>
              </div>
              <a className="section-heading__link" href="research.html">Research overview <span>→</span></a>
            </div>

            <div className="research-grid">
              {researchProjects.map((project, index) => (
                <article className="research-card" key={project.title}>
                  <span className="research-card__index">0{index + 1}</span>
                  <p>{project.meta}</p>
                  <h3>{project.title}</h3>
                  <FormatLinks html={project.html} pdf={project.pdf} />
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="about" className="about-section page-shell">
          <div className="about-section__grid">
            <h2>Fields, spacetime, and the <em>structures beneath them.</em></h2>
            <div>
              <p>
                I study Physics with Theoretical Physics at Imperial College London.
                This is my public working archive.
              </p>
              <a className="primary-link primary-link--small" href="mailto:luca.jin@outlook.com">
                Get in touch <span>↗</span>
              </a>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer page-shell">
        <span>© 2026 Yucheng (Luca) Jin</span>
        <span>London · HTML and PDF editions</span>
        <div><a href="notes.html">Work</a><a href="research.html">Research</a><a href="mailto:luca.jin@outlook.com">Email</a></div>
      </footer>
    </>
  );
}
