# Solvere V1 Website — Project Memory

You are building the production marketing site for **Solvere**, an AI-native 
healthcare claim recovery service for UAE clinics. The full brief is in 
`./docs/BRIEF.md`. Read it before writing any code.

## Hard rules (read every session)

1. **Every word of copy in `./docs/COPY.md` is final.** Do not paraphrase. 
   Do not "improve." Do not summarize. Reproduce exactly.
2. **Every color, font, spacing value in `./docs/DESIGN.md` is locked.** 
   No off-token hex codes. No new fonts. No new spacing values.
3. **Every item in `./docs/FORBIDDEN.md` is banned.** If a request would 
   introduce any item from that file, push back and refuse.
4. The site must beat amperos.com on the rubric in `./docs/RUBRIC.md`. 
   Verify against it before declaring any section complete.

## Tech stack (non-negotiable)
- Next.js 14+ App Router, static export
- Tailwind CSS with tokens from DESIGN.md
- next/font/local with self-hosted .woff2 (Fraunces + Inter)
- Framer Motion (used per DESIGN.md motion rules only)
- @calcom/embed-react for the booking modal
- Deploy target: Vercel

## Workflow
- Build section by section, in the order listed in BRIEF.md §5.
- After each section: stop. Show me the result. Wait for approval.
- Never build two sections in one pass.
- If anything in the brief is ambiguous, ask before guessing.

## Aesthetic north star
Swiss private bank meets Stripe. Calm, confident, expensive, never 
childish, never healthcare-cliché. If a decision would make a Wall Street 
Journal advertorial designer wince, don't make it.
