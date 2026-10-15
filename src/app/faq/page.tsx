import { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "FAQ",
  description:
    "Frequently asked questions about the Bomber Command Memorial Register.",
};

const faqs: { q: string; a: string[] }[] = [
  {
    q: "What is the Bomber Command Memorial Register?",
    a: [
      "The Bomber Command Memorial Register is a free, non-commercial research project dedicated to documenting every known memorial to RAF Bomber Command aircrew from the Second World War.",
      "Bomber Command suffered one of the highest casualty rates of any branch of the Allied forces. Of the 125,000 men and women who served, 55,573 were killed — a loss rate of 44.4%. Many were very young, drawn from across Britain, the Commonwealth, and the Allied nations.",
      "When institutional commemoration eventually came, it was sixty years late. The real work of remembrance had long been carried by communities: parishes, schools, local historians, and the families of the dead.",
      "This register exists to record those memorials and to tell the human stories behind them: the crew, the crash, the local people who witnessed it, and the connection between village and aircrew that in many places endures to this day.",
    ],
  },
  {
    q: "My relative served in Bomber Command. Can you help me find them?",
    a: [
      "Possibly, yes — and we would genuinely like to try.",
      "If your relative was killed on operations and their crew is commemorated by a memorial anywhere in the UK or further afield, there is a good chance they are already in the register, or that we can point you towards one. Use the search function to look for their name, squadron, aircraft type, or the date of the operation.",
      "If you cannot find them, please get in touch at admin@bombermemorial.co.uk. Sometimes a crew is on our list but not yet fully documented — a family contact can be exactly what an entry needs to come to life.",
      "For broader genealogical research, the Commonwealth War Graves Commission (cwgc.org) holds records for every Commonwealth serviceman and woman killed in the war. The National Archives at Kew holds squadron Operations Record Books (ORBs), and the RAF Museum in Hendon has extensive collections. We can often point you in the right direction.",
    ],
  },
  {
    q: "How do I submit a new memorial or crash site?",
    a: [
      "The easiest way is to use the contact form on our Contact page, or to email us directly at admin@bombermemorial.co.uk.",
      "Tell us as much as you know: the location of the memorial, the aircraft type and serial number, the squadron and date of the operation, the crew names, any photographs you are able to share, and where you found your information.",
      "You do not need to have complete information to submit. We regularly add entries based on a single photograph or a brief mention in a local history book, then build the record up over time. A partial entry is always better than no entry.",
    ],
  },
  {
    q: "What counts as a memorial on this site?",
    a: [
      "We use the word broadly, to include anything erected or maintained specifically to commemorate a Bomber Command aircrew. That covers stone monuments and cairns at or near crash sites, plaques on church walls or public buildings, dedicated graves where crew are buried together, named benches or trees, and formal crash site markers erected by aviation archaeology groups or local councils.",
      "We do not list general war memorials that include Bomber Command names alongside all other services, unless there is something specifically connected to a Bomber Command crew or crash. The focus is always on the local connection — the memorial that exists because of what happened in or near that particular place.",
      "If you are unsure whether something qualifies, contact us. We would rather consider it and say no than miss something worth recording.",
    ],
  },
  {
    q: "Why is an entry marked Stub or Partial?",
    a: [
      "Every entry in the register is rated against our data quality tiers. Comprehensive means the entry has verified crew names, aircraft details, operation date, crash location, memorial photographs, and narrative context. Partial means we have enough to verify the memorial exists and identify the crew, but significant gaps remain. Stub means we know the memorial exists, typically from a single source, but little else is confirmed.",
      "Roughly 40% of entries are currently below full quality. That is not a failing — it reflects how fragmented the historical record is, and how much of what is known lives in people\u2019s heads rather than in archives.",
      "If you have information that could improve a Partial or Stub entry, please get in touch.",
    ],
  },
  {
    q: "I\u2019ve spotted an error. How do I report it?",
    a: [
      "Please tell us. Every memorial page has a \u201cSuggest a correction\u201d link at the bottom — use that, or email us at admin@bombermemorial.co.uk.",
      "Historical records are imperfect. Crew names were sometimes transcribed incorrectly in official documents. Aircraft serial numbers vary between sources. Even CWGC records, which are authoritative, occasionally carry errors inherited from wartime paperwork.",
      "Local communities often know things that no archive holds. We take corrections seriously and will update the record with attribution if you would like it.",
    ],
  },
  {
    q: "Do you cover memorials outside the UK?",
    a: [
      "Yes, increasingly so. While the register began with UK memorials, Bomber Command operations took place across occupied Europe, and memorials were erected in many countries where aircraft came down. Communities in Belgium, the Netherlands, France, Germany, Norway, and elsewhere commemorated the crews who fell near their homes.",
      "We are actively expanding the international sections of the register. If you know of a Bomber Command memorial in another country, we would very much like to hear about it.",
    ],
  },
  {
    q: "Can I use your photos, maps, or research in my own work?",
    a: [
      "It depends on the specific content. Our research and text is published for educational and remembrance purposes. You are welcome to reference, quote, and link to any page. If you want to reproduce substantial portions for a book or publication, please contact us first — we will almost always say yes.",
      "Photographs are a different matter, because most are not ours to license. Images have been contributed by families, local historians, and organisations including the Imperial War Museum and War Memorials Online. Each may carry its own copyright. If you need to use a specific image, contact us and we will connect you with the source where possible.",
      "For anything non-commercial — a local history society, a school, a remembrance event — just ask.",
    ],
  },
  {
    q: "How do you verify the information?",
    a: [
      "We cross-reference multiple sources before publishing or upgrading an entry\u2019s quality tier. Primary sources include the Commonwealth War Graves Commission (CWGC), squadron Operations Record Books (ORBs) held at the National Archives, AIR 81 casualty files, War Memorials Online, and local historians and parish records.",
      "We also rely heavily on submissions from families and community researchers, who frequently have access to letters, photographs, log books, and oral histories that no official archive holds. We note our sources on each entry, and flag where information comes from a single unverified source.",
      "We do not claim perfection. When we have doubts about a detail, we say so rather than present it as fact.",
    ],
  },
  {
    q: "Who runs this project?",
    a: [
      "The register was founded by Keith Binley, a researcher based in Nottinghamshire. The inspiration was a specific memorial near his home in Farnsfield: the monument to the crew of Halifax MZ519 of 578 Squadron, who were killed in 1944 when their aircraft came down nearby.",
      "Speaking with the farmer who had campaigned for the memorial\u2019s erection — a man who, as a boy, had witnessed the crew laid out in the field after the crash — Keith realised that these intensely local stories were at serious risk of being lost as the eyewitness generation passes.",
      "The register is run on a voluntary basis. It is entirely non-commercial — there are no adverts, no subscriptions, and no revenue. Beyond the core team, the project depends on a wide network of local historians, squadron association members, aviation archaeologists, parish councils, and families who contribute photographs, corrections, and research.",
    ],
  },
  {
    q: "Why isn\u2019t my local memorial listed?",
    a: [
      "Almost certainly because we do not know about it yet. There is no comprehensive national inventory of Bomber Command memorials that we can work from. We build ours one entry at a time, through research, community contacts, and submissions from people like you.",
      "If you know of a memorial that is not listed, please submit it using our contact form or email admin@bombermemorial.co.uk. Even a single photograph and a rough location is enough to start an entry.",
    ],
  },
  {
    q: "How can I get involved as a researcher or volunteer?",
    a: [
      "This is genuinely what brings the register to life, and we welcome it. There are several ways to contribute depending on how much time you have.",
      "Photograph memorials near you. If there is an entry near where you live, or a memorial you know that is not yet listed, visiting and photographing it is enormously valuable.",
      "Research a specific entry. If you have a connection to a particular crew, squadron, or area, taking on one or two Stub or Partial entries and working to complete them is a huge contribution.",
      "Submit corrections and additions. If you spot something wrong, or know something we do not, use the \u201cSuggest a correction\u201d link on any memorial page or email us directly.",
      "Share the project. Squadron associations, local history societies, airfield heritage groups, and veterans\u2019 organisations are often sitting on exactly the kind of information we need. If you are a member of any of those communities, telling them about the register can unlock connections we would never find on our own.",
      "To get involved, contact us at admin@bombermemorial.co.uk and tell us a little about your background and what interests you.",
    ],
  },
];

export default function FAQPage() {
  return (
    <div
      data-pagefind-ignore
      style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1.5rem" }}
    >
      <nav style={{ marginBottom: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/" style={{ color: "#7a4500" }}>
          Home
        </Link>
        <span style={{ color: "#999", margin: "0 0.5rem" }}>/</span>
        <span style={{ color: "#999" }}>FAQ</span>
      </nav>

      <h1
        style={{
          fontFamily: "'Helvetica Neue', Arial, sans-serif",
          color: "#1a2332",
          fontSize: "2rem",
          marginBottom: "2rem",
          lineHeight: 1.2,
        }}
      >
        Frequently Asked Questions
      </h1>

      <div
        style={{
          width: 60,
          height: 2,
          backgroundColor: "#8b7355",
          marginBottom: "2rem",
        }}
      />

      <div style={{ lineHeight: 1.8, fontSize: "1.05rem" }}>
        {faqs.map((faq, i) => (
          <details
            key={i}
            style={{
              marginBottom: "1rem",
              borderBottom: "1px solid #e8e0d4",
              paddingBottom: "1rem",
            }}
          >
            <summary
              style={{
                cursor: "pointer",
                fontWeight: 600,
                color: "#1a2332",
                fontSize: "1.1rem",
                padding: "0.5rem 0",
              }}
            >
              {faq.q}
            </summary>
            <div style={{ marginTop: "0.75rem", color: "#444" }}>
              {faq.a.map((para, j) => (
                <p key={j} style={{ marginBottom: "1rem" }}>
                  {para}
                </p>
              ))}
            </div>
          </details>
        ))}
      </div>

      <div
        style={{
          marginTop: "2rem",
          padding: "1.5rem",
          backgroundColor: "#f8f5f0",
          borderRadius: 8,
          fontSize: "0.95rem",
          color: "#555",
          lineHeight: 1.8,
        }}
      >
        If your question is not answered here, please{" "}
        <Link href="/contact" style={{ color: "#7a4500" }}>
          contact us
        </Link>
        . We read every message.
      </div>
    </div>
  );
}
