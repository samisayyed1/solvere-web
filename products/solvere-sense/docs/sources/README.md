# Sources (G0)

Local copies of every vendor source cited in `requirements/`, `params/` and `docs/`. All fetched on **2026-09-25**. Vendor titles containing "fall detection" are quoted as published; product wording follows `compliance/claims-wording.md`. by systems-engineer through the session proxy. The `.txt` files are text extracted with a stdlib-only PDF/HTML parser (no pypdf or pdftotext was available); on the DS the extractor joined letters that the PDF places one glyph at a time. If a `.txt` and its original disagree, the original wins.

| Short name | File | sha256 | Origin | Notes |
|---|---|---|---|---|
| DS | `MR60FDA2-datasheet-114993388.pdf` | `da2cc48cd5dfa11be470162ea51f3a804614bd9be73d3cbff38bf3193034fd52` | https://files.seeedstudio.com/Bazaar/product_pdf/114993388.pdf (HTTP last-modified 2026-07-30 11:27:19 GMT, 1,473,301 bytes) | Kit industrial product datasheet, 8 pages, "Updated 2026-07-30 08:17:32". Text: `MR60FDA2-datasheet-114993388.txt` |
| MDS | `MR60FDA2-module-datasheet.pdf` | `0a89cbd8edae08224612a935a3d5f7cbb830d2072fed6b33486c39ce7c363d5e` | https://files.seeedstudio.com/wiki/mmwave-for-xiao/mr60/datasheet/MR60FDA2_Fall_Detection_Module_Datasheet.pdf (last-modified 2024-12-27) | Radar module technical specification, Beta V1.0, 2024-03-05, 12 pages; linked from the Wiki "Resources". Text: `MR60FDA2-module-datasheet.txt` |
| Wiki | `wiki-mr60fda2.html` | `9c49f2ab96e9ab4ad457e561139ae8748bcf7c29cb696367d2c2bbb7eed7bac0` | https://wiki.seeedstudio.com/getting_started_with_mr60fda2_mmwave_kit/ (HTTP last-modified 2026-09-24) | Page footer: "Last updated on Aug 19, 2024 by Spencer". Text: `wiki-mr60fda2.txt` |
| XIAO | `wiki-xiao-esp32c6.txt` | `84d818e37a650ec15fb67c7d87c61405f7c277f6872eb374a87201f6e1544399` | https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/ | Text only. Footer: "Last updated on Aug 5, 2024" |
| FDA1 | `wiki-mr60fda1.txt` | `fffdfa57baa7646510a9ae04203ab87074de47d4543533d86f41521c5ce08565` | https://wiki.seeedstudio.com/Radar_MR60FDA1/ | Sibling module, used only for assumptions. Footer: "Last updated on Mar 3, 2023" |
| Web | `seeed-product-page-p5946-excerpt.txt` | `67949ee58268691ee55d26ed709517dc4c53c5da65c62de5aa802c1069d44827` | https://www.seeedstudio.com/MR60FDA2-60GHz-mmWave-Sensor-Fall-Detection-Module-p-5946.html | Price excerpt only; full page sha256 is in the file. Price can depend on region |
| ARSDG | `apple-rubber-seal-design-guide.pdf` | `9060437203f9a9b032c65f8ce540e0b9367cd837984d77073d63ebf926cf0e7a` | https://www.applerubber.com/src/pdf/seal-design-guide.pdf | Apple Rubber Seal Design Guide, 122 pages, used for O-ring gland sizing (Section 4 Table A, p.20; p.90; p.113). Excerpt: `apple-rubber-seal-design-guide-excerpt.txt` (Table A is a graphic table; its column order is noted in the excerpt). Parker's O-Ring Handbook ORD 5700 was tried first and returned HTTP 403 |

The `.txt` hashes change if the text is re-extracted; the PDF and HTML hashes identify the source.

## Discrepancies found between sources

- **Field of view**: DS p.3 and p.6 give 120° horizontal by 100° vertical. The Wiki "Features" list gives a "100° x 40° detection angle". MDS p.4 gives a -3 dB beam of -60° to 60° in both planes (RISKS R-013).
- **Kit price**: DS p.1 gives $26.90 (updated 2026-07-30); the product page on 2026-09-25 gives $28.99 at 1 unit and at 10+ (RISKS R-002).
- **Bluetooth version**: XIAO introduction says Bluetooth 5.3; the XIAO specification table says Bluetooth Low Energy 5.0.
- **Intended use**: MDS p.3 and p.11 describe the radar module as suited to bathrooms and single-person scenes; the v1 pod is for bedrooms and living rooms (RISKS R-004).
- **Typos in the sources**: the MDS introduction and §6.1 call the module "MR60FDC1"; the Wiki "Software Preparation" note calls the kit "MR60BHA2"; DS p.6 lists the button as "Rest" (reset).
- **Not published anywhere**: kit carrier-board outline and hole pattern, kit weight, kit operating temperature, and how the XIAO USB-C behaves with a C-to-C source. The Wiki source file has a commented-out board-size image (`6-mmWave-size.jpg`) that is not shown on the page.
