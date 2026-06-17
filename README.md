# Solvere — V1 marketing site

Production marketing site for [Solvere](https://solvere.ai) — AI-native
healthcare claim recovery for UAE clinics. Built per `./docs/BRIEF.md`.

## Stack

- **Next.js 16** App Router, static export (`output: 'export'`)
- **React 19**
- **TypeScript**
- **Tailwind CSS 3.4** with locked design tokens in [`tailwind.config.ts`](./tailwind.config.ts)
- **Framer Motion** — minimal entrance animations per `docs/DESIGN.md` §10
- **`@calcom/embed-react`** — booking modal
- **Self-hosted fonts** — Fraunces + Inter `.woff2` in `public/fonts/`

## Run locally

```bash
npm install
npm run dev
```

Open <http://localhost:3000>.

## Production build (static)

```bash
npm run build
```

Generates a static site in `./out/`. Drop the folder on any static host
(Vercel, S3 + CloudFront, Netlify, GitHub Pages).

## Deploy to Vercel

```bash
npx vercel --prod
```

Or connect the repo at <https://vercel.com/new> — Vercel auto-detects
Next.js. No env vars are required to build.

## Things you'll need to replace before launch

### 1. Cal.com event link

The "Book a call" buttons all point at the event `solvere/audit-call`.
Set this in two ways:

- **Build-time** — set `NEXT_PUBLIC_CALCOM_LINK="acme/your-event"` in
  Vercel env vars (and `.env.local` for development).
- **Code** — edit the `CAL_LINK` constant in
  [`components/BookACallButton.tsx`](./components/BookACallButton.tsx).

### 2. Team section names + photos (§7.8)

Two `[VARIABLE — ...]` placeholders in
[`components/sections/Team.tsx`](./components/sections/Team.tsx):

- `[VARIABLE — Founder name]`
- `[VARIABLE — Coder name]` + DHA credential string

Drop real headshots in `public/team/` (4:5 ratio, soft cream backdrop —
see brief §7.8) and swap the placeholder `<div role="img">` blocks for
`<Image>` components.

### 3. Real OG + favicons

Placeholder cream PNGs ship in `public/`. Replace:

- `og.png` — 1200×630, cream bg, "Solvere" wordmark in Fraunces, tagline
  "What is owed is owed.", teal accent rule (brief §12)
- `favicon-16.png`, `favicon-32.png`, `apple-touch-icon.png` — simple "S"
  in Fraunces on cream

## Source-of-truth docs (read these before changing anything)

| File | What it locks |
|---|---|
| [`./CLAUDE.md`](./CLAUDE.md) | Workflow + hard rules. |
| [`./docs/BRIEF.md`](./docs/BRIEF.md) | Full 17-section build brief, verbatim. |
| [`./docs/COPY.md`](./docs/COPY.md) | Every word of section copy. **Final. Do not paraphrase.** |
| [`./docs/DESIGN.md`](./docs/DESIGN.md) | Colors, fonts, type scale, spacing, motion. |
| [`./docs/FORBIDDEN.md`](./docs/FORBIDDEN.md) | Hard bans — words, patterns, ornaments. |
| [`./docs/RUBRIC.md`](./docs/RUBRIC.md) | Quality bar to grade against before declaring done. |

## Repo layout

```
solvere-web/
├── app/
│   ├── globals.css         # Tailwind base + a11y + prefers-reduced-motion
│   ├── layout.tsx          # Fonts (next/font/local), SEO/OG meta, skip link
│   └── page.tsx            # Section assembly in §5 order
├── components/
│   ├── BookACallButton.tsx # Cal.com-wired CTA — primary + nav variants
│   ├── FadeIn.tsx          # Framer Motion §10-compliant entrance wrapper
│   └── sections/           # One file per §7 section
├── docs/                   # Locked source-of-truth (see table above)
├── public/
│   ├── fonts/              # Fraunces 400/500/700, Inter 400/500/600
│   └── og.png + favicons   # Placeholders — replace before launch
├── tailwind.config.ts      # Design tokens — every value is from DESIGN.md
└── next.config.ts          # output: 'export', images: { unoptimized: true }
```
