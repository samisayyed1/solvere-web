# R5a — Standards: drawings & tolerancing, electronics (IPC), accessibility & ergonomics
- Date accessed: 2026-09-25 · Author: R5 sub-research agent (Phase 1) · Status: salvaged — parent R5 agent was stopped to save usage; this is the sub-agent's complete returned report, unedited.
- Tags: [V] verified on issuing body / manufacturer page · [R] reported (secondary) · [U] unverified

## Current editions of the requested standards (checked 2026-09-25)

**Access limits:**
- iso.org and shop.ipc.org / shop.electronics.org returned HTTP 403 to direct fetches. For ISO, I used three routes:
  - iso.org titles and abstracts as they appear in search results.
  - ISO/TC 213's own committee site (committee.iso.org).
  - The Institute for Standardization of Serbia (iss.rs). It is an ISO member body whose project pages copy ISO's stage codes and dates. Anything from there is tagged [R].
- IPC status comes from electronics.org (IPC now trades as "Global Electronics Association"), which I could read directly.
- My web-search budget ran out near the end, so a few 2026 items could not be checked a second time. They are listed in section 3.

### 1. Status table

| Standard | Current edition / revision | Year | Issuing body | Status / transition notes | Tag | Source |
|---|---|---|---|---|---|---|
| ASME Y14.5 | Y14.5-2018 (R2024) | Issued 11 Feb 2019; reaffirmed with ANSI approval 12 Nov 2024 | ASME | ASME Y14 status sheet (updated 20 Aug 2026) says **REVISION in PROGRESS**: record 25-391, ANSI PINS submitted 18 Feb 2025. The asme.org product page still calls it "stabilized maintenance" (conflict, see §3). No newer edition has been published. | [V] | https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing ; Y14 status PDF: https://cstools.asme.org/csconnect/Filedownload.cfm?thisfile=160.pdf&dir=CommitteeFiles |
| ASME Y14.5.1 | Y14.5.1-2019 | Issued 31 Aug 2020 | ASME | Written as a supplement to **Y14.5-2009**, not Y14.5-2018. Status sheet says **REVISION in PROGRESS**: record 26-1029, PINS submitted 03 Aug 2026. Not reaffirmed. The product page again says "stabilized maintenance". | [V] | https://www.asme.org/codes-standards/find-codes-standards/y14-5-1-mathematical-definition-dimensioning-tolerancing-principles ; same status PDF |
| ISO 8015 | ISO 8015:2011 (2nd ed.) | 2011 | ISO/TC 213 | Confirmed (stage 90.93) on 10 Dec 2021. A revision exists only as a preliminary work item (ISO/PWI 8015). TC 213 says working group WG14 is discussing the next revision. No draft (DIS) found. | [R] (stage); [V] (TC 213 note) | https://www.iso.org/standard/55979.html ; https://iss.rs/en/project/show/iso:proj:55979 ; https://committee.iso.org/sites/tc213/home/projects/ongoing/ongoing-1.html |
| ISO 1101 | ISO 1101:2017 (4th ed.) | Published Feb 2017 | ISO/TC 213 | Confirmed (90.93) on 3 Oct 2022. A revision is at preliminary stage only (ISO/PWI 1101). No 2023–2026 edition exists. | [R] | https://www.iso.org/standard/66777.html ; https://iss.rs/en/project/show/iso:proj:66777 |
| ISO 14405-1 | **ISO 14405-1:2025 (3rd ed.)** | 2025-08 (published 6 Aug 2025) | ISO/TC 213 with CEN/TC 290 | Replaces ISO 14405-1:2016, which is withdrawn. Changes include: a new indication-area syntax, stacked size specifications, "rank-order size" renamed "statistical size", and cones/tori limited to the cases in annexes. | [R] (ISO foreword seen in iTeh preview; stage from iss.rs) | https://www.iso.org/standard/80703.html ; https://iss.rs/en/project/show/iso:proj:80703 |
| ISO 2768-1 | ISO 2768-1:1989 | 1989 | ISO/TC 213 | Stage 90.92 ("to be revised") on 4 Oct 2022. Its replacement, **ISO 2768** (single part, "tolerance limits for general specification of linear and angular sizes"), reached stage **60.00 (under publication) on 2 Jun 2026**. I could not confirm it has been published (60.60) as of 25 Sep 2026. The CEN parallel appears as "FprEN ISO 2768:2026". | [R] | https://www.iso.org/standard/7748.html ; https://iss.rs/en/project/show/iso:proj:7748 ; https://iss.rs/en/project/show/iso:proj:85741 ; https://www.iso.org/standard/85741.html |
| ISO 2768-2 | Withdrawn (1989 ed.) | Withdrawn 4 Feb 2021 | ISO/TC 213 | Stage 95.99 (withdrawn). Replaced by ISO 22081:2021. | [R] | https://www.iso.org/standard/7749.html ; https://iss.rs/en/project/show/iso:proj:7749 |
| ISO 22081 | ISO 22081:2021 (1st ed.) | Published 4 Feb 2021 | ISO/TC 213 | Confirmed (90.93) on 19 Jun 2026. Replaces ISO 2768-2 only, not 2768-1. | [R] | https://www.iso.org/standard/72514.html ; https://iss.rs/en/project/show/iso:proj:72514 |
| IPC-2221 | Rev C | Dec 2023 | IPC (Global Electronics Association), task group D-31b | Rev B was Nov 2012. No Rev D draft is listed on the IPC status page. | [V] | https://www.electronics.org/ipc-document-revision-table |
| IPC-2222 | Rev B | Oct 2020 | IPC, D-31b | No draft is listed on the status page. | [V] | same |
| IPC-7351 | Rev B | Jun 2010 | IPC, subcommittee 1-13 | Marked **"No Longer Maintained"**. There is no Rev C: a "7351C" was never released. | [V] | same |
| IPC-7352 | Original (no revision letter) | Table says Jul 2023; document header says May 2023 | IPC, subcommittee 1-13 | This is a *guideline*, the de facto successor to 7351. Its cover says it supersedes "IPC-7352 – June 2010", which matches 7351B's date but never names 7351B (see §3). | [V] | same ; https://www.electronics.org/TOC/IPC-7352-TOC.pdf |
| IPC-A-610 | Rev J | Mar 2024 (press release dated 8 Apr 2024) | IPC, committee 7-31b | **IPC-A-610K is at "Final Draft for Industry Review"**. Related documents: 610JA automotive addendum (joint with J-STD-001JA) is published; 610JC telecom addendum is a "Proposed Standard for Ballot". | [V] | revision table ; https://www.electronics.org/Status ; https://www.electronics.org/news-release/ipc-releases-j-revisions-two-leading-standards-electronics-assembly |
| J-STD-001 | Rev J | Apr 2024 | IPC, committee 5-22a (joint IPC/EIA standard) | **J-STD-001K is at "Final Draft for Industry Review"**. The J-STD-001KS space/military addendum is a working draft. No amendment to Rev J is listed. | [V] | same |
| UL 94 | **7th edition**, dated 28 Feb 2023 | Latest revision 2 Jul 2026 (ANSI approved the same day) | UL Standards & Engagement (ULSE), designated ANSI/UL 94 | The 2026 revision adds a flame stabilization time to the flame test method. Six ULSE collaborative-development (CSDS) proposals are listed, the latest dated 29 May 2026. The 6th edition is marked superseded. | [V] | https://www.shopulstandards.com/ProductDetail.aspx?productId=UL94 |
| IEC 60695-11-10 (50 W flame; matches UL 94 HB/V) | Edition 2.0 | Published 21 May 2013, with corrigendum of Sep 2014 incorporated | IEC TC 89 | Current. IEC does not plan to review it before 2028 (its "stability date"). | [V] | https://webstore.iec.ch/en/publication/2938 |
| IEC 60695-11-20 (500 W flame; matches UL 94 5VA/5VB) | Edition 2.0 | Published 22 Apr 2015, with corrigendum of Jan 2016 | IEC TC 89 | Current; stability date 2027. Only applies to materials already rated V-0 or V-1. | [V] | https://webstore.iec.ch/en/publication/22282 |
| WCAG 2.2 | W3C Recommendation, updated edition dated 12 Dec 2024 | First Recommendation 5 Oct 2023 | W3C (Accessibility Guidelines Working Group) | The Dec 2024 update changed four definitions (single pointer, used in an unusual or restricted way, motion animation, programmatically determined) plus editorial fixes. Errata exist. | [V] | https://www.w3.org/TR/WCAG22/ ; https://www.w3.org/WAI/standards-guidelines/wcag/faq/ |
| ISO/IEC 40500 | **ISO/IEC 40500:2025 (2nd ed.) = WCAG 2.2** | Published 24 Sep 2025; W3C announced approval 21 Oct 2025 | ISO/IEC JTC 1, adopted through JTC 1's fast-track procedure for outside specifications (PAS) | Replaces the 2012 edition (WCAG 2.0), now withdrawn. It matches the **Oct 2023** text of WCAG 2.2, not the Dec 2024 update. Moved to 90.92 ("to be revised") on 5 Feb 2026. **ISO/IEC DIS 40500 (3rd ed.)** closed voting 11 Jul 2026. W3C expects the Dec 2024 text to appear as ISO/IEC 40500:2026 by late 2026. The standard is free from ISO. | [V] (W3C); [R] (stage dates) | https://www.w3.org/press-releases/2025/wcag22-iso-pas ; https://www.w3.org/WAI/standards-guidelines/wcag/ ; https://iss.rs/en/project/show/iso:proj:91029 ; https://iss.rs/en/project/show/iso:proj:94018 |
| WCAG 3.0 | Working Draft dated 10 Sep 2026 | — | W3C AG WG | W3C says it will not be a finished standard "for a few more years". WCAG 2 will not be deprecated until several years after WCAG 3 is final. | [V] | https://www.w3.org/TR/wcag-3.0/ ; https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/ |
| ISO 9241-11 | ISO 9241-11:2018 (2nd ed.) | Published 4 Apr 2018 | ISO/TC 159/SC 4 | Confirmed (90.93) on 30 Oct 2023. No amendment found. | [R] | https://www.iso.org/standard/63500.html ; https://iss.rs/en/project/show/iso:proj:63500 |
| ISO 9241-110 | ISO 9241-110:2020 | Published 28 May 2020 | ISO/TC 159/SC 4 | Confirmed (90.93), stage date 30 Oct 2025. Replaced the 2006 "dialogue principles" edition. No amendment found. | [R] | https://www.iso.org/standard/75258.html ; https://iss.rs/en/project/show/iso:proj:75258 |
| ISO 9241-210 | ISO 9241-210:2019 | Published 4 Jul 2019 | ISO/TC 159/SC 4 | Confirmed in 2025 (stage date 22 May 2025). Replaced the 2010 edition. No amendment found. | [R] | https://www.iso.org/standard/77520.html ; https://iss.rs/en/project/show/iso:proj:77520 |

### 2. What each standard covers and what a tool could do

**Before building any tool:** the Global Electronics Association's front matter (2025) forbids feeding IPC standards data into AI engines or algorithms, and forbids text and data mining of it [V] (https://www.electronics.org/TOC/IPC-001JA-610JA-TOC.pdf). ASME, ISO, ULSE and IEC texts are copyrighted in the same way. So a tool should cite clause numbers and hold only user-supplied or licensed values, never embedded standard text. WCAG and ISO/IEC 40500 are the exception: both are free to use.

- **ASME Y14.5 / Y14.5.1**
  - **Governs:** Y14.5 is the US language for GD&T (geometric dimensioning and tolerancing): symbols, datums, feature-of-size rules, modifiers and default rules, on drawings and in 3D models. Y14.5.1 gives the mathematical definitions behind those tolerance zones.
  - **Triggers:** any US or ASME-referenced machined, molded or sheet-metal part, and any drawing handed to a CMM (coordinate measuring machine) or supplier inspection.
  - **A tool can:** check that feature-control frames are well-formed, that datum references resolve, that the title block names the edition, and that no basic dimensions are missing.
  - **Needs a qualified human:** choosing datums and tolerances that fit the part's function, and doing tolerance stack-ups.
- **ISO 8015 / ISO 1101 / ISO 14405-1**
  - **Governs:** the ISO GPS (geometrical product specification) system. ISO 8015 sets the base rules: independency is the default principle, and a drawing that cites a GPS standard invokes the whole system. ISO 1101 defines geometric tolerance symbols and zones. ISO 14405-1 defines how linear sizes and size modifiers are written; the 2025 edition changed that syntax.
  - **Triggers:** drawings for EU and other international supply chains, or any title block that calls up ISO GPS.
  - **A tool can:** flag a drawing that mixes ASME and ISO conventions, flag old 14405-1:2016 syntax (brackets on one dimension line, "/0", "rank-order" wording), and check that the title block cites ISO 8015.
  - **Needs a human:** deciding which size operator or modifier matches the part's function.
- **ISO 2768-1 / ISO 22081**
  - **Governs:** general ("title-block") tolerances for any dimension without its own tolerance. ISO 2768-1 has tolerance classes f/m/c/v for linear and angular sizes. ISO 22081 replaces the old 2768-2 geometric classes H/K/L with a GPS-compatible general specification.
  - **Triggers:** almost every machined or sheet-metal drawing, especially those carrying "ISO 2768-mK".
  - **A tool can:** flag "2768-mK" callouts, since the K class is now withdrawn, and prompt a move to ISO 22081. It can also warn that 2768-1 is about to be replaced.
  - **Needs a human:** choosing the tolerance class, because it drives cost.
- **IPC-2221C / IPC-2222B**
  - **Governs:** generic and rigid-board design rules: materials, conductor sizing and spacing, electrical clearance, plated holes, test coupons.
  - **Triggers:** any PCB design package or fabrication note.
  - **A tool can:** run DRC-style checks (design-rule checks: clearance by voltage, annular ring, aspect ratio) against user-entered limits, and fill fabrication-note templates.
  - **Needs a human:** high-voltage creepage decisions, the product class (1/2/3), and impedance and thermal trade-offs.
- **IPC-7351B / IPC-7352**
  - **Governs:** land-pattern (footprint) geometry, naming and courtyards.
  - **Triggers:** building or reviewing a component library.
  - **A tool can:** lint footprint names and courtyard spacing, and flag libraries still based on 7351B.
  - **Needs a human:** the process-specific pad adjustments.
- **IPC-A-610J / J-STD-001J**
  - **Governs:** J-STD-001 sets process and material requirements for soldered assemblies. IPC-A-610 sets visual accept/reject criteria by product class.
  - **Triggers:** contract manufacturing, and any purchase order that names a class.
  - **A tool can:** make sure the purchase order or drawing names the class and revision, and warn that Rev K is coming.
  - **Needs a human:** the inspection calls themselves, which require IPC-certified people (CIS/CIT).
- **UL 94 / IEC 60695-11-10 / -11-20**
  - **Governs:** small-scale burn tests that rate plastics.
  - **HB:** a horizontal specimen burns slowly or stops by itself.
  - **V-2, V-1, V-0:** vertical tests of rising strictness. V-0 must self-extinguish fastest. V-1 and V-0 forbid drips that ignite the cotton below; V-2 allows them.
  - **5VB and 5VA:** a much larger flame applied repeatedly. 5VB allows the flame to burn a hole through the test plaque; 5VA does not.
  - **IEC equivalents:** the 50 W method in IEC 60695-11-10 covers HB and V; the 500 W method in -11-20 covers 5V. (Class descriptions: [R] https://en.wikipedia.org/wiki/UL_94; IEC scope: [V].)
  - **Triggers:** enclosures, housings and internal plastic parts in electrical appliances and IT/AV equipment. End-product standards such as IEC/UL 62368-1 call for these ratings.
  - **A tool can:** check the bill of materials against UL iQ Yellow Card data (rating at the part's actual wall thickness and colour) and against the rating the end-product standard requires.
  - **Needs a human:** interpreting the end-product standard, and all testing and certification.
- **WCAG 2.2 / ISO/IEC 40500**
  - **Governs:** testable accessibility criteria for web and app content at levels A, AA and AAA.
  - **Triggers:** public-sector websites, the EU (EN 301 549 and the European Accessibility Act), ADA-related procurement, and any product that claims accessibility conformance.
  - **A tool can:** automatically test a meaningful minority of criteria, such as contrast, missing alternative text, form labels, the new 2.2 target-size minimum, and some focus-visibility checks.
  - **Needs a human:** keyboard and screen-reader walkthroughs, whether alt text actually makes sense, whether cognitive and "redundant entry" criteria are met, and signing the conformance claim.
  - **WCAG 3.0:** track it, but do not design to it yet.
- **ISO 9241-11 / -110 / -210**
  - **Governs:** ergonomics and usability. Part 11 defines usability (effectiveness, efficiency, satisfaction in a stated context of use). Part 110 gives interaction principles. Part 210 sets requirements for a human-centred design *process*.
  - **Triggers:** medical-device usability files (alongside IEC 62366-1), public procurement, and UX process audits.
  - **A tool can:** provide templates and traceability: context-of-use records, a user-requirements matrix, and evaluation plans.
  - **Needs a human:** the user research and evaluation itself, which is what the standard requires.

### 3. Discrepancies and items not found

1. **ASME Y14.5 and Y14.5.1:** the asme.org product pages say "stabilized maintenance", but ASME's own Y14 status sheet (20 Aug 2026) says revision in progress for both. The status sheet is newer and more specific. There is no draft or ballot date for a new Y14.5 edition, and I could not check for a public-review notice because the search budget ran out.
2. **Y14.5.1-2019** supplements Y14.5-2009, not Y14.5-2018 [V]. Mapping it onto 2018 drawings needs expert judgement.
3. **New ISO 2768:** it was at 60.00 on 2 Jun 2026. I could not confirm publication, the final year of the ISO edition, or its exact content changes. A secondary claim that the new edition drops the "rejection rule" and narrows scope to linear and angular sizes is [U]. iso.org was blocked throughout.
4. **ISO 2768-1:** iso.org's summary says it was "reviewed and confirmed in 2022", but iss.rs shows 90.92 ("to be revised") for that same review. Both agree it is still current.
5. **ISO/TC 213's "ongoing projects" page is out of date.** It still says WG12 is revising 14405-1, which was published in 2025.
6. **IPC-7352's cover** says it supersedes "IPC-7352 – June 2010". That looks like a typo for IPC-7351B (June 2010); IPC never explicitly says 7352 replaces 7351B. The release date also differs: May 2023 in the document header, July 2023 in the revision table.
7. **IPC-A-610K and J-STD-001K:** no comment deadline or target release date was shown. There is no IPC-2221D, 2222C or 7352A activity on the status page.
8. **IPC-A-610J vs J-STD-001J dates:** the revision table says Mar 2024 and Apr 2024. The joint press release is dated 8 Apr 2024.
9. **UL 94 6th edition dates** vary between sellers (ANSI webstore "Ed. 6-2013"; ULSE shop shows an edition date of 30 May 2018). This does not matter because the 6th edition is superseded.
10. **ISO/IEC 40500:2026** is expected but not confirmed published. The DIS vote closed 11 Jul 2026.
11. **ISO 9241 series:** stage dates come only from iss.rs. iso.org pages could not be opened.

### 4. Sources
- ASME Y14.5: https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing
- ASME Y14.5.1: https://www.asme.org/codes-standards/find-codes-standards/y14-5-1-mathematical-definition-dimensioning-tolerancing-principles
- ASME Y14 status sheet: https://cstools.asme.org/csconnect/Filedownload.cfm?thisfile=160.pdf&dir=CommitteeFiles&preview=true
- ISO pages (blocked with 403; seen only in search results): https://www.iso.org/standard/55979.html, /66777.html, /80703.html, /7748.html, /7749.html, /72514.html, /85741.html, /63500.html, /75258.html, /77520.html, /91029.html, /94018.html
- ISO/TC 213: https://committee.iso.org/sites/tc213/home/projects/ongoing/ongoing-1.html
- iss.rs (ISO stage mirror): https://iss.rs/en/project/show/iso:proj:55979, :66777, :80703, :7748, :7749, :72514, :85741, :91029, :94018, :63500, :75258, :77520
- ISO 14405-1:2025 foreword (iTeh preview): https://cdn.standards.iteh.ai/samples/iso/iso-14405-1-2025/12b879e743d748899b20ebe1383ff0bb/iso-14405-1-2025.pdf
- IPC revision table: https://www.electronics.org/ipc-document-revision-table
- IPC status page: https://www.electronics.org/Status
- IPC "J" revisions press release: https://www.electronics.org/news-release/ipc-releases-j-revisions-two-leading-standards-electronics-assembly
- IPC-7352 table of contents: https://www.electronics.org/TOC/IPC-7352-TOC.pdf
- IPC J-STD-001JA/610JA table of contents (AI and data-mining statement): https://www.electronics.org/TOC/IPC-001JA-610JA-TOC.pdf
- IPC Q2 2026 releases (I-Connect007): https://iconnect007.com/article/151199/ipc-standards-released-for-q2-2026/151196/smt
- UL 94 (ULSE shop): https://www.shopulstandards.com/ProductDetail.aspx?productId=UL94 and https://www.shopulstandards.com/ProductDetail.aspx?UniqueKey=34400
- UL 94 class descriptions: https://en.wikipedia.org/wiki/UL_94
- IEC 60695-11-10: https://webstore.iec.ch/en/publication/2938
- IEC 60695-11-20: https://webstore.iec.ch/en/publication/22282
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/ ; https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/ ; https://www.w3.org/WAI/standards-guidelines/wcag/faq/ ; https://www.w3.org/WAI/standards-guidelines/wcag/
- W3C ISO/IEC 40500 announcements: https://www.w3.org/press-releases/2025/wcag22-iso-pas ; https://www.w3.org/WAI/news/2025-10-21/wcag22-iso
- W3C WCAG 3.0: https://www.w3.org/TR/wcag-3.0/ ; https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/