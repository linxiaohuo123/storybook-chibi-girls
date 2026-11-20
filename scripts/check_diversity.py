#!/usr/bin/env python3
"""Check exact normalized plan differences; semantic and visual review remain required."""

import argparse
import itertools
import json
import sys
import unicodedata
from pathlib import Path


AXES = ("theme", "hair_style", "hair_color", "outfit_silhouette",
        "signature_prop", "pose", "expression")
STRUCTURE = ("hair_style", "outfit_silhouette", "pose")
REQUIRED = ("id", *AXES, "palette_id")


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def validate_record(record, label):
    if not isinstance(record, dict):
        raise ValueError(f"{label} must be an object")
    missing = [field for field in REQUIRED
               if not isinstance(record.get(field), str) or not record[field].strip()]
    if missing:
        raise ValueError(f"{label} has missing/empty/non-string fields: {', '.join(missing)}")
    return record


def check_ids(records, label):
    seen = set()
    for record in records:
        identifier = normalized(record["id"])
        if identifier in seen:
            raise ValueError(f"Duplicate id in {label}: {record['id']}")
        seen.add(identifier)


def is_accepted(record):
    """Only use history with explicit passed status and no contradictory marker."""
    markers = []
    if "quality_status" in record:
        markers.append(record["quality_status"])
    for field in ("visual_review", "quality"):
        value = record.get(field)
        if isinstance(value, dict) and "status" in value:
            markers.append(value["status"])
    return bool(markers) and all(marker == "passed" for marker in markers)


def collision(first, second, scope):
    differences = [field for field in AXES
                   if normalized(first[field]) != normalized(second[field])]
    structural = [field for field in STRUCTURE if field in differences]
    reasons = []
    if len(differences) < 4:
        reasons.append("fewer_than_four_different_axes")
    if not structural:
        reasons.append("no_structural_difference")
    if not reasons:
        return None
    return {"first_id": first["id"], "second_id": second["id"], "scope": scope,
            "different_axes": differences, "different_axis_count": len(differences),
            "structural_differences": structural, "reasons": reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--history", type=Path, help="Optional accepted-character JSONL. Read only.")
    args = parser.parse_args()
    base = {"schema_version": 1, "semantic_review_required": True,
            "limitation": "Only exact NFKC/case/whitespace-normalized strings are compared. Synonyms and visually similar designs still require review."}
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(plan, dict) or plan.get("mode") not in ("new_character", "edit"):
            raise ValueError("plan.mode must be new_character or edit")
        records = plan.get("characters")
        if not isinstance(records, list) or not records:
            raise ValueError("plan.characters must be a nonempty array")
        for index, record in enumerate(records):
            validate_record(record, f"characters[{index}]")
        check_ids(records, "plan")

        history, skipped = [], 0
        history_status = "not_requested"
        if args.history is not None and plan["mode"] == "new_character":
            history_status = "requested"
            if not args.history.is_file():
                raise ValueError(f"History file not found: {args.history}")
            history_status = "loaded"
            for number, line in enumerate(args.history.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                item = json.loads(line)
                if not isinstance(item, dict):
                    raise ValueError(f"history line {number} must be an object")
                if not is_accepted(item):
                    skipped += 1
                    continue
                history.append(validate_record(item, f"history line {number}"))
            check_ids(history, "history")
        if plan["mode"] == "new_character":
            existing_ids = {normalized(item["id"]) for item in history}
            for record in records:
                if normalized(record["id"]) in existing_ids:
                    raise ValueError(f"New-character id already exists in history: {record['id']}")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({**base, "status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    collisions = []
    pairs_checked = 0
    if plan["mode"] == "new_character":
        pairs = itertools.chain(
            ((a, b, "current_batch") for a, b in itertools.combinations(records, 2)),
            ((a, b, "loaded_history") for a in records for b in history))
        for first, second, scope in pairs:
            pairs_checked += 1
            result = collision(first, second, scope)
            if result is not None:
                collisions.append(result)
    status = "not_applicable" if plan["mode"] == "edit" else (
        "failed" if collisions else "needs_semantic_review")
    print(json.dumps({**base, "status": status, "mode": plan["mode"],
                      "diversity_checks_passed": None if plan["mode"] == "edit" or pairs_checked == 0 else not collisions,
                      "comparison_coverage": "none" if pairs_checked == 0 else "exact_strings_only",
                      "character_count": len(records), "history_status": history_status,
                      "history_records_used": len(history), "history_records_skipped": skipped,
                      "comparison_scope": "batch_and_loaded_history" if history else "current_batch_only",
                      "pairs_checked": pairs_checked, "minimum_different_axes": 4,
                      "required_structural_axes": list(STRUCTURE), "collisions": collisions},
                     ensure_ascii=False, indent=2))
    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())
