import re
from typing import List, Dict

# ------------------ REGEX PATTERNS ------------------

PII_PATTERNS = {
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),

    "PHONE": re.compile(
        r"(?<!\w)"
        r"(\+?\d{1,3}[\s-]?)?"
        r"(\(?\d{2,4}\)?[\s-]?)?"
        r"\d{3,4}[\s-]?\d{3,4}"
        r"(?!\w)"
    ),

    "DOB": re.compile(
        r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        re.IGNORECASE
    ),

    "APPT_ID": re.compile(
        r"\b(?:APPT|BKG|INV)[-_]?\d{4,}\b",
        re.IGNORECASE
    ),

    "INSURANCE_ID": re.compile(
        r"\b(?:BUPA|POLICY|INS)[-_]?[A-Z0-9-]{4,}\b",
        re.IGNORECASE
    ),

    "GOV_ID": re.compile(
        r"\b(\d{3}-\d{2}-\d{4}|\d{4}[\s-]\d{4}[\s-]\d{4}|\d{10,12})\b"
    ),

    "URL": re.compile(
        r"https?://[^\s]+"
    ),
}

# ------------------ HEURISTIC PATTERNS ------------------

NAME_PATTERN = re.compile(
    r"\b(Dr\.?|Patient|Partner)\s*:?[\s]+("
    r"[A-Z]\.\s*[A-Z][a-z]+|"
    r"[A-Z][a-z]+\s[A-Z][a-z]+|"
    r"[A-Z][a-z]+"
    r")\b"
)

PROVIDER_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s"
    r"(Clinic|Hospital|Labs?|IVF|Pathology|Fertility)\b"
)

ADDRESS_PATTERN = re.compile(
    r"\b\d{1,4}\s[A-Za-z\s]+"
    r"(Street|St|Road|Rd|Lane|Ln|Avenue|Ave|Flat)\b.*?\b\d{4,6}\b",
    re.IGNORECASE
)

# ------------------ PRIORITY (HIGHER = STRONGER) ------------------

PRIORITY = {
    "GOV_ID": 100,
    "INSURANCE_ID": 90,
    "APPT_ID": 80,
    "DOB": 70,
    "URL": 65,
    "EMAIL": 60,
    "ADDRESS": 50,
    "PROVIDER": 45,
    "NAME": 40,
    "PHONE": 30,
}

# ------------------ HELPERS ------------------

def is_false_phone(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 25): min(len(text), end + 25)].lower()
    blacklist = ["steps", "battery", "locker", "not a phone", "%"]
    return any(bad in window for bad in blacklist)


def overlaps(a: Dict, b: Dict) -> bool:
    return not (a["end"] <= b["start"] or b["end"] <= a["start"])


def inside_any(span: Dict, spans: List[Dict], span_type: str) -> bool:
    for s in spans:
        if s["type"] == span_type:
            if span["start"] >= s["start"] and span["end"] <= s["end"]:
                return True
    return False

# ------------------ CORE FUNCTIONS ------------------

def detect_spans(text: str) -> List[Dict]:
    spans = []

    # Pass 1: URLs first
    for match in PII_PATTERNS["URL"].finditer(text):
        spans.append({
            "type": "URL",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.95
        })

    # Pass 2: other regex PII
    for pii_type, pattern in PII_PATTERNS.items():
        if pii_type == "URL":
            continue

        for match in pattern.finditer(text):
            temp_span = {
                "type": pii_type,
                "start": match.start(),
                "end": match.end()
            }

            if pii_type == "EMAIL" and inside_any(temp_span, spans, "URL"):
                continue

            if pii_type == "PHONE" and is_false_phone(text, match.start(), match.end()):
                continue

            spans.append({
                "type": pii_type,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.95
            })

    # Heuristic patterns
    for match in NAME_PATTERN.finditer(text):
        spans.append({
            "type": "NAME",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.75
        })

    for match in PROVIDER_PATTERN.finditer(text):
        spans.append({
            "type": "PROVIDER",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.80
        })

    for match in ADDRESS_PATTERN.finditer(text):
        spans.append({
            "type": "ADDRESS",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.85
        })

    return spans


def resolve_overlaps(spans: List[Dict]) -> List[Dict]:
    spans = sorted(spans, key=lambda s: (s["start"], -PRIORITY[s["type"]]))
    resolved = []

    for span in spans:
        keep = True
        for r in resolved[:]:
            if overlaps(span, r):
                if PRIORITY[span["type"]] <= PRIORITY[r["type"]]:
                    keep = False
                    break
                else:
                    resolved.remove(r)
        if keep:
            resolved.append(span)

    return resolved


def scrub_text(text: str, spans: List[Dict]) -> str:
    scrubbed = text
    for span in sorted(spans, key=lambda s: s["start"], reverse=True):
        scrubbed = (
            scrubbed[:span["start"]]
            + f"[{span['type']}]"
            + scrubbed[span["end"]:]
        )
    return scrubbed


def process_entry(entry: Dict) -> Dict:
    text = entry["text"]

    spans = resolve_overlaps(detect_spans(text))
    scrubbed_text = scrub_text(text, spans)

    return {
        "entry_id": entry["entry_id"],
        "scrubbed_text": scrubbed_text,
        "detected_spans": spans,
        "types_found": sorted({s["type"] for s in spans}),
        "scrubber_version": "v3"
    }
