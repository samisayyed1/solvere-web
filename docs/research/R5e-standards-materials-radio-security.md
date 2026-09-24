# R5e — Standards: materials, radio/EMC, product cybersecurity
- Date accessed: 2026-09-25 · Author: research agent (Phase 1) · Scope: current status of the EU RoHS and REACH/SCIP substance rules, FCC Part 15, ISED RSS-Gen/RSS-247, EU RED cybersecurity (Delegated Regulation 2022/30 plus EN 18031), CISPR 32/35 (EN 55032/55035), ETSI EN 303 645, NIST IR 8259 series, EU Cyber Resilience Act and OWASP ASVS.
- Tags: **[V]** verified on the issuing body's own page (URL given) · **[R]** secondary source · **[U]** unverified (background knowledge or not re-checked in this session).
- Forge stance: this file only summarises and links to the sources. It does not reproduce any standard or regulation text, and it makes no compliance claims. A qualified human signs off.

## Summary
- **The CRA is already partly in force.** Manufacturers must report actively exploited vulnerabilities and severe incidents from **11 Sep 2026**. This duty covers in-scope products placed on the market *before* 11 Dec 2027 as well. Deadlines are 24 h for an early warning, 72 h for a notification, and a final report within 14 days (vulnerabilities) or 1 month (incidents). Reports go through ENISA's Single Reporting Platform, which went live on 11 Sep 2026. The rules for notified bodies (Chapter IV) have applied since **11 Jun 2026**. Full application starts **11 Dec 2027**. [V]
- **The RED cybersecurity delegated act has an end date.** Delegated Regulation (EU) 2022/30 has applied since **1 Aug 2025**. It is repealed with effect from **11 Dec 2027** by Delegated Regulation (EU) **2026/339**, adopted 16 Feb 2026 and published in the OJ on 29 Apr 2026. From that date the CRA replaces it for radio equipment. Market surveillance can still check products placed on the market between 1 Aug 2025 and 10 Dec 2027. [V]
- **EN 18031-1/-2/-3:2024 are harmonised but restricted.** They are cited by Implementing Decision (EU) 2025/138 (OJ 30 Jan 2025). They give **no presumption of conformity** in these cases:
  - the user may skip setting a password (clauses 6.2.5.1/6.2.5.2);
  - toy or childcare equipment has no parental or guardian control (-2);
  - secure updates rely on the clause 6.3.2.4 criteria (-3).
  The "rationale" and "guidance" sections never give presumption. [V]
- **RoHS lead exemptions changed on 1 Jul 2026.** Delegated Directive (EU) 2025/2364 (lead in steel/Al/Cu, exemptions 6(a)–6(c)) applies from that date [V]. Its sister acts 2025/1802 (7(a)) and 2025/2363 (7(c)) are reported to apply from the same date [R]. The next expiries fall on **11 Dec 2026** (6(b)-I, cats 1–7 and 10), 11 Jun 2027 and **30 Jun 2027** [V], unless a pending renewal application keeps them alive [R]. Directive (EU) 2025/2456 hands RoHS scientific work to ECHA from **13 Aug 2027** [V].
- **ISED RSS-Gen Issue 6 is new.** It was published 30 Jul 2026 and amended (Amendment 1) on 15 Sep 2026. Issue 5 is still accepted for one year after publication, i.e. until about 30 Jul 2027. RSS-247 is at Issue 4 (24 Jul 2025). [V]
- **REACH Candidate List:** 253 entries after the update of 4 Feb 2026, which added n-hexane and BPAF [R]. The ECHA site returned 403, so I could not confirm the count or whether a mid-2026 update happened. Treat the count as a floor. [U]
- **CISPR 32 and CISPR 35 both reach their IEC stability date in 2026.** CISPR 32 Ed. 2.1 (2015+A1:2019) and CISPR 35 Ed. 1.0 (2016) are current [V]. CISPR 32 Ed. 3 is reported at FDIS stage, with publication expected about Dec 2026 [R].
- **Other current editions:** ETSI EN 303 645 **V3.1.3 (2024-09)** [V]; NIST IR 8259 **Rev. 1 final (20 Apr 2026)**, while 8259A (May 2020) and 8259B (Aug 2021) are unchanged [V]; OWASP ASVS **5.0.0 (30 May 2025)** [V].

## Standards table

| Standard | Current edition/revision | Year | Body | Status / transition notes | Tag | Source URL |
|---|---|---|---|---|---|---|
| EU RoHS | Directive 2011/65/EU as amended | 2011 | EP & Council | 10 restricted substances. The EC topic page looks stale: it does not list the 2025 acts. | [V] | https://environment.ec.europa.eu/topics/waste-and-recycling/rohs-directive_en |
| RoHS Annex II amendment | Delegated Directive (EU) 2015/863 | 2015 | European Commission | Added the 4 phthalates (DEHP, BBP, DBP, DIBP). | [V] | same EC page |
| RoHS exemptions 6(a)–6(c) (lead in steel/Al/Cu) | Delegated Directive (EU) 2025/2364 | adopted 8 Sep 2025; OJ 21 Nov 2025 | European Commission | Applies from **1 Jul 2026**. Expiries: 6(a)-I/II and 6(c) on 30 Jun 2027; 6(b)-I on **11 Dec 2026** (cats 1–7, 10) or 30 Jun 2027 (cats 9, 11); 6(b)-II on 11 Jun 2027 (cats 1–7, 10) or 30 Jun 2027 (cats 9, 11). | [V] | https://eur-lex.europa.eu/eli/dir_del/2025/2364/oj/eng |
| RoHS exemption 7(a) (high-melting-temperature solder) | Delegated Directive (EU) 2025/1802 | OJ 21 Nov 2025 [R] | European Commission | Reported to apply from 1 Jul 2026. EUR-Lex was rate-limited, so not re-checked. | [R] | https://www.sgs.com/en-hk/news/2025/12/exemptions-of-rohs-directive-updated |
| RoHS exemption 7(c) (lead in glass/ceramic) | Delegated Directive (EU) 2025/2363 | OJ 21 Nov 2025 [R] | European Commission | Reported to apply from 1 Jul 2026. Not re-checked on EUR-Lex. | [R] | as above |
| RoHS: tasks moved to ECHA | Directive (EU) 2025/2456 | adopted 26 Nov 2025; OJ 12 Dec 2025 | EP & Council | Applies from **13 Aug 2027**. ECHA takes over exemption evaluation and restriction review; the restricted-substance list is reviewed at least every 4 years. | [V] | https://eur-lex.europa.eu/eli/dir/2025/2456/oj/eng |
| REACH SVHC Candidate List | 253 entries | last known update 4 Feb 2026 | ECHA | Added n-hexane and BPAF and its salts. Article 33 information duty applies above 0.1 % w/w in an article. Not known whether a June/July 2026 update happened, because echa.europa.eu returned 403. | [R] | https://www.sgs.com/en/news/2026/02/safeguards-02126-echa-expands-candidate-list-to-253-svhcs |
| SCIP database notification | Waste Framework Directive 2008/98/EC Art. 9(1)(i) (as amended by 2018/851) | duty since 5 Jan 2021 | ECHA / EP & Council | Suppliers of articles that contain a Candidate-List SVHC above 0.1 % w/w must notify ECHA's SCIP database. The ECHA page returned 403, so this is not re-checked. | [U] | https://echa.europa.eu/scip |
| FCC 47 CFR Part 15 | eCFR current; last amended **2026-04-27** | — | FCC | Subpart B (unintentional radiators, §15.101): most digital devices may use **SDoC or Certification**. Certification is mandatory for scanning receivers, radar detectors and Access BPL. Subpart C (intentional radiators, §15.201): **Certification by a TCB** by default, with SDoC only for narrow cases (carrier-current systems, §§15.211/15.213/15.221, some devices below 490 kHz). Procedures are in Part 2 Subpart J. | [V] | https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15 (read via the eCFR versioner API) |
| ISED RSS-Gen | **Issue 6** + Amendment 1 | 30 Jul 2026; A1 15 Sep 2026 | ISED Canada | Replaces Issue 5 (2018, amended 2019 and 2021). One-year transition: Issue 5 or 6 accepted until about 30 Jul 2027. A1 allows cable-locating equipment at 101.4 kHz. Publication notice SMSE-011-26. | [V] | https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-gen-general-requirements-compliance-radio-apparatus |
| ISED RSS-247 | **Issue 4** | 24 Jul 2025 | ISED Canada | DTS/FHSS/LE-LAN in 902–928 MHz, 2.4 GHz and 5 GHz bands. Notice SMSE-006-25. The 6-month transition from Issue 3 is reported to have ended in early 2026 [R]. | [V] (issue/date) | https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-247-digital-transmission-systems-dtss-frequency-hopping-systems-fhss-and-licence-exempt-local |
| EU RED | Directive 2014/53/EU | 2014 | EP & Council | In force. Article 3(3)(d)(e)(f) cybersecurity requirements were activated by 2022/30. | [V] | https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en |
| RED cyber delegated act | Delegated Regulation (EU) 2022/30 | 29 Oct 2021 (OJ 12 Jan 2022) | European Commission | Applied from **1 Aug 2025**. **Repealed with effect from 11 Dec 2027** by (EU) 2026/339. | [V] | https://eur-lex.europa.eu/eli/reg_del/2026/339/oj |
| Repeal act | Delegated Regulation (EU) 2026/339 | adopted 16 Feb 2026; OJ 29 Apr 2026 | European Commission | Avoids overlap with the CRA. Surveillance of products placed on the market between 1 Aug 2025 and 10 Dec 2027 is not affected. | [V] | https://eur-lex.europa.eu/eli/reg_del/2026/339/oj |
| EN 18031-1 / -2 / -3 | **:2024** | 2024 | CEN-CENELEC (JTC 13) | Cited **with restrictions** by Implementing Decision (EU) 2025/138 (28 Jan 2025, OJ 30 Jan 2025), entries 164–166 of Annex I to 2022/2191 (restrictions listed in Summary). No amended EN 18031 versions (e.g. /A1) were found as cited. | [V] | https://eur-lex.europa.eu/eli/dec_impl/2025/138/oj |
| CISPR 32 (MME emission) | **Ed. 2.1** (2015 + AMD1:2019, consolidated version) | 2019-10-01 | IEC CISPR/I | IEC stability date **2026**. Ed. 3 reported registered as FDIS in Feb 2026, publication expected about Dec 2026 [R]. | [V] (Ed. 2.1) / [R] (Ed. 3) | https://webstore.iec.ch/en/publication/65836 |
| EN 55032 | EN 55032:2015 + A11:2020 + A1:2020 | 2020 | CENELEC | Reported as cited under EMC Directive 2014/30/EU via Implementing Decision (EU) 2019/1326 as amended. OJ entry not re-checked. | [R] | https://knowledge.bsigroup.com/products/electromagnetic-compatibility-of-multimedia-equipment-emission-requirements-3 |
| CISPR 35 (MME immunity) | **Ed. 1.0** | 2016-08-16 | IEC CISPR/I | IEC stability date **2026**. No amendment or new edition listed. | [V] | https://webstore.iec.ch/en/publication/25667 |
| EN 55035 | EN 55035:2017 + A11:2020 | 2020 | CENELEC | Reported as cited under the EMC Directive. Not re-checked. | [R] | https://ib-lenhardt.com/kb/glossary/en-55035-cispr-35 |
| ETSI EN 303 645 | **V3.1.3** | 2024-09 | ETSI TC CYBER | Latest version folder 03.01.03_60 (24 Sep 2024). Earlier versions: V2.1.1 (2020). Not a RED harmonised standard. | [V] | https://www.etsi.org/deliver/etsi_en/303600_303699/303645/ |
| NIST IR 8259 | **Rev. 1** (final) | 2026-04-20 | NIST | Replaces IR 8259 (2020-05-29). Covers the whole lifecycle, including maintenance, support and end of life. DOI 10.6028/NIST.IR.8259r1. | [V] | https://csrc.nist.gov/pubs/ir/8259/r1/final |
| NIST IR 8259A | Original (final) | 2020-05 | NIST | IoT device cybersecurity capability core baseline. No revision listed. | [V] | https://csrc.nist.gov/pubs/ir/8259/a/final |
| NIST IR 8259B | Original (final) | 2021-08-25 | NIST | Non-technical supporting capability core baseline. No revision listed. | [V] | https://csrc.nist.gov/pubs/ir/8259/b/final |
| EU Cyber Resilience Act | Regulation (EU) 2024/2847 | 23 Oct 2024; OJ 20 Nov 2024 | EP & Council | In force since 10 Dec 2024. Chapter IV (notified bodies) from **11 Jun 2026**. Art. 14 reporting from **11 Sep 2026**, also for products placed before 11 Dec 2027. Full application **11 Dec 2027**. Type-examination certificates issued under other EU harmonisation legislation stay valid until 11 Jun 2028. Commission implementation guidance published 27 Jul 2026. | [V] | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R2847 ; https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act |
| CRA harmonised standards | Standardisation request **M/606**: 41 standards (horizontal + vertical) | — | CEN / CENELEC / ETSI | None were found cited in the OJ as of access. Page last updated 31 Jul 2026. The EC page sends readers to STAN4CRA / CYBERSTAND for status. | [V] (request) / [U] (no citations) | https://digital-strategy.ec.europa.eu/en/policies/cra-standardisation |
| CRA Single Reporting Platform | ENISA SRP | live 11 Sep 2026 | ENISA + CSIRT network | Manufacturers report once through the SRP. Open-source software stewards have duties from 11 Dec 2027 (Art. 24(3)). | [V] | https://digital-strategy.ec.europa.eu/en/policies/cra-reporting |
| OWASP ASVS | **5.0.0** | 2025-05-30 | OWASP | No 5.0.x or 5.1 release listed. The "latest" tag is a moving development build. The owasp.org project page returned 404 when accessed. | [V] (OWASP GitHub org) | https://github.com/OWASP/ASVS/releases |

## One-paragraph summaries

**EU RoHS (2011/65/EU + 2015/863 + 2025 acts).**
- *What it governs:* it limits 10 substances in electrical and electronic equipment (EEE): Pb, Cd, Hg, Cr(VI), PBB, PBDE and four phthalates [V]. Limits are set per homogeneous material, at 0.1 % w/w (0.01 % for Cd) [U — check Annex II].
- *Product triggers:* any EEE placed on the EU market, unless it is out of scope or covered by a time-limited Annex III/IV exemption.
- *2026–2027 changes:*
  - The 2025 delegated directives reset the lead exemptions 6(a)–(c), 7(a) and 7(c) from 1 Jul 2026. Several sub-exemptions expire between Dec 2026 and Jun 2027 [V for 2364; R for the others].
  - Pending renewal applications may keep an exemption valid past its listed date [R].
  - ECHA takes over the scientific work from 13 Aug 2027 [V].
- *Forge can automate:*
  - flag BOM lines by exemption code and expiry date;
  - track supplier declarations and missing material-declaration data (e.g. IPC-1752A-style);
  - generate a technical-file checklist.
- *Needs a human:* whether the product is in scope, whether an exemption really applies, the analytical test (XRF/ICP by a lab) and signing the EU Declaration of Conformity.

**REACH Candidate List and SCIP.**
- *What it governs:*
  - Candidate List SVHCs trigger an information duty down the supply chain (Art. 33) when an article contains more than 0.1 % w/w [R].
  - In the EU, the same threshold also triggers a SCIP notification under the Waste Framework Directive [U].
  - Separately, notification to ECHA (Art. 7(2)) applies above 1 t/yr [U].
- *List size:* the list grows about twice a year. The last confirmed count is 253 (4 Feb 2026) [R].
- *Forge can automate:* diffing the BOM's full material declarations against a *dated snapshot* of the Candidate List, with a rule to refresh the snapshot. It can also draft SCIP dossiers and customer Art. 33 letters.
- *Needs a human:* supplier data quality, calculation at article level ("once an article, always an article"), and submission to ECHA.

**FCC 47 CFR Part 15.**
- *What it governs:* RF emissions from unintentional radiators (Subpart B: digital devices, receivers, power supplies) and licence-exempt intentional radiators (Subpart C) [V].
- *Authorisation routes:*
  - Most Subpart B digital devices may use SDoC (self-declaration, with testing by any competent lab) or Certification [V].
  - Subpart C transmitters generally need Certification through a TCB, with a few SDoC exceptions [V].
  - Module and host integration and labelling follow Part 15/Part 2 rules [U — not re-read].
- *Forge can automate:* choosing the Class A/B and authorisation route, a test-plan template (conducted and radiated emissions, intentional-radiator tests), SDoC document scaffolding, label and manual-statement checklists, and a warning when the eCFR "last amended" date changes (2026-04-27 at access).
- *Needs a human:* testing by an FCC-recognised accredited lab, TCB grants, and the SDoC signatory (the US responsible party).

**ISED RSS-Gen and RSS-247.**
- *What they govern:* RSS-Gen sets Canada's general certification, labelling, manual and measurement rules. It is now Issue 6 (30 Jul 2026, amended 15 Sep 2026), with a one-year transition from Issue 5 [V]. RSS-247 Issue 4 (24 Jul 2025) covers DTS, FHSS and LE-LAN radios in 902–928 MHz, 2.4 GHz and 5 GHz [V].
- *Product triggers:* any licence-exempt radio sold in Canada. These are Category I devices, which need a TAC from ISED or a certificate from a recognised certification body [R].
- *Forge can automate:* a lookup of which RSS applies, a transition-date calendar, bilingual (EN/FR) label and manual checklists, and cross-mapping of test cases to FCC Part 15.247/15.407 [U].
- *Needs a human:* an accredited lab, a certification body, and ISED registration.

**EU RED 2014/53/EU, Delegated Regulation 2022/30 and EN 18031.**
- *What it governs:*
  - From 1 Aug 2025, internet-connected radio equipment, plus toys, childcare and wearable radio equipment that process personal data, must meet Art. 3(3)(d) (network protection), (e) (privacy) and (f) (fraud) [V].
  - EN 18031-1/-2/-3:2024 give presumption of conformity *only if* no restricted clause is triggered: no "no-password" option, parental control for toys and childcare, and the -3 secure-update criteria excluded [V].
  - If any restriction applies, or the standards are not applied in full, a notified body is needed for those articles [R].
- *End date:* the regime ends on 11 Dec 2027, when the CRA takes over (2026/339) [V].
- *Forge can automate:*
  - a decision tree for 3(3)(d)/(e)/(f) applicability;
  - an EN 18031 mechanism checklist (authentication, secure update, secure storage, logging and so on), written in Forge's own words;
  - a "restricted-clause tripwire" check (e.g. does the design allow a blank password?);
  - reuse of the same evidence toward CRA Annex I.
- *Needs a human:* the risk assessment, the notified-body route, and signing the declaration of conformity.

**CISPR 32 / CISPR 35 (EN 55032 / EN 55035).**
- *What they govern:* EMC emission (32) and immunity (35) of multimedia equipment (IT, AV and broadcast receivers) up to 600 V [V].
- *Product triggers:* in the EU these are the usual harmonised routes to presumption of conformity under the EMC Directive 2014/30/EU [R]. Radio products also use the ETSI EN 301 489 series under RED Art. 3(1)(b) [U].
- *Editions:* both IEC documents reach their stability date in 2026. CISPR 32 Ed. 3 is reported to be close to publication (about Dec 2026) [R]. EN adoption and OJ citation will lag behind that, so Forge must not assume Ed. 3 gives EU presumption of conformity.
- *Forge can automate:* a Class A/B determination prompt, a port-by-port emissions and immunity test-plan template, and performance-criteria (A/B/C) prompts.
- *Needs a human:* an accredited EMC lab (ISO/IEC 17025) and interpretation of the results.

**ETSI EN 303 645 V3.1.3.**
- *What it governs:* a consumer-IoT security baseline: no universal default passwords, a vulnerability-disclosure policy, software updates, secure storage and communication, and data minimisation [V version; U content].
- *Status:* not itself mandatory. It is widely used as the basis for national schemes and maps to EN 18031 and CRA Annex I [R].
- *Forge can automate:* a provision-by-provision self-assessment template (IDs and short paraphrases only) and SBOM/VDP artefacts.
- *Needs a human:* third-party assessment where a scheme requires one.

**NIST IR 8259 / 8259A / 8259B.**
- *What they govern:* voluntary US guidance for IoT manufacturers. IR 8259 Rev. 1 (final 20 Apr 2026) covers pre- and post-market activities across the whole lifecycle, including end of life [V]. 8259A defines device technical capabilities (identity, configuration, data protection, logical access, software update, state awareness) and 8259B defines supporting non-technical capabilities [V dates; U content].
- *Product triggers:* not mandatory. Relevant to US federal procurement (SP 800-213) and to the US IoT labelling programme [U].
- *Forge can automate:* capability checklists that also map to EN 303 645 and CRA Annex I.

**EU Cyber Resilience Act (Regulation (EU) 2024/2847).**
- *What it governs:* horizontal cybersecurity rules for "products with digital elements", i.e. hardware and software, including remote data processing [V].
- *Timeline* [V]:
  - entry into force 10 Dec 2024;
  - rules for notified conformity-assessment bodies from 11 Jun 2026;
  - **reporting duties from 11 Sep 2026** (Art. 14), which apply even to products placed on the market before 11 Dec 2027 (Art. 69(3));
  - everything else, including Annex I essential requirements, SBOM, CE marking and the support period, from **11 Dec 2027**.
- *Reporting:* timelines are 24 h, 72 h, and a final report within 14 days (vulnerabilities) or 1 month (incidents), via ENISA's SRP, which is live [V].
- *Harmonised standards:* 41 are requested under M/606, but none were confirmed cited as of access. Until they are cited, conformity rests on the Annex I text plus the Commission guidance of 27 Jul 2026 [V/U].
- *Forge can automate:* SBOM generation (CycloneDX/SPDX), a vulnerability-handling and CVD policy template, a 24 h/72 h/14 d/1 month reporting runbook with clocks, a support-period declaration prompt, an Annex III/IV class screener (important or critical product?), and a technical-documentation skeleton.
- *Needs a human:* the product classification decision, the conformity-assessment module or notified body, the EU declaration of conformity, and the actual SRP submissions (an authorised person).

**OWASP ASVS 5.0.0.**
- *What it governs:* a web and application security verification requirements catalogue with three levels [V version; U structure].
- *Status:* voluntary. A good checklist source for the software side of CRA Annex I and for Forge code-review gates.
- *Forge can automate:* citing requirement IDs (v5.0.0-prefixed) in review checklists. Pin the version, because IDs changed between 4.x and 5.0 [R].

## Implications for Forge
1. **Ship a CRA reporting runbook now.** Article 14 has been live since 11 Sep 2026 and covers products already on the market. Forge should include a `security-incident` rule that starts 24 h, 72 h and 14 d / 1 month clocks and points to the ENISA SRP. The rule must say that a named human submits, never Forge.
2. **Treat RED cybersecurity as a bridge to the CRA.** Rules should warn that 2022/30 ends on 11 Dec 2027. Evidence gathered for EN 18031 should be tagged so it can be reused toward CRA Annex I.
3. **Add EN 18031 restricted-clause tripwires.** Check for a password-optional mode, missing parental control in toy or childcare radio products, and -3 secure-update criteria. Flag each as "no presumption: notified body route likely".
4. **Store dated snapshots, not "current" claims.** RoHS exemption expiry tables, the REACH Candidate List count, the eCFR last-amended date and ISED issue numbers all change during 2026–2027. Each rule should carry `as_of` and `source_url` fields plus a staleness warning, e.g. after 180 days.
5. **Flag BOM substances at line-item level.** Record the RoHS exemption code and expiry date, SVHC hits above 0.1 % w/w, and the SCIP-required flag. Forge outputs are "flags for review", never "compliant".
6. **Make SBOM a first-class artefact.** CRA Annex I and EN 303 645 both expect it. Generate it in CI and link it from the technical file.
7. **Keep test-plan templates edition-aware.** CISPR 32 Ed. 3 is imminent. Templates should pin "CISPR 32:2015+A1:2019 / EN 55032:2015+A11+A1:2020" until an EN and OJ citation of Ed. 3 is confirmed.
8. **Use a jurisdiction matrix.** The same radio can need FCC Part 15 (SDoC or Certification), ISED RSS-Gen Issue 6 with RSS-247 Issue 4, and EU RED (3.1(a)/(b), 3.2 and 3.3(d–f)). Forge should generate one matrix per product, where each cell names the human or lab that signs.
9. **Never reproduce text.** Standards and requirement IDs are cited by number with a short paraphrase. ASVS and EN 303 645 IDs are fine. EN 18031, CISPR and IEC clause text must not be copied.

## Not found / discrepancies
- **ECHA site (echa.europa.eu) returned 403.** The Candidate List count (253, 4 Feb 2026) comes from test houses [R]. I could not confirm whether a June/July 2026 update happened. SCIP scope and dates are [U].
- **The EC RoHS topic page looks outdated.** It does not list the 2025 delegated directives or Directive 2025/2456, although EUR-Lex confirms both 2025/2364 and 2025/2456.
- **EUR-Lex rate-limited** fetches of 2025/1802 and 2025/2363, so their details are [R].
- **"Pack 29" RoHS exemption consultation** (29 May–1 Aug 2026, from the abandoned R5 stub) could not be re-verified [U]. It is left out of the table.
- **Stub correction:** the R5 stub listed "Directive (EU) 2025/2456" as a RoHS amendment. That is correct, but it is a Parliament and Council directive, not a Commission delegated act, and it applies from 13 Aug 2027 [V].
- **CISPR 32 Ed. 3** FDIS stage and expected Dec 2026 publication come from a secondary source (genorma) only. The IEC project page was not checked.
- **EN 55032/EN 55035** OJ citation details under the EMC Directive (Implementing Decision 2019/1326 as amended) were not checked on EUR-Lex [R].
- **CRA harmonised standards:** I found no evidence that any is cited in the OJ. The deliverable deadlines under M/606 were not confirmed. Proposed amendments to the CRA, such as the "digital omnibus", were not investigated [U].
- **The owasp.org ASVS project page returned 404.** The version was taken from OWASP's official GitHub releases instead.
- **Transition dates:** the RSS-247 Issue 3→4 transition (6 months) is [R]. The ISED RSS list page did not show RSS-Gen or RSS-247 rows; it is dynamically loaded.
- **Not covered, possibly relevant:** the FCC "Cyber Trust Mark" (US IoT label), the ETSI EN 301 489 series, the EU Battery Regulation 2023/1542 and the EU POPs Regulation.

## Sources

| # | Source | Body | URL | Used for |
|---|---|---|---|---|
| 1 | RoHS Directive topic page | European Commission (DG ENV) | https://environment.ec.europa.eu/topics/waste-and-recycling/rohs-directive_en | 10 substances; 2015/863 |
| 2 | Delegated Directive (EU) 2025/2364 | EUR-Lex | https://eur-lex.europa.eu/eli/dir_del/2025/2364/oj/eng | Lead exemptions 6(a)–(c), dates |
| 3 | Directive (EU) 2025/2456 | EUR-Lex | https://eur-lex.europa.eu/eli/dir/2025/2456/oj/eng | ECHA tasks, 13 Aug 2027 |
| 4 | SGS: RoHS exemptions updated (Dec 2025) | SGS (secondary) | https://www.sgs.com/en-hk/news/2025/12/exemptions-of-rohs-directive-updated | 2025/1802, 2025/2363 |
| 5 | SGS: Candidate List 253 SVHCs (Feb 2026) | SGS (secondary) | https://www.sgs.com/en/news/2026/02/safeguards-02126-echa-expands-candidate-list-to-253-svhcs | Candidate List count |
| 6 | eCFR versioner API, title 47 part 15 (§15.101, §15.201; versions list) | NARA/OFR (eCFR) | https://www.ecfr.gov/api/versioner/v1/versions/title-47.json?part=15 | Part 15 rules; last amended 2026-04-27 |
| 7 | RSS-Gen Issue 6 | ISED | https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-gen-general-requirements-compliance-radio-apparatus | Issue, date, transition |
| 8 | RSS-247 Issue 4 | ISED | https://ised-isde.canada.ca/site/spectrum-management-telecommunications/en/devices-and-equipment/radio-equipment-standards/radio-standards-specifications-rss/rss-247-digital-transmission-systems-dtss-frequency-hopping-systems-fhss-and-licence-exempt-local | Issue, date |
| 9 | RED topic page | European Commission (DG GROW) | https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en | 2022/30 status; repeal |
| 10 | Implementing Decision (EU) 2025/138 | EUR-Lex | https://eur-lex.europa.eu/eli/dec_impl/2025/138/oj | EN 18031 citation and restrictions |
| 11 | Delegated Regulation (EU) 2026/339 | EUR-Lex | https://eur-lex.europa.eu/eli/reg_del/2026/339/oj | Repeal of 2022/30 w.e.f. 11 Dec 2027 |
| 12 | CISPR 32:2015+AMD1:2019 CSV | IEC Webstore | https://webstore.iec.ch/en/publication/65836 | Ed. 2.1, stability date |
| 13 | CISPR 35:2016 | IEC Webstore | https://webstore.iec.ch/en/publication/25667 | Ed. 1.0, stability date |
| 14 | CISPR 32 ED3 project listing | genorma (secondary) | https://genorma.com/en/standards/cispr-32-ed3 | Ed. 3 FDIS, expected date |
| 15 | EN 55032 product page | BSI (secondary) | https://knowledge.bsigroup.com/products/electromagnetic-compatibility-of-multimedia-equipment-emission-requirements-3 | EN 55032 edition |
| 16 | EN 303 645 deliverables directory | ETSI | https://www.etsi.org/deliver/etsi_en/303600_303699/303645/ | V3.1.3 (2024-09) |
| 17 | NIST IR 8259 Rev. 1 | NIST CSRC | https://csrc.nist.gov/pubs/ir/8259/r1/final | Final 2026-04-20 |
| 18 | NIST IR 8259A / 8259B | NIST CSRC | https://csrc.nist.gov/pubs/ir/8259/a/final ; https://csrc.nist.gov/pubs/ir/8259/b/final | Dates, no revisions |
| 19 | Regulation (EU) 2024/2847 (CRA), consolidated HTML | EUR-Lex | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R2847 | Arts. 14, 69, 71 |
| 20 | CRA policy page | European Commission (DG CNECT) | https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act | Timeline; 27 Jul 2026 guidance |
| 21 | CRA standardisation page | European Commission | https://digital-strategy.ec.europa.eu/en/policies/cra-standardisation | M/606, 41 standards |
| 22 | CRA reporting page | European Commission | https://digital-strategy.ec.europa.eu/en/policies/cra-reporting | SRP live 11 Sep 2026 |
| 23 | ASVS releases | OWASP (GitHub org) | https://github.com/OWASP/ASVS/releases | v5.0.0, 30 May 2025 |
