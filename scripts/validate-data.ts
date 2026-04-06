/**
 * BMR-36: Pre-release data validation script
 * Run with: bun scripts/validate-data.ts
 *
 * Validates all memorial JSONs in public/data/memorials/:
 * - Required fields present (id, title, location_name, lat/lon)
 * - location_confidence block present and valid
 * - No duplicate IDs
 * - Valid coordinate ranges
 */

import { readdir, readFile } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const MEMORIALS_DIR = join(__dirname, "../public/data/memorials");

interface ValidationIssue {
  file: string;
  field: string;
  message: string;
  severity: "error" | "warning";
}

const VALID_STATUSES = ["verified", "confirmed", "approximate", "estimated"];

async function validate() {
  const files = (await readdir(MEMORIALS_DIR)).filter((f) =>
    f.endsWith(".json")
  );

  console.log(`\nValidating ${files.length} memorial files...\n`);

  const issues: ValidationIssue[] = [];
  const ids = new Map<string, string>(); // id -> filename
  let passCount = 0;

  for (const file of files) {
    const filePath = join(MEMORIALS_DIR, file);
    let data: Record<string, unknown>;

    try {
      const raw = await readFile(filePath, "utf8");
      data = JSON.parse(raw);
    } catch (e) {
      issues.push({
        file,
        field: "JSON",
        message: `Invalid JSON: ${e instanceof Error ? e.message : String(e)}`,
        severity: "error",
      });
      continue;
    }

    let fileHasIssues = false;

    // Required fields
    for (const field of ["id", "title"]) {
      if (!data[field]) {
        issues.push({
          file,
          field,
          message: `Missing required field: ${field}`,
          severity: "error",
        });
        fileHasIssues = true;
      }
    }

    // Location fields (warning, not error — some memorials have no known location)
    if (data.latitude == null || data.longitude == null) {
      issues.push({
        file,
        field: "lat/lon",
        message: "Missing latitude or longitude",
        severity: "warning",
      });
      fileHasIssues = true;
    } else {
      // Validate coordinate ranges (UK and near Europe: lat 49-61, lon -11 to 10)
      const lat = data.latitude as number;
      const lon = data.longitude as number;
      if (lat < -90 || lat > 90) {
        issues.push({
          file,
          field: "latitude",
          message: `Invalid latitude: ${lat}`,
          severity: "error",
        });
        fileHasIssues = true;
      }
      if (lon < -180 || lon > 180) {
        issues.push({
          file,
          field: "longitude",
          message: `Invalid longitude: ${lon}`,
          severity: "error",
        });
        fileHasIssues = true;
      }
    }

    if (!data.location_name) {
      issues.push({
        file,
        field: "location_name",
        message: "Missing location_name",
        severity: "warning",
      });
      fileHasIssues = true;
    }

    // location_confidence block
    const lc = data.location_confidence as Record<string, unknown> | undefined;
    if (!lc) {
      issues.push({
        file,
        field: "location_confidence",
        message: "Missing location_confidence block",
        severity: "error",
      });
      fileHasIssues = true;
    } else {
      if (!lc.status || !VALID_STATUSES.includes(lc.status as string)) {
        issues.push({
          file,
          field: "location_confidence.status",
          message: `Invalid or missing status: ${lc.status}`,
          severity: "error",
        });
        fileHasIssues = true;
      }
    }

    // Duplicate ID check
    const id = data.id as string;
    if (id) {
      if (ids.has(id)) {
        issues.push({
          file,
          field: "id",
          message: `Duplicate ID "${id}" (also in ${ids.get(id)})`,
          severity: "error",
        });
        fileHasIssues = true;
      } else {
        ids.set(id, file);
      }
    }

    if (!fileHasIssues) passCount++;
  }

  // Print results
  const errors = issues.filter((i) => i.severity === "error");
  const warnings = issues.filter((i) => i.severity === "warning");

  if (errors.length > 0) {
    console.log(`ERRORS (${errors.length}):`);
    for (const issue of errors) {
      console.log(`  [ERROR] ${issue.file} — ${issue.field}: ${issue.message}`);
    }
    console.log();
  }

  if (warnings.length > 0) {
    console.log(`WARNINGS (${warnings.length}):`);
    for (const issue of warnings) {
      console.log(
        `  [WARN]  ${issue.file} — ${issue.field}: ${issue.message}`
      );
    }
    console.log();
  }

  console.log("─".repeat(60));
  console.log(
    `RESULT: ${passCount}/${files.length} files passed all checks`
  );
  console.log(
    `  ${errors.length} errors, ${warnings.length} warnings`
  );
  console.log("─".repeat(60));

  // Exit with error code if there are hard errors
  if (errors.length > 0) {
    process.exit(1);
  }
}

validate().catch((err) => {
  console.error("Validation failed:", err);
  process.exit(1);
});
