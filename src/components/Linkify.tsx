import React from "react";

// Turns bare domains and http(s) URLs in plain narrative text into external links.
const URL_RE = /\b((?:https?:\/\/)?(?:[a-z0-9-]+\.)+(?:com|co\.uk|org\.uk|org|net)(?:\/[^\s,)]*)?)/gi;

export default function Linkify({ text }: { text: string }) {
  const parts = text.split(URL_RE);
  return (
    <>
      {parts.map((part, i) => {
        if (i % 2 === 0) return part;
        const trimmed = part.replace(/[.;:]+$/, "");
        const href = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
        return (
          <React.Fragment key={i}>
            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#7a4500" }}>
              {trimmed}
            </a>
            {part.slice(trimmed.length)}
          </React.Fragment>
        );
      })}
    </>
  );
}
