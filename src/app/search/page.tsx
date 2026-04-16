'use client';

import { useEffect, useRef } from 'react';
import Link from 'next/link';

declare global {
  interface Window {
    posthog?: { capture: (event: string, properties?: Record<string, unknown>) => void };
  }
}

export default function SearchPage() {
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load Pagefind UI via script tags — generated at build time into /pagefind/
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/pagefind/pagefind-ui.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = '/pagefind/pagefind-ui.js';
    script.onload = () => {
      if (searchRef.current) {
        // @ts-expect-error - PagefindUI is a global from the loaded script
        new window.PagefindUI({
          element: searchRef.current,
          showSubResults: true,
          showImages: false,
          filters: true,
        });

        // PostHog: track search queries via Pagefind input events
        const observer = new MutationObserver(() => {
          const input = searchRef.current?.querySelector<HTMLInputElement>('.pagefind-ui__search-input');
          if (input && !input.dataset.phTracked) {
            input.dataset.phTracked = 'true';
            let debounceTimer: ReturnType<typeof setTimeout>;
            input.addEventListener('input', () => {
              clearTimeout(debounceTimer);
              debounceTimer = setTimeout(() => {
                const query = input.value.trim();
                if (!query) return;
                const resultCount = searchRef.current?.querySelectorAll('.pagefind-ui__result').length ?? 0;
                if (resultCount === 0) {
                  window.posthog?.capture('search_no_results', { query });
                } else {
                  window.posthog?.capture('search_query', { query, result_count: resultCount });
                }
              }, 1500);
            });
          }
        });
        observer.observe(searchRef.current, { childList: true, subtree: true });
      }
    };
    document.head.appendChild(script);

    return () => {
      // Cleanup on unmount
      document.head.removeChild(link);
      document.head.removeChild(script);
    };
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Breadcrumb */}
      <nav style={{ marginBottom: '1.5rem', fontSize: '0.85rem' }}>
        <Link href="/" style={{ color: '#2c5f8a' }}>Home</Link>
        <span style={{ color: '#999', margin: '0 0.5rem' }}>/</span>
        <span style={{ color: '#999' }}>Search</span>
      </nav>

      <h1 style={{
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        color: '#1a2332',
        fontSize: '2rem',
        marginBottom: '0.5rem',
        lineHeight: 1.2,
      }}>
        Search the Register
      </h1>
      <p style={{ color: '#666', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: 1.6 }}>
        Search across all 200+ memorials by name, squadron, location, aircraft type, or crew member.
        Use the filters below to narrow results by squadron, county, aircraft, or record quality.
      </p>

      <div ref={searchRef} />

      <style>{`
        .pagefind-ui__search-input {
          font-family: 'Helvetica Neue', Arial, sans-serif !important;
        }
        .pagefind-ui__result-title {
          color: #1a2332 !important;
        }
        .pagefind-ui__result-excerpt mark {
          background-color: #d4c98c !important;
          color: #1a2332 !important;
        }
      `}</style>
    </div>
  );
}
