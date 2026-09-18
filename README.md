# Prospect-to-Diagnostic — Jayesh Patel (Wio Bank)

Built for the Growpido AI & Automation Engineer build task, Track B.

## What this is

A 3-file pipeline that turns a set of publicly-sourced claims about a
person into a one-page diagnostic, with every claim labelled
**VERIFIED / PARTIALLY VERIFIED / REJECTED**, and a visible log of what
got rejected and why.

```
claims_data.json     -> raw research: claims + their sources + trust tier
verify.py             -> deterministic rules, labels every claim
generate_report.py    -> formats the labelled claims into a 1-page PDF
```

Run order:
```
python3 verify.py            # writes output/verification_result.json
python3 generate_report.py   # writes output/diagnostic_jayesh_patel.pdf
```

## Why it's split into three files, not one script

Research (finding claims and sources) and judgement (deciding what to
trust) are different jobs with different failure modes. Keeping them in
separate files means:
- a human can audit `claims_data.json` on its own — is the source list
  honest and complete? — without touching any logic
- the verification *rules* in `verify.py` are visible and editable
  without re-running research
- the report is just formatting; it never re-decides what's true

## The rule that matters most

A claim is only **VERIFIED** if 2+ *independent, higher-trust* sources
support it. "Independent" excludes:
- aggregator sites (Crunchbase, The Org, TheOfficialBoard) agreeing with
  each other — they routinely scrape one another or LinkedIn, so
  agreement between two of them is not two opinions, it's one opinion
  copied twice
- the subject's own LinkedIn/profile copy, on its own

If a claim is contradicted by a source that outranks its own support,
it is **REJECTED outright**, not downgraded with a soft caveat. Example
in this diagnostic: a feature article says Patel has been CEO "since
December 2020." A UAE shareholder's own press release, plus an
independent Gulf News report, both place his confirmation as CEO around
February 2022, tied to the Central Bank's license approval. The
December 2020 claim is dropped, not hedged.

## The claim it refused, and why (required for submission)

**Rejected claim:** *"Wio Bank is owned solely by 'the investment and
holding company Abu Dhabi Holding.'"* — from a single Entrepreneur
Middle East feature.

**Why:** Wio Bank's actual ownership structure is public record via
ADQ's own newsroom and corroborated independently by The National and
Gulf Business: four shareholders (ADQ + Alpha Dhabi at a combined 65%,
Etisalat/e& at 25%, First Abu Dhabi Bank at 10%). The single-owner claim
is very likely a garbled shorthand for ADQ (whose full name is close to
"Abu Dhabi Holding"), but I don't get to assume that — a system that
quietly "corrects" a wrong claim into a guessed right one is worse than
one that just refuses it. It's logged as rejected, with both
contradicting sources named, for a human to resolve.

## Where this pipeline is weakest (read this before trusting it)

- **It doesn't fetch live data.** `claims_data.json` was populated by
  me, this week, using web search. A production version needs a real
  ingestion step (search API + scraper) feeding into the same
  `claims_data.json` shape — the verification logic doesn't change.
- **Tier assignment is still a human judgement call.** I decided Gulf
  News counts as "press-independent" and Crunchbase doesn't. That
  classification itself isn't verified by anything — it's my call,
  and it's the single point where bias could enter the system
  invisibly. A real deployment should make this list reviewable/
  editable by the client, not buried in code.
- **No sentiment or reputational risk scoring** — that was Track A's
  job, not this one, but it's worth naming: this diagnostic tells you
  what's *true*, not what's *risky to leave uncorrected*. Those are
  different judgments and shouldn't be collapsed into one score.
- **One page is a hard constraint I fought against.** The FY2023
  financial claim deserves more scrutiny than one bullet gives it —
  a company's own audited numbers vs a CEO's quoted numbers is a real
  gap worth its own paragraph, and it got compressed to fit the format.

## Human gate

Nothing here is meant to go to a client unreviewed. The PDF's own
footer says so. The refusal log (`output/verification_result.json` →
`refused_claims`) exists specifically so a reviewer can check the
system's *rejections*, not just its acceptances — that's usually the
part nobody double-checks.
