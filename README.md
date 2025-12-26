# Exercise A — PII / Sensitive Identifier Scrubber

## Context

Ashwam processes free-text women’s health journals containing symptoms, cycle notes, appointments, and care logistics. Before any downstream processing, all personally identifying or linkable information must be removed without destroying the health meaning of the entry.

This project implements a deterministic PII and sensitive identifier scrubber that operates on a fixed synthetic dataset and produces an auditable output suitable for downstream processing.

---

## Why This Exercise

I chose this exercise because it reflects real problems faced when working with healthcare text data. The challenge is not only identifying sensitive information, but doing so carefully—avoiding over-scrubbing while preserving clinical meaning. It requires clear reasoning, explicit tradeoffs, and an approach that can be easily explained and tested.

---

## Problem Overview

The input is a JSONL file where each line contains a journal entry: {"entry_id":"j_001","text":"Free-text journal entry..."}


The goal is to process each entry and:

1. Detect and replace sensitive identifiers with typed placeholders  
2. Produce a structured audit output describing what was removed  
3. Preserve all health-related content such as symptoms, cycle data, mood, and medication  
4. Ensure the solution is deterministic, testable, and runnable locally  

All data provided is synthetic.

---

## Sensitive Identifiers Handled

### Direct Identifiers

- **EMAIL**
- **PHONE**  
  Supports common AU / US / IN formats and tolerates spaces, hyphens, and parentheses
- **NAME**  
  Patient, partner, and clinician names using heuristic-based detection
- **ADDRESS**  
  Street-style addresses using pattern-based matching
- **DATE_OF_BIRTH (DOB)**

### Health-System Identifiers

- **PROVIDER / CLINIC IDENTIFIER**
- **APPOINTMENT / BOOKING / INVOICE ID**
- **INSURANCE POLICY / MEMBER ID**
- **GOVERNMENT HEALTH ID**  
  SSN-like, Aadhaar-like, and Medicare-like patterns

### Additional Identifiers

- **URL**

---

## What Is Not Scrubbed

The scrubber is intentionally conservative and does not remove:

- Symptoms (e.g., cramps, bloating, anxiety)
- Cycle information (day count, timing)
- Medication names unless tied to an identifier
- Food, sleep, activity, or mood
- Vitals such as weight or blood pressure
- Generic numbers that are not identifiers

The guiding principle throughout is to remove identity while preserving health signal.

---

## Detection Approach

The solution is entirely rule-based and deterministic. It uses:

- Regular expressions for structured identifiers such as emails, phone numbers, and IDs
- Heuristic patterns for names, providers, and addresses
- Context-based checks to avoid numeric false positives

No machine learning models or external services are used, keeping the system predictable and auditable.

---

## Overlap Handling and Priority Logic

Sensitive identifiers can overlap in free text. To handle this, each identifier type is assigned a priority level.

When overlaps occur:
- Higher-priority identifiers are kept
- Lower-priority overlapping spans are discarded
- Broader and more specific spans take precedence

For example, a URL containing an email address is scrubbed as a URL rather than masking the embedded email separately.

---

## Confidence Scoring

Each detected span includes a confidence score:

- Strong regex matches (EMAIL, PHONE, IDs) are assigned high confidence
- Heuristic-based detections (NAME, PROVIDER) receive slightly lower confidence
- Ambiguous cases are scored conservatively

Confidence scores are rule-based and included to support auditability rather than statistical certainty.

---

## Output Format

For each journal entry, the output includes:

- `entry_id`
- `scrubbed_text`
- `detected_spans` with:
  - type
  - start and end character offsets from the original text
  - confidence score
- `types_found` as a unique list
- `scrubber_version`

Raw PII values are never written to output files or logs.

---

## Example

**Input** 

Appointment booked at Monash Women’s Health Clinic with Dr. Kavita Rao. Ref ID: APPT-839201. Feeling anxious.

**Output**

Appointment booked at [PROVIDER] with [NAME]. Ref ID: [APPT_ID]. Feeling anxious.

The clinical meaning is preserved while personal identifiers are removed.

---

## Running the Scrubber

The scrubber can be run locally using:
python cli.py --in journals.jsonl --out scrubbed.jsonl


The output is written as a JSONL file with one processed entry per line.

---

## Testing

The test suite verifies that:

- All required identifier types are detected
- Health content is not over-scrubbed
- Numeric false positives are avoided
- Overlapping matches are resolved correctly
- Informal and multilingual text remains intact

Tests can be run with:     
python tests.py


---

## Known Limitations

- Name detection is heuristic-based and may miss uncommon formats
- Address detection relies on simple street-style patterns
- Context understanding is limited to rule-based logic

These limitations are intentional to maintain determinism and explainability.

---

## Future Improvements

With more time or tooling, I would:

- Introduce lightweight NER to improve name and provider recall
- Expand address detection for additional international formats
- Make detection rules configurable by region
- Add richer per-span audit explanations

---

## Final Notes

This solution prioritizes clarity, privacy, and explainability over aggressive detection. Each design decision reflects a conscious tradeoff aimed at protecting identity while preserving meaningful health information.



