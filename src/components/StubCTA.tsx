interface StubCTAProps {
  quality: string;
  title: string;
}

export default function StubCTA({ quality, title }: StubCTAProps) {
  if (quality === "Complete") return null;

  const isStub = quality === "Stub";

  return (
    <div
      style={{
        backgroundColor: isStub ? "#faf6ee" : "#f9f7f4",
        border: `1px solid ${isStub ? "#d4c08c" : "#e0dcd5"}`,
        borderRadius: 8,
        padding: "1.5rem 2rem",
        marginTop: "2rem",
        textAlign: "center",
      }}
    >
      <h3
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "1.1rem",
          marginBottom: "0.75rem",
        }}
      >
        {isStub ? "Help Us Tell This Story" : "Can You Help Complete This Record?"}
      </h3>
      <p
        style={{
          color: "#666",
          fontSize: "0.95rem",
          maxWidth: 600,
          margin: "0 auto 1rem",
          lineHeight: 1.6,
        }}
      >
        {isStub
          ? `We have only basic information about ${title}. If you know about this memorial \u2014 its location, the crew it commemorates, its history, or have photographs \u2014 please get in touch.`
          : `This record for ${title} is partially complete. We\u2019re looking for additional details such as crew information, photographs, narrative history, or source references.`}
      </p>
      <p
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          fontSize: "0.85rem",
          color: "#8b7355",
          fontStyle: "italic",
        }}
      >
        Contact us at{" "}
        <a href="mailto:admin@bombermemorial.co.uk" style={{ color: "#2c5f8a" }}>
          admin@bombermemorial.co.uk
        </a>{" "}
        to contribute information
      </p>
    </div>
  );
}
