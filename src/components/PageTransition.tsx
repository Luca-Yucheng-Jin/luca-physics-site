import { useEffect, useRef, useState } from 'react';

type TransitionState = 'idle' | 'arriving' | 'leaving';

type StoredTransition = {
  x?: number;
  y?: number;
};

const STORAGE_KEY = 'luca-page-transition';

function readArrival(): StoredTransition | null {
  try {
    const value = sessionStorage.getItem(STORAGE_KEY);
    if (!value) return null;
    sessionStorage.removeItem(STORAGE_KEY);
    return JSON.parse(value) as StoredTransition;
  } catch {
    return null;
  }
}

function isTransitionLink(anchor: HTMLAnchorElement, event: MouseEvent) {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
  if (anchor.target && anchor.target !== '_self') return false;
  if (anchor.hasAttribute('download') || anchor.hasAttribute('data-no-transition')) return false;

  const raw = anchor.getAttribute('href') || '';
  if (!raw || raw.startsWith('#') || /^(mailto:|tel:|javascript:)/i.test(raw)) return false;

  const target = new URL(anchor.href, window.location.href);
  if (target.origin !== window.location.origin) return false;
  if (target.pathname === window.location.pathname && target.search === window.location.search) return false;
  return /(?:\.html)?\/?$/i.test(target.pathname);
}

export function PageTransition() {
  const arrival = useRef<StoredTransition | null>(readArrival());
  const [state, setState] = useState<TransitionState>(arrival.current ? 'arriving' : 'idle');

  useEffect(() => {
    const initial = arrival.current;
    if (!initial) return;
    document.documentElement.style.setProperty('--transition-x', `${(initial.x ?? 0.5) * 100}%`);
    document.documentElement.style.setProperty('--transition-y', `${(initial.y ?? 0.5) * 100}%`);
    const timer = window.setTimeout(() => setState('idle'), 760);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let navigationTimer = 0;

    const onClick = (event: MouseEvent) => {
      const target = event.target as Element | null;
      const anchor = target?.closest('a') as HTMLAnchorElement | null;
      if (!anchor || !isTransitionLink(anchor, event)) return;

      event.preventDefault();
      const x = event.clientX / Math.max(window.innerWidth, 1);
      const y = event.clientY / Math.max(window.innerHeight, 1);
      if (reducedMotion.matches) {
        window.location.assign(anchor.href);
        return;
      }

      document.documentElement.style.setProperty('--transition-x', `${x * 100}%`);
      document.documentElement.style.setProperty('--transition-y', `${y * 100}%`);
      setState('leaving');

      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ x, y }));
      } catch {
        // Navigation still works when storage is unavailable.
      }

      navigationTimer = window.setTimeout(() => window.location.assign(anchor.href), 600);
    };

    document.addEventListener('click', onClick, true);
    return () => {
      document.removeEventListener('click', onClick, true);
      window.clearTimeout(navigationTimer);
    };
  }, []);

  return (
    <div className={`cosmic-page-transition cosmic-page-transition--${state}`} aria-hidden="true">
      <div className="cosmic-page-transition__field" />
      <div className="cosmic-page-transition__ring" />
    </div>
  );
}
