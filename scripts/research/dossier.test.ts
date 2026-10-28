import { describe, expect, test } from "bun:test";
import { validate, crosscheck, apply, quality, type Dossier } from "./dossier";

const base = (): Dossier => ({
  memorial_id: "test-memorial", researched_at: "2026-10-28", custodian_status: "known",
  searches: [{ query: "Halifax X1 crash", useful: true }],
  sources: [
    { id: "S1", url: "https://losses.internationalbcc.co.uk/loss/1", title: "IBCC", publisher: "IBCC", tier: "institutional", retrieved: "2026-10-28" },
    { id: "S2", url: "https://www.cwgc.org/x", title: "CWGC", publisher: "CWGC", tier: "official", retrieved: "2026-10-28" },
    { id: "S3", url: "https://local.example.org/story", title: "Local", publisher: "Local Society", tier: "researched", retrieved: "2026-10-28", summary: "The story." },
    { id: "S4", url: "https://local.example.org/other", title: "Local 2", publisher: "Local Society", tier: "researched", retrieved: "2026-10-28" },
    { id: "S5", url: "https://forum.example.com/t/1", title: "Forum", publisher: "Some Forum", tier: "community", retrieved: "2026-10-28" },
  ],
  claims: [
    { id: "C1", field: "crew.name", person: "smith", value: "John Albert Smith", sources: ["S1"] },
    { id: "C2", field: "crew.name", person: "smith", value: "J. Smith", sources: ["S2"] },
    { id: "C3", field: "crew.age", person: "smith", value: 21, sources: ["S1"] },
    { id: "C4", field: "crew.role", person: "smith", value: "Pilot", sources: ["S3"] },
    { id: "C5", field: "squadron", value: "1658 HCU", sources: ["S1", "S3"] },
  ],
  paragraphs: [{ section: "narrative", text: "Sgt Smith flew from Hurn.", cites: ["C1", "C5"] }],
});

describe("crosscheck", () => {
  test("name variants agreeing on initial + surname corroborate, fullest spelling kept", () => {
    const g = crosscheck(base()).find(g => g.field === "crew.name")!;
    expect(g.status).toBe("corroborated");
    expect(g.accepted).toBe("John Albert Smith");
  });

  test("two pages from the same publisher are one source, not two", () => {
    const d = base();
    d.claims.push({ id: "C9", field: "station", value: "Hurn", sources: ["S3", "S4"] });
    const g = crosscheck(d).find(g => g.field === "station")!;
    expect(g.status).toBe("single");
    expect(g.values[0].publishers).toEqual(["local society"]);
  });

  test("a planted conflict is marked conflict; resolved only by a unique higher tier", () => {
    const d = base();
    d.claims.push({ id: "C10", field: "crew.age", person: "smith", value: 22, sources: ["S3"] });
    const g = crosscheck(d).find(g => g.field === "crew.age")!;
    expect(g.status).toBe("conflict");
    expect(g.accepted).toBe(21); // IBCC (institutional) beats local (researched)
  });

  test("conflicting cause of loss is never auto-resolved", () => {
    const d = base();
    d.claims.push({ id: "C11", field: "cause_of_loss", value: "Icing", sources: ["S1"] });
    d.claims.push({ id: "C12", field: "cause_of_loss", value: "Lightning strike", sources: ["S3"] });
    const g = crosscheck(d).find(g => g.field === "cause_of_loss")!;
    expect(g.status).toBe("conflict");
    expect(g.accepted).toBeUndefined();
  });

  test("event claims never conflict with each other and never reach a record field", () => {
    const d = base();
    d.claims.push({ id: "E1", field: "event", value: "Took off 02:30", sources: ["S1"] }, { id: "E2", field: "event", value: "Took off 02:50", sources: ["S3"] });
    d.paragraphs.push({ section: "narrative", text: "Sources give 02:30 and 02:50.", cites: ["E1", "E2"] });
    expect(crosscheck(d).filter(g => g.field === "event").every(g => g.status === "single")).toBe(true);
    expect(validate(d)).toEqual([]);
    expect(apply(d, { id: "t", crew: [], sources: [] }).record.event).toBeUndefined();
  });

  test("a single community-tier fact is held back", () => {
    const d = base();
    d.claims.push({ id: "C13", field: "erected_by", value: "Someone", sources: ["S5"] });
    const g = crosscheck(d).find(g => g.field === "erected_by")!;
    expect(g.accepted).toBeUndefined();
  });
});

describe("validate", () => {
  test("a clean dossier passes", () => expect(validate(base())).toEqual([]));

  test("a claim with no source fails", () => {
    const d = base(); d.claims.push({ id: "C20", field: "station", value: "Hurn", sources: [] });
    expect(validate(d).join()).toContain("no sources");
  });

  test("a paragraph citing nothing fails", () => {
    const d = base(); d.paragraphs.push({ section: "narrative", text: "Unsourced.", cites: [] });
    expect(validate(d).join()).toContain("cites no claims");
  });

  test("a paragraph citing a conflicted claim fails unless it presents the conflict", () => {
    const d = base();
    d.claims.push({ id: "C21", field: "cause_of_loss", value: "Icing", sources: ["S1"] }, { id: "C22", field: "cause_of_loss", value: "Lightning", sources: ["S3"] });
    d.paragraphs.push({ section: "narrative", text: "It was icing.", cites: ["C21"] });
    expect(validate(d).join()).toContain("conflicted claim");
    d.paragraphs[1].presents_conflict = true;
    expect(validate(d)).toEqual([]);
  });

  test("non-ISO dates and http links fail", () => {
    const d = base();
    d.claims.push({ id: "C23", field: "crash_date", value: "21 March 1944", sources: ["S1"] }, { id: "C24", field: "crew.ibcc_url", person: "smith", value: "http://x", sources: ["S1"] });
    const e = validate(d).join();
    expect(e).toContain("YYYY-MM-DD");
    expect(e).toContain("https");
  });
});

describe("apply", () => {
  const record = () => ({ id: "test-memorial", crew: [{ name: "Peter Jones", role: "Air Gunner" }], sources: [], external_narratives: [], data_quality: "Comprehensive", narrative_source: "generated-claude-sonnet" });

  test("held-back and conflicted facts never reach the record", () => {
    const d = base();
    d.claims.push({ id: "C30", field: "erected_by", value: "Forum Claim", sources: ["S5"] });
    d.claims.push({ id: "C31", field: "cause_of_loss", value: "Icing", sources: ["S1"] }, { id: "C32", field: "cause_of_loss", value: "Lightning", sources: ["S3"] });
    const r = apply(d, record()).record;
    expect(r.erected_by).toBeUndefined();
    expect(r.cause_of_loss).toBeUndefined();
  });

  test("accepted crew merge with existing crew; nobody is dropped", () => {
    const r = apply(base(), record()).record;
    expect(r.crew.map((c: any) => c.name)).toEqual(["John Albert Smith", "Peter Jones"]);
    expect(r.crew[0].age).toBe(21);
  });

  test("every source an applied fact rests on is recorded; unused sources are not", () => {
    const r = apply(base(), record()).record;
    const urls = r.sources.map((s: any) => s.url);
    expect(urls).toContain("https://losses.internationalbcc.co.uk/loss/1");
    expect(urls).not.toContain("https://forum.example.com/t/1");
    expect(r.external_narratives[0].original_url).toBe("https://local.example.org/story");
  });

  test("retractions remove unsupported content; a sourced fact for the field still lands", () => {
    const d = base();
    d.retractions = [{ field: "maintainer.organisation", reason: "no source" }, { field: "local_contacts", reason: "no source" }, { field: "squadron", reason: "wrong" }];
    const r = apply(d, { ...record(), maintainer: { organisation: "Invented Body" }, local_contacts: [{ org_name: "X" }], squadron: "Bomber Command" }).record;
    expect(r.maintainer).toBeUndefined();
    expect(r.local_contacts).toEqual([]);
    expect(r.squadron).toBe("1658 HCU");
  });

  test("retracting crew is refused by validation", () => {
    const d = base(); d.retractions = [{ field: "crew", reason: "x" }];
    expect(validate(d).join()).toContain("cannot be retracted");
  });

  test("model-written narrative is replaced and relabelled", () => {
    const r = apply(base(), record()).record;
    expect(r.narrative).toBe("Sgt Smith flew from Hurn.");
    expect(r.narrative_source).toBe("researched-dossier");
  });
});

describe("quality", () => {
  test("no photo means Partial, however good the rest", () => {
    const d = base();
    expect(apply(d, { id: "t", crew: [], sources: [] }).quality).toBe("Partial");
  });

  test("everything present gives Comprehensive", () => {
    const d = base();
    d.photos = [{ url: "https://wmr.iwm.org.uk/sites/default/files/images/x.jpg", credit: "IWM", caption: "The memorial", source_id: "S1" }];
    expect(apply(d, { id: "t", crew: [], sources: [] }).quality).toBe("Comprehensive");
  });

  test("custodian unknown blocks Comprehensive", () => {
    const d = base(); d.custodian_status = "unknown";
    d.photos = [{ url: "https://wmr.iwm.org.uk/sites/default/files/images/x.jpg", credit: "IWM", caption: "c", source_id: "S1" }];
    expect(apply(d, { id: "t", crew: [], sources: [] }).quality).toBe("Partial");
  });

  test("nothing sourced gives Stub", () => {
    const d = base(); d.claims = []; d.paragraphs = [];
    expect(quality({ crew: [] }, d)).toBe("Stub");
  });
});
