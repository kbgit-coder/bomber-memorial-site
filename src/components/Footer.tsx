import Link from "next/link";

export default function Footer() {
  return (
    <footer
      style={{
        backgroundColor: "#1a2332",
        borderTop: "3px solid #8b7355",
        color: "#c9b98a",
        marginTop: "4rem",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "2.5rem 1.5rem",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          gap: "2rem",
        }}
      >
        <div>
          <h3
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#c9b98a",
              fontSize: "1rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: "0.75rem",
            }}
          >
            Bomber Command Memorial Register
          </h3>
          <p
            style={{
              fontSize: "0.875rem",
              color: "rgba(201, 185, 138, 0.7)",
              lineHeight: 1.6,
            }}
          >
            Honouring the memorials, crash sites, and aircrew of RAF Bomber
            Command, 1939&ndash;1945. We will remember them.
          </p>
        </div>
        <div>
          <h4
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#c9b98a",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: "0.75rem",
            }}
          >
            Navigate
          </h4>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            <Link
              href="/"
              style={{
                color: "rgba(201, 185, 138, 0.7)",
                fontSize: "0.875rem",
                textDecoration: "none",
              }}
            >
              Home
            </Link>
            <Link
              href="/faq"
              style={{
                color: "rgba(201, 185, 138, 0.7)",
                fontSize: "0.875rem",
                textDecoration: "none",
              }}
            >
              FAQ
            </Link>
            <Link
              href="/contact"
              style={{
                color: "rgba(201, 185, 138, 0.7)",
                fontSize: "0.875rem",
                textDecoration: "none",
              }}
            >
              Contact
            </Link>
            <Link
              href="/terms"
              style={{
                color: "rgba(201, 185, 138, 0.7)",
                fontSize: "0.875rem",
                textDecoration: "none",
              }}
            >
              Site Terms
            </Link>
          </div>
        </div>
        <div>
          <h4
            style={{
              fontFamily: "'Helvetica Neue', Arial, sans-serif",
              color: "#c9b98a",
              fontSize: "0.875rem",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginBottom: "0.75rem",
            }}
          >
            Contribute
          </h4>
          <p
            style={{
              fontSize: "0.875rem",
              color: "rgba(201, 185, 138, 0.7)",
              lineHeight: 1.6,
            }}
          >
            Know of a memorial not listed here? Have photographs, crew details,
            or corrections? We welcome contributions from researchers, families,
            and enthusiasts. Contact us at{" "}
            <a
              href="mailto:admin@bombermemorial.co.uk"
              style={{ color: "#c9b98a" }}
            >
              admin@bombermemorial.co.uk
            </a>
            .
          </p>
        </div>
      </div>
      <div
        style={{
          borderTop: "1px solid rgba(139, 115, 85, 0.3)",
          padding: "1rem 1.5rem",
          textAlign: "center",
          fontSize: "0.8rem",
          color: "rgba(201, 185, 138, 0.5)",
        }}
      >
        &copy; {new Date().getFullYear()} Bomber Command Memorial Register. All
        rights reserved.
      </div>
    </footer>
  );
}
