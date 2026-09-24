# R5b — Standards: safety, risk analysis, systems engineering
- Date accessed: 2026-09-25 · Author: R5 sub-research agent (Phase 1) · Status: salvaged — parent R5 agent was stopped to save usage; this is the sub-agent's complete returned report, unedited.
- Tags: [V] verified on issuing body / manufacturer page · [R] reported (secondary) · [U] unverified

# Research report: current editions and status of 13 safety, risk and systems-engineering standards and handbooks (checked 2026-09-25)

**Key findings:**
- **Transitions under way:** IEC 61508 Ed.3 is at the vote stage (CDV). ISO 26262 Ed.3 reached the DIS stage on 2026-08-04. DO-254A / ED-80A are targeted for Dec 2027 / Mar 2028. IEC 60601-1 Ed.4 is not expected before about 2029–2031. The EU withdrawal date (dow) for the 2020 edition of EN IEC 62368-1 is 2027-02-15.
- **EU gap for 62368-1:** only EN 62368-1:2014 appears to be cited in the EU Official Journal (OJ) under the Low Voltage Directive (LVD). The 2024 edition will probably not be cited.
- **No new editions found:** STPA Handbook, AIAG & VDA FMEA Handbook, NASA SE Handbook Rev2, NPR 7123.1D, INCOSE SEH 5th edition and DO-178C are all still current.
- **Search budget ran out:** the session hit its 200-search limit near the end. EU harmonisation status for 61508 and 26262 is therefore unverified.
- **Blocked sites:** iso.org, faa.gov, incose.org, ieeexplore and acm.org refused automated fetches. I used committee.iso.org and other sources instead, and tagged those claims to match.

Tags: **[V]** verified on the issuing body's (or its publisher's) own page · **[R]** reported by a secondary source · **[U]** unverified.

## (1) Summary table

| Standard | Current edition / revision | Year | Issuing body | Status / transition notes | Tag | Source URL |
|---|---|---|---|---|---|---|
| IEC 62368-1 | Ed. 4.0 (there is a corrected version dated 2025-08) | 2023-05-26 | IEC TC 108 | IEC stability date is 2026. Ed.4 replaces Ed.3 (2018). | [V] | https://webstore.iec.ch/en/publication/69308 |
| EN IEC 62368-1:2024 (+A11:2024) | EU adoption of IEC Ed.4 | 2024-04 | CENELEC | Approved 2024-02-15. National adoption deadline (dop) 2025-02-15. Withdrawal of conflicting national standards (dow) **2027-02-15**. Supersedes EN IEC 62368-1:2020 and its amendments (+A11:2020). | [R] (EN foreword seen in the Slovenian national (SIST) sample copy) | https://cdn.standards.iteh.ai/samples/74334/13887e080eb8466fa27bb8bd180a52ca/SIST-EN-IEC-62368-1-2024.pdf |
| EN 62368-1 OJ status (LVD 2014/35/EU) | 2014 ed. cited; 2020 ed. never cited | — | European Commission | The 2020+A11 edition was never cited in the OJ. SIQ (Dec 2025) reports the 2024+A11 edition will **not** be cited: the harmonised-standards consultant (HAS) review raised about 500 comments and TC108X stopped the process. The Commission's LVD decision 2023/2723 has no 62368 entries. | [R] Nemko, SIQ; [V] negative check on EUR-Lex 2023/2723 | https://www.siq.si/en/news/update-on-en-iec-62368-12024-a112024-and-ojeu-harmonization-status/ ; https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ%3AL_202302723 |
| UL 62368-1 (US/Canada) | Ed. 4 (joint with CSA C22.2 No. 62368-1-2025) | 2025-07-31 | UL Standards & Engagement / CSA | UL: active and effective on publication. CSA: enforcement from 2026-04-30 [R]. No official cutoff date for the 3rd edition [R]. | [V] UL; [R] CSA | https://www.shopulstandards.com/ProductDetail.aspx?productId=UL62368-1_4_S_20250731 |
| IEC 60601-1 | Ed. 3.2 consolidated version (2005+AMD1:2012+AMD2:2020; includes COR3:2022) | 2020-08-20 | IEC SC 62A | IEC stability date 2028. Ed.4 is being drafted: collateral standards merged in, 12 hazard clusters A–L [V]. CDV (vote draft) expected late 2028; publication about 2029–2031 [R]. | [V] / [R] | https://webstore.iec.ch/en/publication/67497 ; https://assets.iec.ch/public/sc62a/IEC_60601-1_Ed._4.0_Design_Specification_2023-11-03.pdf |
| EN 60601-1 under MDR | EN 60601-1:2006 with amendments; A13:2024 shown | — | European Commission | Cited as entry 65 of Implementing Decision (EU) 2021/1182, consolidated 2026-06-17. My fetch only surfaced A13:2024, not the full chain of amendments. | [V] with caveat | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02021D1182-20260617 |
| IEC 60601-1-2 (EMC) | Ed. 4.1 consolidated version (2014+AMD1:2020) | 2020-09-01 | IEC SC 62A | IEC stability date 2028. Will fold into 60601-1 Ed.4. No EN 60601-1-2 entry found in the MDR consolidation. | [V] | https://webstore.iec.ch/en/publication/67554 |
| IEC 61508 (Parts 1–7) | Ed. 2.0 | 2010-04-30 | IEC SC 65A | IEC stability date 2027. Ed.3 is at CDV stage: Part 1 CDV (65A/1164) circulated 2025-02-14, closed 2025-05-09 [R]; Part 4 CDV 65A/1166 [R]. The 61508 Association expects Ed.3 in early 2027 [R]. IEC TR 61508-3-3:2025 (object-oriented software) was published 2025-07-16 [V]. | [V] / [R] | https://webstore.iec.ch/en/publication/5515 ; https://61508.org/knowledge/standards-development/ |
| ISO 26262 | 2nd edition | 2018-12-17 | ISO TC 22/SC 32 | The 2018 edition has been marked "to be revised" (stage 90.92) since 2024-07-08. The 3rd-edition drafts (ISO/DIS 26262-1 and -5) were registered at DIS stage 40.00 on **2026-08-04**; a 12-week ballot is next. Publication date not confirmed. | [V] | https://committee.iso.org/standard/68383.html ; https://committee.iso.org/standard/90020.html ; https://committee.iso.org/standard/90024.html |
| DO-178C / ED-12C | DO-178C (with supplements DO-330/331/332/333) | 2011 (13 Dec 2011 per AC 20-115D [R]) | RTCA / EUROCAE | No DO-178D found. Recognised by FAA AC 20-115D (2017-07-21 [R]) and EASA AMC 20-115D (published together Oct 2017 [V]). RTCA SC-240 is working on DO-395, a COTS/open-source supplement [R]. | [V] / [R] | https://www.rtca.org/do-178/ ; https://www.easa.europa.eu/en/newsroom-and-events/news/harmonised-software-easa-amc-and-faa-ac-20-115d-have-been-published |
| DO-254 / ED-80 | Original edition | April 2000 | RTCA SC-180 / EUROCAE WG-46 | Recognised via FAA AC 20-152A and EASA AMC 20-152A [V]. AC 20-152A issued 2022-10-07 [R]. Revision under way: RTCA SC-243 targets **DO-254A in Dec 2027**; EUROCAE WG-128 targets **ED-80A by 2028-03-31**. | [V] / [R] | https://www.rtca.org/wp-content/uploads/2025/07/SC-243-TOR-Rev2-Approved-2025-06-26.pdf ; https://www.eurocae.net/working-group/wg-128/ |
| AIAG & VDA FMEA Handbook | 1st edition (a later "2nd printing" exists [R]) | June 2019 | AIAG / VDA QMC | Only erratum listed: June 2020. No 2nd edition found. | [V] | https://webshop.vda.de/QMC/en/aiag-vda-fmea-handbook_eng ; https://www.aiag.org/training-and-resources/manuals/manual-erratas |
| STPA Handbook | Leveson & Thomas | March 2018 | MIT PSASS (Partnership for Systems Approaches to Safety and Security) | Free PDF; Japanese, Chinese and Korean translations exist. No newer edition listed. | [V] | https://psas.scripts.mit.edu/home/get_file.php?name=STPA_Handbook.pdf |
| NASA SE Handbook | NASA/SP-2016-6105 Rev2 | 2016 (web version updated 2024-03-27) | NASA | No Rev 3 found. | [V] / [R] | https://www.nasa.gov/reference/systems-engineering-handbook/ |
| NPR 7123.1 | Rev **D**, updated with Change 2 | Effective 2023-07-05 | NASA OCE (Office of the Chief Engineer) | Expires 2028-07-05. | [V] | https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1B |
| INCOSE SE Handbook | 5th edition | June 2023 | INCOSE / Wiley | Aligned to ISO/IEC/IEEE 15288:2023. No 6th edition found. | [V] (publisher page; incose.org returned 403) | https://www.wiley.com/INCOSE+Systems+Engineering+Handbook%2C+5th+Edition-p-9781119814290 |
| EARS (paper) | Mavin, Wilkinson, Harwood, Novak, "Easy Approach to Requirements Syntax (EARS)", RE'09 (17th IEEE Int'l Requirements Engineering Conf.), pp. 317–322, **DOI 10.1109/RE.2009.9** | 2009 | IEEE | The DOI resolves to IEEE Xplore document 5328509. | [V] DOI resolution; [R] pages (Univ. of Manchester repository) | https://research.manchester.ac.uk/en/publications/easy-approach-to-requirements-syntax-ears/ |

## (2) Per-item summaries

**IEC/EN/UL 62368-1.**
- **Scope and triggers:** safety of audio/video, IT and communications equipment using a hazard-based model. Energy sources (electrical, thermal, mechanical, radiation, fire) are classified and safeguards are specified against each. Any mains- or battery-powered AV/ICT product triggers it: chargers, PSUs, routers, laptops, displays.
- **Software can automate:**
  - energy-source classification worksheets;
  - safeguard-to-energy-source traceability matrices;
  - checks that a component or critical-parts list is complete;
  - markings and labelling checklists;
  - tracking which edition, national deviations and dates apply per market.
- **Needs a qualified human:** a test lab or certification body (NRTL, the IECEE CB Scheme) for testing and the report. In the EU, the manufacturer must justify LVD compliance. That is harder when the edition used is not cited in the OJ.

**IEC 60601-1 (+ 60601-1-2).**
- **Scope and triggers:** basic safety and essential performance of medical electrical equipment, with collateral standards for EMC, usability and alarms. Any device with an applied part or mains/battery power sold as medical equipment triggers it.
- **Software can automate:**
  - the risk-management-file cross-references to ISO 14971;
  - essential-performance lists;
  - applicability matrices showing which collateral and particular standards apply;
  - EMC test-plan templates;
  - traceability lints linking hazards to requirements to tests.
- **Needs a qualified human:** an accredited test lab, the CB Scheme and an EU notified body under the MDR.

**IEC 61508.**
- **Scope and triggers:** the generic functional-safety standard for electrical, electronic and programmable electronic safety functions. It covers the safety lifecycle, safety integrity levels (SIL 1–4), hardware metrics and software techniques. It is the parent standard for sector standards such as 61511, 62061 and 26262. Any product where a control or protection function reduces risk triggers it.
- **Software can automate:**
  - SIL-determination templates;
  - traceability from safety requirements through design to verification;
  - checks that the techniques-and-measures tables are complete;
  - FMEDA spreadsheets that compute diagnostic coverage and PFH/PFD figures;
  - coding-standard and static-analysis gating.
- **Needs a qualified human:** a functional-safety assessor, often a certification body such as TÜV or exida, for independent assessment and certification.

**ISO 26262.**
- **Scope and triggers:** functional safety of electrical/electronic systems in series-production road vehicles. It covers hazard analysis and risk assessment (HARA), ASIL levels A–D, safety goals, and hardware and software development. The 3rd edition is expected to cover ML, SOTIF alignment and predictive maintenance [R]. Any automotive electrical/electronic item or supplier component triggers it.
- **Software can automate:**
  - HARA and safety-goal templates;
  - checks on ASIL decomposition rules;
  - traceability of safety requirements across the hierarchy of goals, functional, technical, hardware and software requirements;
  - hardware metrics (the SPFM, LFM and PMHF failure metrics);
  - work-product completeness checklists.
- **Needs a qualified human:** confirmation reviews, functional-safety audits and the assessment by an independent assessor (independence levels I0–I3). OEM acceptance also rests with people.

**DO-178C / ED-12C.**
- **Scope and triggers:** development assurance for airborne software. Objectives scale by software level A–E. Any software in type-certificated aircraft or TSO equipment triggers it.
- **Software can automate:**
  - templates for the certification plans (PSAC, SDP, SVP, SCMP, SQAP);
  - bidirectional traceability from high-level requirements through low-level requirements and code to tests;
  - structural coverage measurement (statement, decision, MC/DC);
  - objective-by-level compliance matrices.
- **Needs a qualified human:** FAA/EASA certification liaison. Stages of Involvement (SOI) audits are done by FAA/EASA staff or delegated DERs. Tool qualification under DO-330 also needs authority acceptance.

**DO-254 / ED-80.**
- **Scope and triggers:** design assurance for airborne electronic hardware, especially custom devices such as FPGAs and ASICs, at DAL A–E. AC 20-152A adds its own objectives for COTS devices and circuit board assemblies.
- **Software can automate:**
  - requirements-to-HDL-to-test traceability;
  - elemental analysis and code-coverage reports;
  - checklists of the extra AC 20-152A objectives.
- **Needs a qualified human:** the certification authority or DER.

**AIAG & VDA FMEA Handbook.**
- **Scope and triggers:** Design FMEA, Process FMEA, and a supplemental FMEA for Monitoring and System Response (FMEA-MSR). It uses a 7-step method: planning, structure analysis, function analysis, failure analysis, risk analysis, optimisation, documentation [U]. Automotive suppliers under IATF 16949 are expected to use it.
- **The rating scales (my own summary; the handbook is paywalled, so [U]):**
  - **Severity** rates how bad the worst effect of a failure mode is, from 1 (no noticeable effect) to 10. The top ratings are reserved for effects on safe operation, health or regulatory compliance.
  - **Occurrence** rates how likely the failure *cause* is to happen, judged mainly by how effective the prevention controls are and how proven the design or process is. 1 means the cause has effectively been designed out.
  - **Detection** rates how well the current detection controls would catch the cause or failure mode before the design is released or the part ships. 10 means there is no detection method; 1 means it is always caught.
  - FMEA-MSR swaps Occurrence and Detection for Frequency and Monitoring ratings.
- **Action Priority (AP):** the old Risk Priority Number (RPN) was S×O×D. AP replaces it with a lookup over S/O/D combinations that gives High, Medium or Low. It weights Severity first, then Occurrence, then Detection. This stops a high-severity risk from hiding behind a modest product score. High means the team must act or document why current controls are enough; Medium means it should; Low means it could.
- **Software can automate:** the structure, function and failure trees; the AP lookup; carrying items into the control plan; and flags for High-AP items without actions.
- **Needs a qualified human:** a cross-functional team and a trained facilitator to judge the ratings. Customer approval also rests with people.

**STPA Handbook (MIT, March 2018).**
- **Scope:** a systems-theoretic hazard analysis. It fits software-intensive and human-in-the-loop systems better than failure-based methods. The four steps below are verified against the handbook's Chapter 2 and written in my own words.
- **The four steps:**
  1. **Define the purpose of the analysis.** Name the losses stakeholders will not accept. Set the system boundary. Derive system-level hazards and constraints.
  2. **Model the control structure.** Build a hierarchical model of feedback loops: controllers, the control actions they issue and the feedback they receive. Start abstract and refine it.
  3. **Identify unsafe control actions (UCAs).** For each control action, check whether it is hazardous when not given, when given, when given too early, too late or out of order, or when stopped too soon or applied too long. Turn each UCA into a controller constraint.
  4. **Identify loss scenarios.** Explain why a UCA could arise, such as bad feedback, a wrong process model or flawed logic. Also explain why a correct command might not be carried out, such as actuator or process faults. Use the scenarios to drive requirements and tests.
- **Software can automate:** control-structure diagrams, UCA tables, scenario-to-requirement traceability, and completeness lints.
- **Needs a qualified human:** domain experts. A regulator or assessor accepts the analysis only as part of a wider safety case.

**NASA SE Handbook Rev2 and NPR 7123.1D.**
- **Scope:** NPR 7123.1D holds the binding NASA requirements (the 17 common technical processes [U], life-cycle reviews, the SE Management Plan). The handbook (SP-6105) is non-binding guidance on how to meet them. Both apply to NASA programmes, projects and contractors.
- **Software can automate:**
  - templates for the SE Management Plan and the review entrance/success criteria;
  - requirement quality lints;
  - verification matrices;
  - tailoring and compliance matrices.
- **Needs a qualified human:** the Technical Authority, review boards and waiver approvals.

**INCOSE SE Handbook, 5th edition.**
- **Scope:** a practitioner guide to the ISO/IEC/IEEE 15288:2023 life-cycle processes. It is not a regulatory requirement. INCOSE's CSEP/ASEP certification exams are based on it [U].
- **Software can automate:** process templates, tailoring checklists and MBSE scaffolding.
- **Needs a qualified human:** engineering judgement. Certification is issued by INCOSE, not by a regulator.

**EARS.**
- **What it is:** a lightweight template syntax for natural-language requirements. Each requirement is a single "the system shall" sentence, and an optional leading clause says when it applies. This removes much of the ambiguity of free text without needing a formal notation.
- **The six patterns, with made-up examples for a fictional "HydroSense" battery-powered handheld soil-moisture sensor:**
  - **Ubiquitous** (always active, no keyword): "The HydroSense sensor shall store each moisture reading with a UTC timestamp."
  - **Event-driven** (`When` a trigger occurs): "When the user presses the Measure button, the HydroSense sensor shall display a moisture reading within 2 seconds."
  - **State-driven** (`While` a condition holds): "While battery charge is below 10 %, the HydroSense sensor shall disable the display backlight."
  - **Unwanted behaviour** (`If … then`, for faults and misuse): "If the probe temperature is outside −20 °C to +60 °C, then the HydroSense sensor shall mark the reading as invalid."
  - **Optional feature** (`Where` a variant is fitted): "Where the Bluetooth module is fitted, the HydroSense sensor shall send stored readings to a paired phone on request."
  - **Complex** (keywords combined): "While field-logging mode is active, when the sampling interval elapses, the HydroSense sensor shall record a reading to flash memory."
- **Software can automate:** almost all checking. A linter can check keyword order, that there is one "shall" and one system name, and flag vague words such as "quickly" or "user-friendly". It can classify requirements by pattern and suggest `If/then` counterparts for event requirements that have none.
- **Needs a qualified human:** only for whether a requirement is semantically correct and complete.

## (3) Discrepancies / not found

- **EN 62368-1 in the OJ:** Nemko reports the 2014 edition is cited and the 2020 edition is not. SIQ says the "existing harmonized version" stays listed but does not name the edition. I could not open the Commission's LVD summary list to confirm directly. The dow for the 2014 edition was extended to 2024-07-06 [R, Nemko]. SIQ says its removal from the OJ depends on the Commission.
- **UL 62368-1 3rd-edition cutoff:** the "2027-02-15" date sometimes cited is unconfirmed (SIQ says so explicitly). It matches the EN dow and may have been borrowed from it.
- **IEC 60601-1 Ed.4 publication:** secondary sources give 2029–2030 and, more recently, about 2031. I could not open the Eisner Safety pages; the dates come from search snippets. IEC's own design spec confirms the scope and clusters but gives no dates in the pages I read.
- **EN 60601-1 MDR citation:** my fetch returned only "EN 60601-1:2006/A13:2024" for entry 65. I could not confirm whether A1, A12 and A2 are also listed. Check the EUR-Lex text directly.
- **IEC 61508 Ed.3 timing:** the 61508 Association says the "CDV [is] due early 2026". Other sources show CDVs circulating from Feb 2025 (65A/1164, 65A/1166), and German draft editions (E DIN) of them were issued in 2026. There may be a second CDV round. The publication forecast (early 2027) is [R] only; the IEC project dashboard returned 403.
- **ISO 26262 Ed.3 publication:** UL says Q2 2027, SRES says about Oct 2027, and Hermes Solution says 2029. The ISO pages confirm DIS registration only (2026-08-04). Given that DIS stage, the Hermes 2029 date looks inconsistent.
- **DO-254A dates:** RTCA targets Dec 2027 and EUROCAE targets 2028-03-31 for ED-80A.
- **FAA pages:** faa.gov returned 403, so the AC 20-115D date (2017-07-21) and AC 20-152A date (2022-10-07) are [R]. Recognition of DO-254/ED-80 through AC/AMC 20-152A is confirmed in RTCA's own terms-of-reference document [V].
- **Not researched (search budget exhausted):** whether EN 61508 or ISO 26262 are harmonised or referenced in EU legislation [U]. I believe neither is OJ-cited as a harmonised standard, but I did not verify it. The DO-395 status also rests on a search snippet [R].
- **AIAG & VDA FMEA content:** the S/O/D and AP descriptions come from background knowledge, not the paywalled handbook [U]. I did not reproduce the AP table.

## (4) Sources

- IEC webstore: https://webstore.iec.ch/en/publication/69308 · https://webstore.iec.ch/en/publication/67497 · https://webstore.iec.ch/en/publication/67554 · https://webstore.iec.ch/en/publication/2603 (60601 series bundle, 2026-07-10, not a new edition) · https://webstore.iec.ch/en/publication/5515 · https://webstore.iec.ch/en/publication/5516 · https://webstore.iec.ch/en/publication/99554
- IEC SC 62A 60601-1 Ed.4 design spec: https://assets.iec.ch/public/sc62a/IEC_60601-1_Ed._4.0_Design_Specification_2023-11-03.pdf
- EN IEC 62368-1:2024 foreword (SIST sample): https://cdn.standards.iteh.ai/samples/74334/13887e080eb8466fa27bb8bd180a52ca/SIST-EN-IEC-62368-1-2024.pdf
- SIQ (Dec 2025) OJ status: https://www.siq.si/en/news/update-on-en-iec-62368-12024-a112024-and-ojeu-harmonization-status/
- SIQ UL/CSA 4th edition: https://www.siq.si/en/news/ul-csa-62368-1-4th-edition-timeline-transition-from-the-3rd-edition/
- Nemko: https://www.nemko.com/blog/hazard-based-2nd-vs-3rd-vs-4th-edition · https://www.nemko.com/blog/en-iec-62368-1-ed.-3-extension-of-withdrawal
- EUR-Lex LVD decision 2023/2723: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ%3AL_202302723
- EUR-Lex MDR 2021/1182 consolidated: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02021D1182-20260617 · https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32021D1182
- UL Standards & Engagement: https://www.shopulstandards.com/ProductDetail.aspx?productId=UL62368-1_4_S_20250731
- UL (TC 62, Oct 2023): https://www.ul.com/insights/current-state-iec-tc-62-standardization
- Eisner Safety (60601-1 Ed.4 timeline, from search snippets): https://eisnersafety.com/2026/07/28/iec-60601-1-4th-edition-in-one-place/
- 61508 Association: https://61508.org/knowledge/standards-development/
- DIN Media (61508-4 CDV draft): https://www.dinmedia.de/en/draft-standard/din-en-iec-61508-4/404501704
- ISO committee pages: https://committee.iso.org/standard/68383.html · https://committee.iso.org/standard/90020.html · https://committee.iso.org/standard/90024.html
- ISO 26262 Ed.3 secondary: https://www.ul.com/sis/blog/what-to-expect-with-version-3-of-iso-26262 · https://sres.ai/functional-safety/iso-26262-edition-3-standardization-timing-vocabulary-and-management-of-functional-safety/ · https://www.hermessol.com/global-trend/iso-26262-edition3-work-item-registered-2026
- RTCA DO-178: https://www.rtca.org/do-178/
- RTCA SC-243 terms of reference Rev 2: https://www.rtca.org/wp-content/uploads/2025/07/SC-243-TOR-Rev2-Approved-2025-06-26.pdf
- RTCA March 2026 status report: https://www.rtca.org/wp-content/uploads/2026/03/7-A-March-PMC-Report_03.10.2026v2.pdf
- EUROCAE WG-128: https://www.eurocae.net/working-group/wg-128/
- EASA AMC 20-115D: https://www.easa.europa.eu/en/newsroom-and-events/news/harmonised-software-easa-amc-and-faa-ac-20-115d-have-been-published
- FAA (403, seen via search only): https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1032046 · https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1041323
- AIAG / VDA: https://www.aiag.org/training-and-resources/manuals/details/FMEAAV-1 · https://www.aiag.org/training-and-resources/manuals/manual-erratas · https://webshop.vda.de/QMC/en/aiag-vda-fmea-handbook_eng
- MIT PSASS: https://psas.scripts.mit.edu/home/books-and-handbooks/ · https://psas.scripts.mit.edu/home/get_file.php?name=STPA_Handbook.pdf
- NASA: https://www.nasa.gov/reference/systems-engineering-handbook/ · https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7123&s=1B · https://ntrs.nasa.gov/search.jsp?R=20170001761
- Wiley (INCOSE SEH 5th edition): https://www.wiley.com/INCOSE+Systems+Engineering+Handbook%2C+5th+Edition-p-9781119814290
- EARS: https://doi.org/10.1109/RE.2009.9 (resolves to https://ieeexplore.ieee.org/document/5328509/) · https://research.manchester.ac.uk/en/publications/easy-approach-to-requirements-syntax-ears/ · https://alistairmavin.com/ears/

No files were created. The only local files are WebFetch's automatic PDF caches, which I read to check the SIST foreword, the RTCA terms of reference, the IEC design spec and the STPA Handbook.