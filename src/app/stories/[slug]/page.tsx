import { Metadata } from 'next';
import Link from 'next/link';
import { getAllStorySlugs, getStoryBySlug } from '@/lib/stories';
import { getMemorialBySlug } from '@/lib/data';

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  const slugs = getAllStorySlugs();
  return slugs.map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const story = await getStoryBySlug(params.slug);
  if (!story) return { title: 'Story Not Found' };

  return {
    title: `${story.title} | Stories | Bomber Command Memorial Register`,
    description: story.summary,
    openGraph: {
      title: story.title,
      description: story.summary,
      type: 'article',
      url: `https://bombermemorial.co.uk/stories/${params.slug}`,
      ...(story.date && { publishedTime: story.date }),
    },
  };
}

export default async function StoryPage({ params }: Props) {
  const story = await getStoryBySlug(params.slug);

  if (!story) {
    return (
      <div
        style={{
          maxWidth: 800,
          margin: '4rem auto',
          padding: '0 1.5rem',
          textAlign: 'center',
        }}
      >
        <h1
          style={{
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
            color: '#1a2332',
          }}
        >
          Story Not Found
        </h1>
        <p>The story you are looking for could not be found.</p>
        <Link href="/stories" style={{ color: '#7a4500' }}>
          Back to Stories
        </Link>
      </div>
    );
  }

  const linkedMemorials = story.memorial_slugs
    .map((slug) => {
      const m = getMemorialBySlug(slug);
      return m ? { slug, title: m.title, aircraft_type: m.aircraft_type } : null;
    })
    .filter(Boolean) as {
    slug: string;
    title: string;
    aircraft_type?: string;
  }[];

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: story.title,
    description: story.summary,
    author: { '@type': 'Person', name: story.author },
    datePublished: story.date,
    url: `https://bombermemorial.co.uk/stories/${params.slug}`,
    publisher: {
      '@type': 'Organization',
      name: 'Bomber Command Memorial Register',
      url: 'https://bombermemorial.co.uk',
    },
  };

  return (
    <div data-pagefind-body="" style={{ maxWidth: 760, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Breadcrumb */}
      <nav style={{ marginBottom: '1.5rem', fontSize: '0.85rem' }}>
        <Link href="/" style={{ color: '#7a4500' }}>
          Home
        </Link>
        <span style={{ color: '#999', margin: '0 0.5rem' }}>/</span>
        <Link href="/stories" style={{ color: '#7a4500' }}>
          Stories
        </Link>
        <span style={{ color: '#999', margin: '0 0.5rem' }}>/</span>
        <span style={{ color: '#999' }}>{story.title}</span>
      </nav>

      {/* Header */}
      <header style={{ marginBottom: '2.5rem' }}>
        <h1 data-pagefind-meta="title" style={h1Style}>
          {story.title}
        </h1>
        {story.subtitle && (
          <p
            style={{
              fontSize: '1.15rem',
              color: '#8b7355',
              fontStyle: 'italic',
              marginBottom: '0.75rem',
              lineHeight: 1.4,
            }}
          >
            {story.subtitle}
          </p>
        )}
        <div
          style={{
            fontSize: '0.85rem',
            color: '#999',
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
      </header>

      {/* Linked memorial badges */}
      {linkedMemorials.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: '0.75rem',
            flexWrap: 'wrap',
            marginBottom: '2rem',
          }}
        >
          {linkedMemorials.map((m) => (
            <Link
              key={m.slug}
              href={`/memorial/${m.slug}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.4rem 0.85rem',
                backgroundColor: '#1a2332',
                color: '#c9b98a',
                borderRadius: 6,
                fontSize: '0.8rem',
                fontFamily: "'Helvetica Neue', Arial, sans-serif",
                textDecoration: 'none',
                letterSpacing: '0.02em',
              }}
            >
              <span style={{ fontSize: '0.7rem', opacity: 0.6 }}>MEMORIAL</span>
              {m.title}
            </Link>
          ))}
        </div>
      )}

      {/* Attribution */}
      <div
        style={{
          padding: '1rem 1.5rem',
          backgroundColor: '#f8f6f2',
          borderLeft: '4px solid #8b7355',
          borderRadius: '0 8px 8px 0',
          marginBottom: '2rem',
          fontSize: '0.95rem',
          color: '#555',
          fontStyle: 'italic',
        }}
      >
        With sincere thanks to {story.author} for sharing their story.
      </div>

      {/* Story content */}
      <article
        className="story-content"
        style={{
          lineHeight: 1.85,
          fontSize: '1.05rem',
          color: '#333',
        }}
        dangerouslySetInnerHTML={{ __html: story.contentHtml }}
      />

      {/* Memorial links at bottom */}
      {linkedMemorials.length > 0 && (
        <section
          style={{
            marginTop: '3rem',
            paddingTop: '2rem',
            borderTop: '2px solid #e0dcd5',
          }}
        >
          <h2 style={sectionHeading}>
            Related Memorial{linkedMemorials.length > 1 ? 's' : ''}
          </h2>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            {linkedMemorials.map((m) => (
              <Link
                key={m.slug}
                href={`/memorial/${m.slug}`}
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                <div
                  style={{
                    backgroundColor: '#f8f6f2',
                    borderLeft: '4px solid #7a4500',
                    borderRadius: '0 8px 8px 0',
                    padding: '1rem 1.25rem',
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'Helvetica Neue', Arial, sans-serif",
                      color: '#1a2332',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                    }}
                  >
                    {m.title}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>
                    View the full memorial record &rarr;
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Back to stories */}
      <div style={{ marginTop: '2.5rem' }}>
        <Link
          href="/stories"
          style={{
            color: '#7a4500',
            fontSize: '0.9rem',
            fontFamily: "'Helvetica Neue', Arial, sans-serif",
          }}
        >
          &larr; All stories
        </Link>
      </div>
    </div>
  );
}

const h1Style: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: '#1a2332',
  fontSize: '2.25rem',
  marginBottom: '0.5rem',
  lineHeight: 1.2,
};

const sectionHeading: React.CSSProperties = {
  fontFamily: "'Helvetica Neue', Arial, sans-serif",
  color: '#1a2332',
  fontSize: '1.25rem',
  marginBottom: '1rem',
  paddingBottom: '0.5rem',
  borderBottom: '2px solid #e0dcd5',
};
