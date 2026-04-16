import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

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
        <script
          dangerouslySetInnerHTML={{
            __html: `
              !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
              posthog.init('phc_6iC8kWZD8EzWetkwaYvvamfLKo2PrQnLK3y7ADCSz7r', {
                api_host: 'https://eu.i.posthog.com',
                person_profiles: 'identified_only',
                capture_pageview: true,
                capture_pageleave: true,
              });
            `,
          }}
        />
      </head>
      <body>
        <Header />
        <main style={{ minHeight: "calc(100vh - 200px)" }}>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
