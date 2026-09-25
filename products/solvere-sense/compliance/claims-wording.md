# Claims wording (deny-list and neutral terms)

**Not a compliance determination.** This is the project's wording policy, set by the owner (Owner round 2, `docs/intake/G0-owner-answers-2.md`: "Keep 'no medical or safety claims' strict: even 'fall detection' wording must not imply a safety device"). It is the check list for REQ-SAFE-003 and REQ-SAFE-004. A qualified human decides the regulatory position (Q-17).

## Scope

All user-facing text: labels, packaging, instructions, marketing and web copy, app screens, notifications, and Home Assistant / ESPHome entity and device names. The kit ships ESPHome firmware (DS p.2); its default entity names must be checked and renamed where they hit the deny-list.

Engineering documents in this repository (requirements, tests, reviews) also use the neutral terms. When they cite a vendor document whose title contains a denied term (for example the DS title "XIAO 60GHz mmWave Human Fall Detection Sensor-MR60FDA2"), the title is quoted as published and never reused as product text.

## Use these neutral terms

| Say | For |
|---|---|
| fall event, fall-event output | the sensor's fall output |
| presence, presence output | the sensor's presence output |
| home-automation sensor, ceiling presence sensor | the product |
| sends an event to Home Assistant | what happens on a fall event |

## Deny-list (case-insensitive, any inflection)

- fall detection, fall detector, detects falls, fall alert, fall alarm, fall monitoring
- alarm, alert (as a product function), emergency, SOS, call for help
- safety device, keeps (you / them) safe, protects, protection (of people), peace of mind
- medical, health, care, caregiver, patient, elderly, senior, vulnerable, clinical, diagnose
- monitor or monitoring (of people), guaranteed, never miss, life-saving, 24/7 safety

## How it is checked

- Before G4: `safety-compliance-engineer` reviews every user-facing text against this list (TP-SAFE-003, TP-SAFE-004).
- Lint note: a text search for the deny-list terms over `app/`, `firmware/` entity names, `release/` and marketing copy is a check that can fail; it is proposed as an automated check once those folders have content. Until then the review is manual.
- Any exception needs the owner's decision and a qualified human's approval, recorded here with the date.

## Exceptions

None.
