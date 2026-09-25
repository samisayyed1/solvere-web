# Firmware -- standards and applicability

## When each standard applies

| Standard | Current edition (2026-09-25) | Applies when | Source |
|---|---|---|---|
| DO-178C / ED-12C | 2011, no DO-178D published | Airborne software (only if the project is aviation). | R5b §1 |
| DO-254 / ED-80 | Original edition, Apr 2000 (DO-254A targeted Dec 2027) | Airborne complex electronic hardware (only if aviation). | R5b §1 |
| IEC 61508 | Ed. 2.0, 2010 (Ed.3 at CDV/vote stage) | Functional safety of programmable electronic systems, any sector without a sector-specific derivative. | R5b §1 |
| ISO 26262 | 2nd edition, 2018 (3rd-edition DIS registered 2026-08-04) | Automotive functional safety (only if the product is automotive). | R5b §1 |
| NIST IR 8259 / 8259A / 8259B | IR 8259 Rev. 1 (final, 2026-04-20); 8259A (2020-05), 8259B (2021-08) unchanged | IoT device cybersecurity capability baseline. | R5e §"Standards table" |
| ETSI EN 303 645 | V3.1.3, 2024-09 | Consumer IoT cybersecurity baseline (not RED-harmonised). | R5e §"Standards table" |
| EN 18031-1/-2/-3 | :2024, cited with restrictions by (EU) 2025/138 | RED Article 3.3(d)/(e)/(f) cybersecurity presumption of conformity for radio equipment placed in the EU -- restrictions apply (no presumption if a password-optional mode exists, if toy/childcare equipment lacks parental control, or for -3's secure-update criteria). | R5e §Summary |

Most of these are sector-gated (aviation, automotive) or apply only to radio equipment placed on the EU market -- confirm applicability in `mapping-compliance` before treating any of them as binding.

## What Forge automates

- Build, static analysis, and unit tests on every firmware change (`building-firmware`), with tests proven to fail on a mutated implementation.
- Simulation (Renode/QEMU-class, per the installed toolchain) before any hardware step.
- Size and timing budget checks (flash/RAM headroom, worst-case loop time) against `params/params.toml`.

## What needs a qualified human

- Any DO-178C/DO-254/IEC 61508/ISO 26262 applicability determination and the associated development-assurance-level work -- this is safety-critical certification territory, not something Forge's checks substitute for.
- Boot/OTA security review: signature verification and rollback protection get an explicit human review note before any "secure" claim.
- HIL testing and flashing run through bounded tools only, and are `permissions.ask` -- a human is in the loop for every physical write to hardware.
- CRA (Cyber Resilience Act) vulnerability/incident reporting obligations (active from 2026-09-11, full application 2027-12-11) are filed by a named human through ENISA's Single Reporting Platform, never by Forge -- see `docs/standards/compliance.md`.
