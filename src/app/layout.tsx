import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PostHogProvider from "@/components/PostHogProvider";

export const metadata: Metadata = {
  title: {
    default: "Bomber Command Memorial Register",
    template: "%s | Bomber Command Memorial Register",
  },
  description:
    "A digital register honouring the memorials, crash sites, and crew of RAF Bomber Command during the Second World War.",
  keywords: [
    "Bomber Command",
    "WW2",
    "RAF",
    "memorial",
    "Second World War",
    "aircrew",
    "remembrance",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              "name": "Bomber Command Memorial Register",
              "url": "https://bombermemorial.co.uk",
              "description": "A digital register honouring the memorials, crash sites, and crew of RAF Bomber Command during the Second World War.",
              "publisher": {
                "@type": "Organization",
                "name": "Bomber Command Memorial Register",
                "url": "https://bombermemorial.co.uk"
              },
              "potentialAction": {
                "@type": "SearchAction",
                "target": "https://bombermemorial.co.uk/search?q={search_term_string}",
                "query-input": "required name=search_term_string"
              }
            }),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Dataset",
              "name": "Bomber Command Memorial Register",
              "description": "Database of 400+ WW2 Bomber Command memorials, crash sites, and crew records across the United Kingdom and Europe.",
              "url": "https://bombermemorial.co.uk",
              "license": "https://opendatacommons.org/licenses/odbl/",
              "creator": {
                "@type": "Organization",
                "name": "Bomber Command Memorial Register"
              },
              "temporalCoverage": "1939/1945",
              "spatialCoverage": {
                "@type": "Place",
                "name": "United Kingdom and Europe"
              },
              "keywords": ["WW2", "Bomber Command", "RAF", "memorial", "crash site", "aircrew", "Second World War"]
            }),
          }}
        />
      </head>
      <body>
        <PostHogProvider>
          <Header />
          <main style={{ minHeight: "calc(100vh - 200px)" }}>{children}</main>
          <Footer />
        </PostHogProvider>
      </body>
    </html>
  );
}
