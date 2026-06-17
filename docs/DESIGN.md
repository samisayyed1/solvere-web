# Solvere Design System — Locked

Source of truth for tokens, type scale, spacing, responsive behavior, and motion.
Consult this file constantly during build. No off-token values. No new fonts.
No new spacing. No new motion patterns beyond what is allowed below.

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
