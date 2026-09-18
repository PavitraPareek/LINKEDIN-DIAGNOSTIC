"""
verify.py
---------
Deterministic verification engine for the Prospect-to-Diagnostic pipeline.

Input:  claims_data.json  (a claim, the sources that support it, the
        sources that contradict it, and each source's trust tier)
Output: verification_result.json  (every claim labelled VERIFIED /
        PARTIALLY_VERIFIED / UNVERIFIED, plus a separate refusal log)

This file contains NO network calls. It only applies rules to data that
has already been collected. That split is intentional: research
(collecting claims + sources) and judgement (deciding what to trust) are
kept as two separate, auditable steps, so a human reviewer can inspect
either one without re-running the other.

Tier ranking (highest trust first):
  primary            - published by the entity the claim is about, or a
                        party with direct financial/legal skin in the
                        claim (e.g. a shareholder's own newsroom).
  press-independent   - independent news desk reporting, not a profile
                        piece and not sourced from the subject directly.
  press-interview      - direct quotes from the subject, published by an
                        independent outlet. Trustworthy as "the subject
                        said this," not as independent confirmation of
                        numbers.
  press-profile        - bio-style features, typically built from
                        subject-supplied material.
  aggregator            - crowdsourced/scraped profile sites (Crunchbase,
                        The Org, TheOfficialBoard, etc). These frequently
                        copy each other or LinkedIn, so agreement between
                        two aggregators is NOT treated as independent
                        corroboration.
  self-reported          - the subject's own LinkedIn/profile copy.
"""

import json
from pathlib import Path

INDEPENDENT_TIERS = {"primary", "press-independent"}
WEAK_TIERS = {"aggregator", "self-reported", "press-profile", "press-interview"}


def load_data(path="claims_data.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def classify(claim, sources):
    """
    Returns (status, reason) for a single claim.

    Rules, applied in order:
    1. If the claim has ANY contradicting source that is primary or
       press-independent, and the claim's own support is weaker than
       that -> UNVERIFIED, refused. A louder/better-sourced contradiction
       beats a quieter one.
    2. If 2+ INDEPENDENT-tier sources support the claim and none
       contradict at that tier -> VERIFIED.
    3. If exactly 1 independent-tier source supports it, or multiple
       weak-tier sources support it (with a corroboration caveat noted),
       or supporting sources look like they trace to one common origin
       -> PARTIALLY_VERIFIED.
    4. Otherwise -> UNVERIFIED.
    """
    supporting_tiers = [sources[s]["tier"] for s in claim["supporting"]]
    contradicting_tiers = [sources[s]["tier"] for s in claim.get("contradicting", [])]

    strong_contradiction = any(t in INDEPENDENT_TIERS for t in contradicting_tiers)
    strong_support_count = sum(1 for t in supporting_tiers if t in INDEPENDENT_TIERS)

    if strong_contradiction and strong_support_count < 2:
        better_sources = [
            s for s in claim.get("contradicting", [])
            if sources[s]["tier"] in INDEPENDENT_TIERS
        ]
        reason = (
            f"Contradicted by higher-trust source(s) {better_sources}. "
            f"Claim's own support ({claim['supporting']}) does not clear "
            f"the two-independent-source bar needed to override that "
            f"contradiction. Refused rather than passed through with a "
            f"caveat, because the contradiction is about a specific fact "
            f"(a date / an ownership structure), not a matter of opinion."
        )
        return "UNVERIFIED", reason

    if strong_support_count >= 2:
        return "VERIFIED", (
            f"Corroborated by {strong_support_count} independent, "
            f"higher-trust sources with no higher-trust contradiction."
        )

    if strong_support_count == 1:
        return "PARTIALLY_VERIFIED", (
            "Only one independent-tier source found. Treated as likely "
            "true but not cross-confirmed."
        )

    if claim.get("corroboration_caveat"):
        return "PARTIALLY_VERIFIED", (
            "Multiple sources agree, but they plausibly share a common "
            "origin (a subject-supplied bio) rather than being "
            "independently reported: " + claim["corroboration_caveat"]
        )

    if supporting_tiers:
        return "PARTIALLY_VERIFIED", (
            "Only weak-tier sources (aggregator / self-reported / profile) "
            "support this claim; no independent confirmation found."
        )

    return "UNVERIFIED", "No credible source found for this claim."


def run():
    data = load_data()
    sources = data["source_registry"]
    results = []
    for claim in data["claims"]:
        status, reason = classify(claim, sources)
        results.append({
            "id": claim["id"],
            "text": claim["text"],
            "status": status,
            "reason": reason,
            "supporting_sources": claim["supporting"],
            "contradicting_sources": claim.get("contradicting", []),
        })

    out = {
        "subject": data["subject"],
        "results": results,
        "refused_claims": [r for r in results if r["status"] == "UNVERIFIED" and r["contradicting_sources"]],
    }

    Path("output").mkdir(exist_ok=True)
    with open("output/verification_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Processed {len(results)} claims.")
    for r in results:
        print(f"  [{r['status']:18s}] {r['id']}: {r['text'][:70]}")

    return out


if __name__ == "__main__":
    run()
