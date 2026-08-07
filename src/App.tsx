import { PageTransition } from './components/PageTransition';

const projects = [
  {
    title: 'Optical Optimization of Semitransparent Perovskite Devices',
    meta: 'Research Intern · Fudan University · Summer 2025',
  },
  {
    title: 'Validating the Higgs Boson',
    meta: 'Imperial College London · Statistical analysis · 2025',
  },
  {
    title: 'The Kelvin Water Dropper',
    meta: 'Imperial College London · Theoretical modelling · 2025',
  },
];

const notes = [
  {
    subject: 'Quantum field theory',
    title: 'Path Integrals and the Quantum–Statistical Correspondence',
    href: 'notes/path-integral.html',
  },
  {
    subject: 'Quantum field theory',
    title: 'Nonabelian Symmetries — Srednicki Ch. 24',
    href: 'notes/srednicki-nonabelian.html',
  },
  {
    subject: 'General relativity',
    title: 'Linearised Gravity and Gravitational Waves',
    href: 'notes/tong-gr-ps4.html',
  },
  {
    subject: 'Quantum mechanics',
    title: 'Non-Degeneracy and Reality of Bound States in 1D',
    href: 'notes/qm-bound-states.html',
  },
];

export default function App() {
  return (
    <>
      <PageTransition />

      <header className="masthead">
        <a className="wordmark" href="#top" aria-label="Yucheng (Luca) Jin — home">
          Luca Jin
        </a>
        <nav aria-label="Primary navigation">
          <a href="#about">About</a>
          <a href="notes.html">Notes</a>
          <a href="research.html">Research</a>
          <a href="reading.html">Reading</a>
        </nav>
        <a className="contact-link" href="mailto:luca.jin@outlook.com">Contact</a>
      </header>

      <main>
        <section id="top" className="hero-home">
          <picture className="hero-home__image" aria-hidden="true">
            <source media="(max-width: 680px)" srcSet={`${import.meta.env.BASE_URL}assets/black-hole-hero-mobile.png`} />
            <img src={`${import.meta.env.BASE_URL}assets/black-hole-hero.png`} alt="" fetchPriority="high" />
          </picture>
          <div className="hero-home__shade" />
          <div className="hero-home__content shell">
            <p className="eyebrow">Physics with Theoretical Physics · Imperial College London</p>
            <h1>Yucheng <em>(Luca)</em> Jin</h1>
            <p className="hero-home__intro">
              A working notebook of solved problems, self-contained derivations,
              and research in theoretical physics.
            </p>
            <div className="hero-home__actions">
              <a className="button button--light" href="notes.html">Explore notes <span>↗</span></a>
              <a className="text-link" href="research.html">Research <span>→</span></a>
            </div>
          </div>
          <span className="hero-home__index" aria-hidden="true">01 / 04</span>
        </section>

        <section id="about" className="section shell">
          <div className="section-label">About</div>
          <div className="about-copy">
            <h2>A place to think in public.</h2>
            <p>
              I am an undergraduate at Imperial College London studying Physics
              with Theoretical Physics. My interests lie in quantum field theory,
              gauge theory, geometry, and black-hole physics. This site collects
              the notes and derivations I write while learning them.
            </p>
            <dl className="facts">
              <div><dt>Education</dt><dd>Imperial College London</dd></div>
              <div><dt>Programme</dt><dd>BSc Physics with Theoretical Physics</dd></div>
              <div><dt>Based in</dt><dd>London</dd></div>
            </dl>
          </div>
        </section>

        <section className="section shell section--ruled">
          <div className="section-label">Selected work</div>
          <div className="work-list">
            {projects.map((project, index) => (
              <a className="work-row" href="research.html" key={project.title}>
                <span className="work-row__number">0{index + 1}</span>
                <span className="work-row__copy">
                  <strong>{project.title}</strong>
                  <small>{project.meta}</small>
                </span>
                <span className="work-row__arrow" aria-hidden="true">↗</span>
              </a>
            ))}
          </div>
        </section>

        <section className="section shell section--ruled">
          <div className="section-label">Recent notes</div>
          <div className="notes-grid">
            {notes.map((note) => (
              <a className="note-card" href={note.href} key={note.href}>
                <span>{note.subject}</span>
                <strong>{note.title}</strong>
                <i aria-hidden="true">Read ↗</i>
              </a>
            ))}
          </div>
          <a className="button button--outline" href="notes.html">View all notes <span>↗</span></a>
        </section>

        <section className="contact-section-simple shell">
          <p className="eyebrow">Contact</p>
          <h2>Questions, corrections,<br />or a good problem?</h2>
          <a href="mailto:luca.jin@outlook.com">luca.jin@outlook.com <span>↗</span></a>
        </section>
      </main>

      <footer className="footer-simple shell">
        <span>© 2026 Yucheng (Luca) Jin</span>
        <div><a href="notes.html">Notes</a><a href="research.html">Research</a><a href="reading.html">Reading</a></div>
      </footer>
    </>
  );
}
