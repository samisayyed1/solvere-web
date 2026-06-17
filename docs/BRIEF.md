# SOLVERE — V1 Website Build Brief

**Audience:** AI website builder (Claude window trained on premium frontend execution).
**Output:** A production-ready, single-page marketing site.
**Quality bar:** must measurably outperform `amperos.com` on every dimension named in §13.
**Final deliverable:** a complete Next.js project (or equivalent) that can be deployed to Vercel within 30 minutes.

---

## 0. Mission

Build the V1 marketing site for **Solvere** — an AI-native healthcare claim recovery service for UAE clinics. The site has exactly one job: convert a UAE clinic owner or finance manager into a booked 20-minute audit call via a Cal.com embed.

The site is a single scroll, mobile-first, formal, premium, and aesthetically restrained. The aesthetic is **Swiss private bank meets Stripe** — calm, confident, expensive, never childish, never healthcare-cliché. The medical sector trusts brands that look like they belong on a Wall Street Journal advertorial, not a wellness startup.

**Conversion goal:** clicks on "Book a 20-minute audit call" → opens Cal.com modal.
**Anti-goal:** any feature, any pixel, any line of copy that does not measurably move that conversion forward must be cut.

---

## 1. The Company in 60 Seconds

You are building a brand for a company doing the following:

- UAE insurance companies pay roughly AED 22 billion in healthcare claims every year (CBUAE, 2024).
- Approximately 12–15% of all claims are initially denied.
- Roughly 60–70% of those denials are technically recoverable on appeal.
- UAE clinics only recover ~35% of denied claims — the rest is written off because clinic billers don't have time.
- **Solvere** runs the denied claims through AI agents plus a UAE-licensed medical coder, fixes them, resubmits through eClaimLink and payer portals (Daman, Thiqa, NEXtCARE, NAS, MedNet), and gets the clinic paid.
- The clinic pays **20% of recovered cash**, nothing else. If no recovery, no fee.
- The US analog, **Amperos Health**, raised $16M Series A in April 2026, serves 3,000+ clinics. We are the GCC equivalent — built before they enter the region.

**The buyer:** small-to-mid UAE clinic owner, finance manager, or RCM manager. Typically 30–55 years old, UAE-resident. Reads email on phone. Skeptical of vendors. Already overpaying for a biller who can't keep up.

**The Big Idea:** *the restoration of what is owed.* This single emotional truth governs every visual and verbal decision.

---

## 2. The Conversion Goal — One Button, One Call

The entire site funnels to one action: book a 20-minute discovery call via **Cal.com**.

- **No upload portal** on V1. Claim files contain PHI; accepting them on a marketing page is a regulatory landmine. Data exchange happens only after the call, after a signed NDA, through a secure channel.
- **No contact form** on V1. Cal.com handles all lead capture (name, email, clinic, phone).
- **No "request a demo"** language. Use **"Book a 20-minute audit call"**, every time, no variation.

The CTA appears in exactly **two places**: in the hero, and in the final section. Never three. Repeating it more cheapens it.

---

## 3. Tech Stack — Required

| Layer | Choice | Notes |
|---|---|---|
| Framework | **Next.js 14+ (App Router)** | Static export. No SSR needed for V1. |
| Styling | **Tailwind CSS** | With custom design tokens defined in §6. |
| Type loading | **`next/font/local`** with self-hosted .woff2 files | No Google Fonts CDN — affects LCP. |
| Motion | **Framer Motion** | Used minimally, per §10. |
| Booking | **Cal.com embed** (`@calcom/embed-react`) | Inline modal popup, not redirect. |
| Hosting | **Vercel** | Free tier. Edge deployed. |
| Domain | `solvere.ai` initially, `solvere.com` if acquired | Configure both. |
| Analytics | **Plausible** or **Vercel Analytics** | Privacy-friendly. No Google Analytics. |

The site **must not** use: jQuery, Bootstrap, any UI kit, AI-generated illustrations, stock photo subscriptions, or any third-party widget besides Cal.com.

---

## 4. Brand Identity Lock

| Element | Value |
|---|---|
| Brand name | **Solvere** |
| Pronunciation | *sol-VAY-ray* — never spell phonetically in copy |
| Lockup | Wordmark only. No symbol on V1. Letters set in the serif headline font. |
| Primary tagline | *What is owed is owed.* |
| Secondary tagline | *The AI claim recovery service for UAE clinics.* |
| Legal entity | 1WEB FZE, Abu Dhabi, United Arab Emirates |

---

## 5. Page Structure — Single Scroll

The site is **one page**, in this exact order:

1. **Nav** (sticky, transparent fading to ink on scroll)
2. **Hero** — headline, subhead, primary CTA, trust line
3. **The Number** — AED 22 billion stat, single screen
4. **The Gap** — three stats side by side
5. **How It Works** — four steps
6. **Risk Reversal** — three lines
7. **Why Solvere** — short differentiation block
8. **The Team** — founder + UAE-licensed coder
9. **Final CTA** — repeat of hero CTA with reinforced promise
10. **Footer**

No other pages. No `/about`, no `/pricing`, no `/blog`, no `/login`, no `/careers`.

---

## 6. Design System — Locked

### 6.1 Color tokens

```css
--ink:        #0A0A0A;   /* text, dark sections — never pure black */
--ink-soft:   #1A1A1A;   /* body text on light bg */
--muted:      #595959;   /* secondary text, captions */
--rule:       #E5E0D6;   /* divider lines */
--cream:      #F8F6F1;   /* primary background — parchment, never pure white */
--cream-deep: #EFEBE1;   /* alternate band background */
--teal:       #0E5E5E;   /* primary accent — links, button bg, key stats */
--teal-deep:  #0A4848;   /* accent hover state */
--amber:      #B45309;   /* secondary accent — used ONLY for one element, sparingly */
```

**Do not** introduce new colors. The entire palette is nine values. Hex codes are absolute.

### 6.2 Typography

Two fonts only. Self-hosted as .woff2.

| Role | Font | Weights | Notes |
|---|---|---|---|
| Headlines | **Fraunces** (or Tiempos Headline if licensed) | 400, 500, 700 | Slight serif modulation, financial-document gravitas. |
| Body & UI | **Inter** | 400, 500, 600 | Tabular figures enabled via `font-feature-settings: 'tnum'`. |

**Fraunces** is free via Google Fonts but **must be self-hosted** for the V1. Download .woff2 from fonts.google.com and serve via `next/font/local`.

### 6.3 Type scale (responsive)

| Token | Mobile | Desktop | Line height | Weight | Tracking |
|---|---|---|---|---|---|
| Display (hero) | 48px | 88px | 1.02 | 500 | -0.02em |
| H1 | 36px | 56px | 1.08 | 500 | -0.015em |
| H2 | 28px | 40px | 1.15 | 500 | -0.01em |
| H3 | 22px | 26px | 1.3 | 600 | -0.005em |
| Stat (giant) | 72px | 144px | 1 | 500 | -0.03em |
| Body large | 18px | 21px | 1.5 | 400 | 0 |
| Body | 16px | 17px | 1.55 | 400 | 0 |
| Caption | 13px | 14px | 1.4 | 500 | 0.08em (UPPERCASE) |

Headlines and stats use Fraunces. Everything else uses Inter.

### 6.4 Spacing (8pt grid)

```css
--space-1:  8px;
--space-2:  16px;
--space-3:  24px;
--space-4:  32px;
--space-5:  48px;
--space-6:  64px;
--space-7:  96px;
--space-8:  128px;
--space-9:  192px;
```

Section vertical padding: **`var(--space-7)` mobile, `var(--space-9)` desktop.**
Maximum content width: **1140px**, centered, with 24px gutters mobile / 48px desktop.
Body text columns cap at **640px** (about 65 characters) — never let prose run wider.

### 6.5 Visual references — study these

Before building, the AI must mentally model these sites. Solvere should sit comfortably in this lineage:

- **stripe.com** — restraint, density, premium tabular numbers
- **linear.app** — geometric precision, dark sections
- **mercury.com** — banking-grade trust signals
- **anthropic.com** — cream backgrounds, serif headlines
- **ramp.com** — confident financial typography
- **arc.net** (the website, not the browser) — bold serif headlines, asymmetric layout
- **rwwa.com** (Bonadio) — formal, financial-document feel

Solvere is **not** to resemble: any healthcare startup site, any "AI for business" template, anything with gradient meshes, anything with floating 3D shapes, anything with chat bubbles in the hero.

---

## 7. Section-by-Section Copy and Layout

Every word below is final unless explicitly marked `[VARIABLE]`. Do not paraphrase. Do not "improve." The copy has been weighed and signed off.

### 7.1 Nav

**Layout:** sticky, transparent on cream background at top, fades to cream + bottom border after 80px scroll.

**Left:** Solvere wordmark (Fraunces 500, 22px, ink color).
**Right:** single button — `Book a call` (16px Inter 500, teal background, cream text, 10px vertical / 20px horizontal padding, 6px border-radius). On hover: teal-deep background, 200ms ease-out.

No nav links. No menu hamburger. No login. Just logo + button.

### 7.2 Hero

**Background:** cream.
**Layout:** centered, max-width 960px, 12vh top padding (mobile) / 18vh (desktop).

**Eyebrow** (caption style, teal, uppercase, letter-spaced):
> ABU DHABI · UNITED ARAB EMIRATES

**Headline** (Display size, Fraunces 500, ink):
> Recover the denied insurance claims your billers gave up on.

**Subhead** (Body large, muted, max-width 580px):
> Solvere is the AI-native claim recovery service for UAE healthcare providers. We work your denied claims end-to-end and recover the money. You pay only when we win.

**Primary CTA button** (Inter 500, 17px, cream text, teal bg, 14px / 28px padding, 8px radius):
> Book a 20-minute audit call

**Trust line** (caption, muted, below button with 16px gap):
> No software · No integration · Pay only on recovery

### 7.3 The Number

**Background:** ink.
**Layout:** full-width band, vertical padding `var(--space-9)`.

**Eyebrow** (caption, cream/40% opacity, uppercase):
> THE OPPORTUNITY

**The stat** (Stat-giant size, Fraunces 500, cream color):
> AED 22 Billion

**Caption directly under stat** (body large, cream/70% opacity, max-width 560px):
> paid annually in UAE healthcare claims. A meaningful share is denied — and never recovered. That share is your money.

**Source line** (caption, cream/40% opacity, uppercase, letter-spaced):
> SOURCE — CBUAE QUARTERLY ECONOMIC REVIEW, REPORTED BY GULF NEWS (2024)

### 7.4 The Gap

**Background:** cream.
**Layout:** three columns desktop, stacked mobile, with hairline dividers between.

**Section eyebrow** (caption, teal, uppercase):
> THE GAP

**Section headline** (H2, Fraunces, ink, max-width 720px, centered):
> Most denied claims are recoverable. Most are never recovered.

**Three stats:**

| Stat (Fraunces 500, 88px, teal) | Label (caption, ink, uppercase) | Caption (body, muted) |
|---|---|---|
| 35% | RECOVERED TODAY | The current UAE clinic average for denied claims |
| 60–70% | ACTUALLY RECOVERABLE | Industry benchmark on appeal-eligible denials |
| AED 1.2M+ | LEFT ON THE TABLE | Estimated annual loss per AED 20M of revenue |

**Footer line under the three stats** (body, muted, centered, max-width 640px):
> Solvere closes the gap with AI agents and UAE-licensed medical coders, on a pure pay-on-recovery basis.

### 7.5 How It Works

**Background:** cream.
**Layout:** four-step vertical sequence on mobile, two-by-two grid on desktop. Each step has a step number, a title, a one-sentence description. No icons. No illustrations. The numbers are the visual.

**Section eyebrow:**
> HOW IT WORKS

**Section headline** (H2):
> Four steps. Five days to first audit. Zero risk.

**Step 01 — Send us your denied claims**
> Export the last 90 days of denials from your billing system. One file. Ten minutes of your time.

**Step 02 — We analyze every claim**
> Our AI agents and a DHA-licensed medical coder review each denial, classify the reason, and identify what's recoverable. You receive an audit within five working days.

**Step 03 — We resubmit and appeal**
> We handle resubmissions and appeals through eClaimLink and payer portals — Daman, Thiqa, NEXtCARE, NAS, MedNet, and others. Documentation, follow-up, escalation — all done by us.

**Step 04 — You pay only when we recover**
> Twenty percent of recovered cash. Nothing else. No software fee. No setup fee. If we don't recover, you pay zero.

**Step number styling:** Fraunces 500, 56px, teal, displayed as `01`, `02`, `03`, `04` with no slash or punctuation.

### 7.6 Risk Reversal

**Background:** cream-deep band.
**Layout:** three lines stacked, centered, generously spaced.

**Eyebrow** (caption, teal):
> WHY CLINICS SAY YES

Three lines in H2-sized Fraunces, ink, each on its own line with 32px vertical spacing:

> No software to install.
> No integration with your PMS.
> Pay only when you are paid.

Below the three lines, in body muted, centered, max-width 580px:
> Solvere carries the operational and financial risk. Your downside is zero.

### 7.7 Why Solvere

**Background:** ink.
**Layout:** two-column grid on desktop (left: headline; right: body), single column mobile.

**Eyebrow** (caption, cream/60%):
> WHY SOLVERE

**Left column headline** (H1, Fraunces 500, cream):
> Built in the UAE, for the UAE.

**Right column body** (body large, cream/80%):

> Solvere is not a US tool retrofitted for the Gulf. We are built in Abu Dhabi by people who understand the difference between a Daman denial and a Thiqa rejection, between DHA and DoH coding rules, between a clinic in Karama and a hospital in Khalifa City.

> Our agents read every payer's portal. Our coders are licensed by the same authorities your clinic is. Every recovered dirham trains the system to recover the next one faster.

> When global players enter the region, they will start at zero. We will already be the default.

### 7.8 The Team

**Background:** cream.
**Layout:** centered, two cards side by side (desktop) or stacked (mobile). Each card is a photo, a name, a role line, a credentials line. No social icons, no bio paragraphs.

**Section eyebrow:**
> THE PEOPLE BEHIND THE WORK

**Section headline** (H2):
> Real people. Licensed credentials. Abu Dhabi.

**Card 1 — Founder** *(replace [VARIABLE] with actual content during build)*
- Photo (4:5 ratio, soft cream backdrop, professional, no smile-for-camera energy)
- Name: `[VARIABLE — Founder name]`
- Role: `Founder · 1WEB FZE`
- Credential line: `Based in Abu Dhabi`

**Card 2 — Medical Coder**
- Photo (same treatment)
- Name: `[VARIABLE — Coder name]`
- Role: `Lead Medical Coder · Solvere`
- Credential line: `DHA-licensed · [VARIABLE — CPC or CCS or CPMA] · [VARIABLE — N] years denial management`

Below the two cards, single line caption (body, muted, centered):
> Solvere is operated by 1WEB FZE — a UAE-registered company headquartered in Abu Dhabi.

### 7.9 Final CTA

**Background:** ink, full-bleed band.
**Layout:** centered, vertical padding `var(--space-9)`.

**Headline** (H1, Fraunces, cream, max-width 720px):
> Ready to recover what your clinic is owed?

**Subhead** (body large, cream/70%, max-width 540px):
> Send us your last ninety days of denials. We will return a recoverability audit in five working days. No software. No upfront fee. No risk.

**Button** — same teal CTA as the hero:
> Book a 20-minute audit call

**Trust line below button** (caption, cream/50%):
> 5-DAY AUDIT · PAY ONLY ON RECOVERY · ZERO RISK

### 7.10 Footer

**Background:** cream-deep.
**Layout:** three columns on desktop (logo+address left, links center if any, contact right), stacked mobile. Hairline rule above.

**Left column:**
- Solvere wordmark (small, 18px)
- Address block (caption, muted):
  > 1WEB FZE
  > Abu Dhabi, United Arab Emirates

**Center column:**
- One line only: `hello@solvere.ai`

**Right column** — compliance language (caption, muted, right-aligned desktop / centered mobile):
> DIFC Data Protection Law compliant.
> No protected health information is collected via this website.
> Sensitive data exchange occurs only after a signed NDA via secure encrypted channels.

**Bottom row, full width, hairline rule above** (caption, muted, centered):
> © 2026 1WEB FZE. All rights reserved.

---

## 8. Microcopy Library

Every button, hover state, error state, alt text:

| Context | Copy |
|---|---|
| Primary CTA button | Book a 20-minute audit call |
| Nav CTA button | Book a call |
| Cal.com modal title (if customizable) | Solvere · 20-minute audit call |
| Image alt text — founder | Founder of Solvere, Abu Dhabi |
| Image alt text — coder | Lead Medical Coder at Solvere, DHA-licensed |
| Logo alt text | Solvere |
| Skip-to-content link | Skip to main content |
| Page title (`<title>`) | Solvere — Healthcare Claim Recovery for the UAE |
| Meta description | Solvere recovers denied healthcare insurance claims for UAE clinics. AI-native, pay-only-on-recovery. Abu Dhabi-based. |

---

## 9. Responsive Behavior

Three breakpoints, mobile-first:

```css
/* base: 0–639px (mobile) */
/* @media (min-width: 640px)  — tablet portrait  */
/* @media (min-width: 1024px) — desktop          */
/* @media (min-width: 1440px) — large desktop    */
```

**Mobile-specific rules:**
- Hero display type drops to 48px max
- All multi-column sections collapse to single column
- Sticky nav becomes 56px tall with smaller logo
- CTA button becomes full-width below 640px
- Section padding drops to `var(--space-7)` vertical
- Stat-giant type drops to 72px

**Desktop-specific:**
- Hero is centered, 88px display type
- "How It Works" becomes a 2×2 grid
- "Why Solvere" becomes 50/50 two-column
- Team becomes side-by-side cards

Test at: **375px, 768px, 1280px, 1920px**. The site must look intentional at all four.

---

## 10. Motion Design

Restraint is the whole point. The brand whispers; it does not perform.

**Allowed:**
- Fade-in on scroll with 12px Y-translate, 600ms duration, `cubic-bezier(0.22, 1, 0.36, 1)` easing. Stagger child elements by 80ms.
- Hero text animates in on mount with the same easing, 80ms stagger between eyebrow → headline → subhead → button → trust line.
- Buttons: 200ms ease-out background-color transition on hover. No scale. No shadow. No translate.
- Sticky nav: 200ms opacity + background transition when crossing the 80px scroll threshold.

**Forbidden:**
- Parallax of any kind
- Marquee scrolling stat bars
- Bouncy spring animations
- Mouse-follow effects
- Cursor replacements
- Autoplay video
- Lottie animations
- Page-load splash screens
- Scroll-jacking

Use `prefers-reduced-motion` media query to disable all motion for users who request it.

---

## 11. Accessibility

WCAG 2.1 AA minimum. Required:

- All text meets 4.5:1 contrast ratio (verify: cream `#F8F6F1` on ink `#0A0A0A` ✓; cream/70% on ink — check and adjust if needed).
- All interactive elements have visible focus states (2px teal outline, 2px offset).
- Skip-to-main-content link as first focusable element.
- Semantic HTML: `<header>`, `<main>`, `<section>`, `<footer>`, proper heading hierarchy (one H1, then H2s, then H3s — never skip).
- Alt text on every image (per §8).
- `aria-label` on the nav CTA button.
- Form fields (Cal.com handles this, but verify the embed is accessible).
- Keyboard navigable: every interactive element reachable via Tab.
- Font sizes never below 13px.
- Line height never below 1.4 for body text.

---

## 12. SEO + Open Graph

**`<head>` requirements:**

```html
<title>Solvere — Healthcare Claim Recovery for the UAE</title>
<meta name="description" content="Solvere recovers denied healthcare insurance claims for UAE clinics. AI-native, pay-only-on-recovery. Abu Dhabi-based.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://solvere.ai">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:title" content="Solvere — Healthcare Claim Recovery for the UAE">
<meta property="og:description" content="Recover the denied insurance claims your billers gave up on. AI-native. Pay only on recovery.">
<meta property="og:image" content="https://solvere.ai/og.png">
<meta property="og:url" content="https://solvere.ai">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Solvere — Healthcare Claim Recovery for the UAE">
<meta name="twitter:description" content="Recover the denied insurance claims your billers gave up on. AI-native. Pay only on recovery.">
<meta name="twitter:image" content="https://solvere.ai/og.png">
```

**OG image (`/public/og.png`):** 1200×630, cream background, "Solvere" wordmark in Fraunces large, tagline "What is owed is owed." below, teal accent rule. Build this as part of the deliverable.

**Favicon:** simple "S" in Fraunces on cream square, exported as 32×32, 16×16, and `apple-touch-icon.png` 180×180.

---

## 13. The 10× Benchmark — Solvere vs Amperos

Solvere V1 must outperform `amperos.com` on every measurable axis. The receiving AI must verify each item before declaring the build complete.

| Dimension | Amperos today | Solvere V1 requirement |
|---|---|---|
| Headline typography | Sans-serif (generic startup) | **Serif (Fraunces) — financial-document gravitas** |
| Hero promise clarity | Multi-sentence, requires reading | **One sentence under 15 words** |
| Big-number proof above the fold | None | **AED 22 billion stat in section 2** |
| Risk-reversal language | Implied | **Three explicit lines in section 6** |
| Visible human credentials | None on homepage | **DHA-licensed coder photo + credentials** |
| Lighthouse Performance score | ~85 | **100** |
| Lighthouse Accessibility score | ~95 | **100** |
| Lighthouse Best Practices | ~92 | **100** |
| Lighthouse SEO | ~100 | **100** |
| Largest Contentful Paint (LCP) | ~2.0s | **< 1.2s** |
| Cumulative Layout Shift (CLS) | ~0.05 | **< 0.01** |
| Total page weight | ~1.8MB | **< 400KB** |
| Number of CTAs on page | 4+ | **Exactly 2** |
| Number of distinct fonts | 2+ Google-CDN | **2 self-hosted .woff2 files** |
| Color palette size | 8+ values | **9 locked tokens, no others** |

Run Lighthouse on the final build. Attach the report. If any score is below 100 except Performance (which must be ≥98), iterate until it passes.

---

## 14. Forbidden List — Hard Bans

The site must contain **none** of the following:

- Stock photos of doctors, nurses, or stethoscopes
- Medical iconography (caduceus, heartbeat lines, red crosses, pill icons)
- Generic blue gradients
- AI-generated illustrations
- "Trusted by" customer logo bars (you have no customers yet)
- Faked testimonials or fake metrics
- Pricing tables
- Login button
- Live chat widget (Intercom, Drift, Crisp — none of them)
- Cookie banner with marketing nonsense (only essential consent, if any)
- Newsletter signup
- Blog or "Resources" link
- Footer link to social media (you don't have it yet — don't fake it)
- Emoji anywhere
- Exclamation marks anywhere
- Words: "revolutionary", "cutting-edge", "leverage", "synergy", "world-class", "best-in-class", "next-generation", "powered by AI"
- Border radius greater than 12px
- Drop shadows more than `0 2px 4px rgba(0,0,0,0.06)`
- Gradients with more than two stops
- Animated counters
- Particle effects
- Scroll-triggered video
- Splash / intro screen

---

## 15. Quality Bar — Final Rubric

Before declaring the build complete, the AI must verify all of the following:

**Build correctness**
- [ ] Next.js project builds without errors or warnings
- [ ] All Lighthouse scores hit the targets in §13
- [ ] Works flawlessly on Safari (mobile + desktop), Chrome, Firefox, Edge
- [ ] No console errors on any page
- [ ] All images optimized (WebP or AVIF, with PNG fallback for OG)

**Design fidelity**
- [ ] Every color in use is one of the nine tokens in §6.1 — no off-token values
- [ ] Every font is one of the two in §6.2 — no fallbacks visible
- [ ] Every spacing value is on the 8pt grid in §6.4
- [ ] Type scale matches §6.3 across breakpoints
- [ ] Sections separated by `var(--space-9)` (desktop) / `var(--space-7)` (mobile)

**Copy fidelity**
- [ ] Every word in §7 is reproduced exactly — no paraphrasing
- [ ] No words from the §14 forbidden list appear anywhere
- [ ] Cal.com CTA copy is identical in both placements

**Conversion correctness**
- [ ] Both CTA buttons open the Cal.com modal (not redirect)
- [ ] Cal.com is configured with the correct event link
- [ ] No other interactive element competes with the CTA

**Polish**
- [ ] Focus states visible on all interactive elements
- [ ] `prefers-reduced-motion` respected
- [ ] Skip-to-content link present
- [ ] Page transitions feel calm, never bouncy
- [ ] Site feels expensive — like it belongs on a Wall Street Journal advertorial, not a wellness startup

If any item in this rubric fails, the build is not complete. Iterate until every box is checked.

---

## 16. Deliverables

The receiving AI returns the following:

1. A complete Next.js project (zip or git repo) ready to `npm install && npm run dev`
2. The `og.png` image (1200×630) saved at `/public/og.png`
3. All favicon files at `/public/`
4. A short `README.md` explaining: how to run, how to deploy to Vercel, how to update the Cal.com link, and how to swap the placeholder names/photos in §7.8 when ready
5. A Lighthouse report screenshot or PDF showing all four scores

---

## 17. One-Line Reminder

Every decision in this build is governed by one rule:

> *Would a clinic owner in Karama, reading this on their phone between patients, take it seriously?*

If yes, keep it. If no, cut it. That is the whole brief.

---

**End of brief. Begin build.**
