#!/usr/bin/env python3
"""
Scrape provenance log module for Bomber Memorial.

Central domain-level provenance tracking for all scraping activity.
Reads/writes public/data/governance/scrape-provenance.json.

Usage:
    from scrape_provenance import ProvenanceLog

    log = ProvenanceLog()
    log.record_scrape("aircrewremembered.com", {
        "pages_attempted": 46,
        "pages_succeeded": 45,
        "full_narratives_extracted": 45,
        "script": "scripts/batch-scrape-aircrew.py",
        "output": "/tmp/aircrew-scraped-all.json",
        "notes": "1 page timeout"
    })
    log.save()
"""

import hashlib
import json
import os
from datetime import datetime, timezone

# Resolve relative to this script's location (scripts/ dir)
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
DEFAULT_PROVENANCE_PATH = os.path.join(
    _REPO_ROOT, "public", "data", "governance", "scrape-provenance.json"
)

# Domains known to block bots
BOT_BLOCKED_DOMAINS = [
    "www.tracesofwar.com",
    "www.americanairmuseum.com",
    "www.peakdistrict.gov.uk",
    "www.dartmoor.gov.uk",
    "www.raf.mod.uk",
]

# Monitor schedule defaults
DEFAULT_MONITOR_SCHEDULE = {
    "weekly": [],
    "monthly": ["squadron_association", "remembrance_site"],
    "quarterly": ["heritage_archive", "institutional"],
    "annually": ["encyclopedia", "photo_archive", "static_reference"],
}

# Domain type → monitor frequency mapping
TYPE_TO_FREQUENCY = {
    "squadron_association": "monthly",
    "remembrance_site": "monthly",
    "heritage_archive": "quarterly",
    "institutional": "quarterly",
    "crash_investigation": "quarterly",
    "military_records": "quarterly",
    "encyclopedia": "annually",
    "photo_archive": "annually",
    "news_archive": "annually",
    "community_heritage": "quarterly",
    "static_reference": "annually",
    "unknown": "annually",
}


def content_hash(text: str) -> str:
    """SHA-256 hash of text content for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def classify_domain_type(domain: str, name: str = "") -> str:
    """Heuristic classification of domain type from domain name."""
    d = domain.lower()
    n = name.lower()
    combined = f"{d} {n}"

    if any(k in combined for k in ["squadron", "association", "sqn"]):
        return "squadron_association"
    if any(k in combined for k in ["iwm", "museum", "imperial war"]):
        return "institutional"
    if any(k in combined for k in ["cwgc", "commonwealth war graves"]):
        return "military_records"
    if any(k in combined for k in ["wikipedia", "wiki"]):
        return "encyclopedia"
    if any(k in combined for k in ["geograph", "flickr", "photo"]):
        return "photo_archive"
    if any(k in combined for k in ["aviation-safety", "asn.flightsafety", "crash", "baaa"]):
        return "crash_investigation"
    if any(k in combined for k in ["warmemorial", "war memorial", "remembrance", "memorial"]):
        return "remembrance_site"
    if any(k in combined for k in ["heritage", "archive", "history", "hist"]):
        return "heritage_archive"
    if any(k in combined for k in ["news", "telegraph", "advertiser", "gazette", "mercury", "herald"]):
        return "news_archive"
    if any(k in combined for k in ["parish", "council", "gov.uk", "community"]):
        return "community_heritage"
    if any(k in combined for k in ["findagrave", "roll-of-honour", "rollofhonour"]):
        return "military_records"
    return "unknown"


def infer_change_frequency(domain_type: str) -> str:
    """Infer how often content likely changes based on domain type."""
    freq_map = {
        "squadron_association": "annual_events",
        "remembrance_site": "annual_events",
        "heritage_archive": "rare",
        "institutional": "rare",
        "crash_investigation": "rare",
        "military_records": "rare",
        "encyclopedia": "occasional",
        "photo_archive": "rare",
        "news_archive": "static",
        "community_heritage": "occasional",
        "static_reference": "static",
    }
    return freq_map.get(domain_type, "unknown")


class ProvenanceLog:
    """Read/write/update the scrape provenance log."""

    def __init__(self, path: str = DEFAULT_PROVENANCE_PATH):
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                self._data = json.load(f)
        else:
            self._data = {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "domains": {},
                "bot_blocked_domains": BOT_BLOCKED_DOMAINS,
                "monitor_schedule": DEFAULT_MONITOR_SCHEDULE,
            }

    @property
    def domains(self) -> dict:
        return self._data["domains"]

    def domain_count(self) -> int:
        return len(self._data["domains"])

    def get_domain(self, domain: str) -> dict | None:
        """Get a domain entry, trying with and without www. prefix."""
        key = domain.replace("www.", "")
        return self._data["domains"].get(key)

    def add_domain(
        self,
        domain: str,
        display_name: str = "",
        domain_type: str = "",
        scrape_method: str = "",
        access: str = "public_http",
        bot_policy: str = "unknown",
        memorials_linked: int = 0,
        entries_with_full_text: int = 0,
        content_type: str = "",
        source_tier: str = "",
    ) -> dict:
        """Add or update a domain entry in the provenance log."""
        key = domain.replace("www.", "")
        if not domain_type:
            domain_type = classify_domain_type(domain, display_name)
        if not display_name:
            display_name = key.replace("-", " ").replace(".", " ").title()

        change_freq = infer_change_frequency(domain_type)
        monitor_priority = TYPE_TO_FREQUENCY.get(domain_type, "annually")

        entry = self._data["domains"].get(key, {})
        entry.update({
            "display_name": display_name or entry.get("display_name", ""),
            "domain": domain,
            "type": domain_type,
            "source_tier": source_tier or entry.get("source_tier", ""),
            "scrape_method": scrape_method or entry.get("scrape_method", ""),
            "access": access,
            "bot_policy": bot_policy,
            "scrape_history": entry.get("scrape_history", []),
            "memorials_linked": memorials_linked or entry.get("memorials_linked", 0),
            "entries_with_full_text": entries_with_full_text or entry.get("entries_with_full_text", 0),
            "content_type": content_type or entry.get("content_type", ""),
            "change_frequency": change_freq,
            "monitor_priority": monitor_priority,
            "last_checked": entry.get("last_checked"),
            "last_change_detected": entry.get("last_change_detected"),
        })
        self._data["domains"][key] = entry
        return entry

    def record_scrape(
        self,
        domain: str,
        run_data: dict,
    ) -> dict:
        """
        Record a scrape run against a domain.

        run_data should contain:
            pages_attempted: int
            pages_succeeded: int
            full_narratives_extracted: int (optional)
            script: str
            output: str (optional)
            notes: str (optional)
            content_hashes: dict[url, hash] (optional, for change detection)
            changes_detected: int (optional)
        """
        key = domain.replace("www.", "")
        if key not in self._data["domains"]:
            self.add_domain(domain)

        entry = self._data["domains"][key]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        history_record = {
            "date": today,
            "pages_attempted": run_data.get("pages_attempted", 0),
            "pages_succeeded": run_data.get("pages_succeeded", 0),
            "script": run_data.get("script", ""),
        }

        # Optional fields — only include if provided
        for field in [
            "full_narratives_extracted",
            "output",
            "notes",
            "changes_detected",
        ]:
            if field in run_data:
                history_record[field] = run_data[field]

        entry["scrape_history"].append(history_record)
        entry["last_checked"] = today

        # Update full text count if provided
        if "full_narratives_extracted" in run_data:
            entry["entries_with_full_text"] = (
                entry.get("entries_with_full_text", 0)
                + run_data["full_narratives_extracted"]
            )

        # Update memorials linked if provided
        if "memorials_linked" in run_data:
            entry["memorials_linked"] = run_data["memorials_linked"]

        return history_record

    def update_domain_stats(
        self, domain: str, memorials_linked: int = 0, entries_with_full_text: int = 0
    ):
        """Update the current stats for a domain (typically after injection)."""
        key = domain.replace("www.", "")
        if key not in self._data["domains"]:
            return
        if memorials_linked:
            self._data["domains"][key]["memorials_linked"] = memorials_linked
        if entries_with_full_text:
            self._data["domains"][key]["entries_with_full_text"] = entries_with_full_text

    def mark_bot_blocked(self, domain: str):
        """Mark a domain as bot-blocked."""
        key = domain.replace("www.", "")
        if key in self._data["domains"]:
            self._data["domains"][key]["bot_policy"] = "blocked"
            self._data["domains"][key]["access"] = "blocked"
        if domain not in self._data["bot_blocked_domains"]:
            self._data["bot_blocked_domains"].append(domain)

    def get_unscraped_domains(self) -> list[str]:
        """Return domains that have entries but no scrape history."""
        return [
            k for k, v in self._data["domains"].items()
            if not v.get("scrape_history")
        ]

    def get_stale_domains(self, days: int = 90) -> list[str]:
        """Return domains not checked in the given number of days."""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        stale = []
        for key, entry in self._data["domains"].items():
            last = entry.get("last_checked")
            if not last or last < cutoff:
                stale.append(key)
        return stale

    def summary(self) -> dict:
        """Return a summary of the provenance log state."""
        domains = self._data["domains"]
        scraped = sum(1 for v in domains.values() if v.get("scrape_history"))
        total_entries = sum(v.get("entries_with_full_text", 0) for v in domains.values())
        blocked = len(self._data.get("bot_blocked_domains", []))
        return {
            "total_domains": len(domains),
            "domains_with_scrape_history": scraped,
            "domains_never_scraped": len(domains) - scraped,
            "total_full_text_entries": total_entries,
            "bot_blocked_domains": blocked,
        }

    def save(self):
        """Write the provenance log to disk."""
        self._data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Sort domains alphabetically for readability
        self._data["domains"] = dict(
            sorted(self._data["domains"].items())
        )

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def __repr__(self):
        s = self.summary()
        return (
            f"ProvenanceLog({s['total_domains']} domains, "
            f"{s['domains_with_scrape_history']} scraped, "
            f"{s['bot_blocked_domains']} blocked)"
        )
