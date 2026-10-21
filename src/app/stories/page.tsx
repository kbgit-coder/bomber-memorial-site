import { Metadata } from 'next';
import Link from 'next/link';
import { getAllStories } from '@/lib/stories';
import { getMemorialBySlug } from '@/lib/data';

export const metadata: Metadata = {
  title: 'Stories | Bomber Command Memorial Register',
  description:
    'Personal stories from the families and communities connected to Bomber Command memorials. First-hand accounts, family memories, and the living chain of remembrance.',
};

export default function StoriesIndex() {
  const stories = getAllStories();

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <nav style={{ marginBottom: '1.5rem', fontSize: '0.85rem' }}>
        <Link href="/" style={{ color: '#7a4500' }}>
          Home
        </Link>
        <span style={{ color: '#999', margin: '0 0.5rem' }}>/</span>
        <span style={{ color: '#999' }}>Stories</span>
      </nav>

      <h1 style={h1Style}>Stories</h1>
      <p
        style={{
          fontSize: '1.1rem',
          color: '#555',
          lineHeight: 1.7,
          marginBottom: '2.5rem',
          maxWidth: 680,
        }}
      >
        Personal accounts from the families and communities connected to these
        memorials. The names and dates are in the records. The stories behind
        them live here.
      </p>

      {stories.length === 0 ? (
        <p style={{ color: '#999', fontStyle: 'italic' }}>
          Stories coming soon.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {stories.map((story) => {
            const linkedMemorials = story.memorial_slugs
              .map((slug) => {
                const m = getMemorialBySlug(slug);
                return m ? { slug, title: m.title } : null;
              })
              .filter(Boolean) as { slug: string; title: string }[];

            return (
              <article
                key={story.slug}
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e0dcd5',
                  borderLeft: '4px solid #8b7355',
                  borderRadius: '0 8px 8px 0',
                  padding: '1.75rem 2rem',
                }}
              >
                <Link
                  href={`/stories/${story.slug}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}
                >
                  <h2
                    style={{
                      fontFamily: "'Helvetica Neue', Arial, sans-serif",
                      color: '#1a2332',
                      fontSize: '1.35rem',
                      marginBottom: '0.25rem',
                      lineHeight: 1.3,
                    }}
                  >
                    {story.title}
                  </h2>
                  {story.subtitle && (
                    <p
                      style={{
                        fontSize: '1rem',
                        color: '#8b7355',
                        fontStyle: 'italic',
                        marginBottom: '0.75rem',
                      }}
                    >
                      {story.subtitle}
                    </p>
                  )}
                </Link>

                <div
                  style={{
                    fontSize: '0.8rem',
                    color: '#999',
                    marginBottom: '0.75rem',
                    fontFamily: "'Helvetica Neue', Arial, sans-serif",
                  }}
                >
                  By {story.author} &middot;{' '}
                  {new Date(story.date).toLocaleDateString('en-GB', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}
                </div>

                <p
                  style={{
                    fontSize: '0.95rem',
                    color: '#444',
                    lineHeight: 1.7,
                    marginBottom: '1rem',
                  }}
                >
                  {story.summary}
                </p>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '0.75rem',
                  }}
                >
                  <Link
                    href={`/stories/${story.slug}`}
                    style={{
                      color: '#7a4500',
                      fontSize: '0.9rem',
                      fontWeight: 600,
                      textDecoration: 'none',
                      fontFamily: "'Helvetica Neue', Arial, sans-serif",
                    }}
                  >
                    Read the full story &rarr;
                  </Link>

                  {linkedMemorials.length > 0 && (
                    <div
                      style={{
                        display: 'flex',
                        gap: '0.5rem',
                        flexWrap: 'wrap',
                      }}
                    >
                      {linkedMemorials.map((m) => (
                        <Link
                          key={m.slug}
                          href={`/memorial/${m.slug}`}
                          style={{
                            fontSize: '0.75rem',
                            padding: '0.2rem 0.6rem',
                            borderRadius: 10,
                            backgroundColor: '#1a2332',
                            color: '#c9b98a',
                            textDecoration: 'none',
                            fontFamily: "'Helvetica Neue', Arial, sans-serif",
                            textTransform: 'uppercase',
                            letterSpacing: '0.03em',
                          }}
                        >
                          {m.title}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* CTA */}
      <section
        style={{
          marginTop: '3rem',
          padding: '1.5rem 2rem',
          backgroundColor: '#f8f6f2',
          border: '1px solid #e0dcd5',
          borderRadius: 8,
          textAlign: 'center',
        }}
      >
        <p
          style={{
            fontSize: '1rem',
            color: '#555',
            marginBottom: '0.75rem',
            lineHeight: 1.6,
          }}
        >
          Do you have a story connected to a Bomber Command memorial? We would
          love to hear it.
        </p>
        <a
          href="mailto:admin@bombermemorial.co.uk?subject=Story%20submission&body=Please%20tell%20us%20your%20story%20and%20which%20memorial%20it%20relates%20to%3A%0A%0A"
          style={{
            display: 'inline-block',
            padding: '0.6rem 1.5rem',
            backgroundColor: '#1a2332',
            color: '#c9b98a',
            borderRadius: 6,
            fontSize: '0.9rem',
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            textDecoration: 'none',
          }}
        >
          Share your story
        </a>
      </section>
    </div>
  );
}

const h1Style: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: '#1a2332',
  fontSize: '2rem',
  marginBottom: '0.75rem',
  lineHeight: 1.2,
};
