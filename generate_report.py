"""
generate_report.py
-------------------
Takes output/verification_result.json and produces a one-page PDF
diagnostic: output/diagnostic_jayesh_patel.pdf

Design choice: this script does NOT re-decide what's true. It only
formats what verify.py already decided. Report layout and verification
logic are kept apart so either can be changed without touching the other.
"""

import json
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib import colors

with open("output/verification_result.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("claims_data.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

results = {r["id"]: r for r in data["results"]}
subject = data["subject"]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=16, spaceAfter=1,
                           fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="H2", fontSize=9.3, leading=11, spaceBefore=5,
                           spaceAfter=2, fontName="Helvetica-Bold",
                           textColor=colors.HexColor("#1a1a1a")))
styles.add(ParagraphStyle(name="Small", fontSize=7.2, leading=9,
                           textColor=colors.HexColor("#444444"), spaceAfter=1))
styles.add(ParagraphStyle(name="Body", fontSize=7.7, leading=9.6, spaceAfter=1))
styles.add(ParagraphStyle(name="BodyBold", fontSize=7.7, leading=9.6,
                           fontName="Helvetica-Bold"))

GREEN = colors.HexColor("#1a7f37")
AMBER = colors.HexColor("#9a6700")
RED = colors.HexColor("#cf222e")
GREY = colors.HexColor("#57606a")

STATUS_LABEL = {
    "VERIFIED": ("VERIFIED", GREEN),
    "PARTIALLY_VERIFIED": ("PARTIAL", AMBER),
    "UNVERIFIED": ("REJECTED", RED),
}

doc = SimpleDocTemplate(
    "output/diagnostic_jayesh_patel.pdf",
    pagesize=A4,
    topMargin=10 * mm, bottomMargin=8 * mm,
    leftMargin=14 * mm, rightMargin=14 * mm,
)

story = []

# --- Header -----------------------------------------------------------
story.append(Paragraph("Public-Presence Diagnostic", styles["H1"]))
story.append(Paragraph(
    f"{subject['name']} &nbsp;·&nbsp; {subject['role']} &nbsp;·&nbsp; {subject['location']}",
    styles["Body"]
))
story.append(Paragraph(
    f"Generated {date.today().isoformat()} · Sources: public web, business press, "
    f"and shareholder/regulatory press releases only. No login-gated data used.",
    styles["Small"]
))
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cccccc"),
                         spaceBefore=6, spaceAfter=8))

# --- Verified facts -----------------------------------------------------
verified = [r for r in data["results"] if r["status"] == "VERIFIED"]
story.append(Paragraph("VERIFIED &nbsp;— corroborated by 2+ independent, higher-trust sources", styles["H2"]))
for r in verified:
    story.append(Paragraph(f"• {r['text']}", styles["Body"]))

# --- Partially verified ---------------------------------------------------
partial = [r for r in data["results"] if r["status"] == "PARTIALLY_VERIFIED"]
story.append(Paragraph("PARTIALLY VERIFIED &nbsp;— plausible, but single-source or common-origin only (career history "
                        "and education claims below repeat across profiles that likely share one original bio, not "
                        "independent reporting; FY2023 financials trace to one interview, not a filing)", styles["H2"]))
for r in partial:
    story.append(Paragraph(f"• {r['text']}", styles["Body"]))

# --- Refused / rejected -----------------------------------------------
refused = [r for r in data["results"] if r["status"] == "UNVERIFIED"]
story.append(Paragraph("REJECTED &nbsp;— found in public sources, excluded from this diagnostic", styles["H2"]))
for r in refused:
    story.append(Paragraph(f"• \u201c{r['text']}\u201d", styles["Body"]))
    story.append(Paragraph(f"&nbsp;&nbsp;↳ Why rejected: {r['reason']}", styles["Small"]))

# --- Cross-source inconsistency flag -----------------------------------
story.append(Paragraph("FLAGGED INCONSISTENCY — not auto-resolved", styles["H2"]))
story.append(Paragraph(
    "• Engineering credential conflict: one aggregator (The Org) lists a Civil "
    "Engineering degree from Southern Illinois University Edwardsville; another "
    "(TheOfficialBoard) lists a Master of Science in Mechanical Engineering from "
    "University of Illinois Urbana-Champaign. These could both be true (undergrad "
    "+ graduate degree) or one could be a scraping error. The system does not "
    "guess which — it surfaces the conflict for human resolution instead of "
    "silently picking one.",
    styles["Body"]
))

# --- Three biggest gaps --------------------------------------------------
story.append(Paragraph("THREE BIGGEST GAPS IN CURRENT PUBLIC PRESENCE", styles["H2"]))
gaps = [
    ("1. No first-party bio.", "The CEO-start-date error (C3) and the single-owner "
     "error (C5) both originate from the same third-party feature article, and both "
     "are still live online. Neither Wio Bank's own site nor Patel's own LinkedIn "
     "publishes a dated, factual career/appointment timeline that a journalist could "
     "cite instead — so errors like these have nothing correct to be checked against."),
    ("2. Headline financial claims rest on a single quote, not a filing.",
     "The FY2023 profitability figures (C12) are only sourced to one interview. For an "
     "institutional or DIFC audience, a number attributed to \u201cthe CEO said so\u201d "
     "reads very differently from one attributed to a published financial statement."),
    ("3. Career-history corroboration is an illusion of consensus.", "Multiple "
     "profiles (Crunchbase, The Org, Entrepreneur ME) repeat the same prior-role "
     "claims (C7, C8) — but they plausibly all copy one original bio rather than "
     "reporting independently. It looks well-corroborated; it isn't."),
]
for title, body in gaps:
    story.append(Paragraph(title, styles["BodyBold"]))
    story.append(Paragraph(body, styles["Body"]))

# --- Footer / methodology -------------------------------------------------
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cccccc"),
                         spaceBefore=8, spaceAfter=4))
story.append(Paragraph(
    "Methodology: each claim needs 2 independent higher-trust sources (regulator/"
    "shareholder press release, or independent news desk) to be marked VERIFIED. "
    "Aggregator sites (Crunchbase, The Org, TheOfficialBoard) and the subject's own "
    "profile are never counted as independent confirmation on their own. A claim "
    "contradicted by a higher-trust source than the one supporting it is rejected, "
    "not softened. This diagnostic is a drafting aid — a human must review every line "
    "before it reaches a client.",
    styles["Small"]
))

doc.build(story)
print("Wrote output/diagnostic_jayesh_patel.pdf")
