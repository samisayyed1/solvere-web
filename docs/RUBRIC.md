# Solvere Quality Rubric — Grade Against This Before Declaring Done

Use this file during the polish phase. Paste it back at Claude and have the
build grade itself, item by item. No checkbox is ticked until verified.

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
