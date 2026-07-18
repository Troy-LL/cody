# Cody product landing page — design

**Date:** 2026-07-18  
**Status:** Approved (user: approach A, blue + Times New Roman, GSAP/Lenis, CTA → GitHub)

## Goal

A single static marketing page that tells demo audiences what Cody is: an AI that **points** to files instead of explaining how to find them. Primary CTA opens the public repo.

## Audience

People watching or about to watch a live product demo (not sprint collaborators).

## Stack

- Static site under `landing/` (HTML, CSS, JS only)
- **GSAP** + **ScrollTrigger** for section/hero motion
- **Lenis** for smooth scrolling (respect `prefers-reduced-motion`)
- Libraries via CDN (no build step)
- Deploy on Vercel with project root = `landing/`
- Design intelligence: [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) for pattern/checklist during build; locked brand overrides skill font/color suggestions

## Brand (locked)

- **Colors:** blue-forward palette (primary ~`#1B4FD8`, deep navy text ~`#0A1628`, soft blue wash background ~`#E8F0FE` → white, CTA blue matching primary)
- **Type:** Times New Roman for all UI text (`"Times New Roman", Times, serif`)
- **No** purple gradients, no Inter/system-ui as primary, no card-heavy dashboard look

## Page structure

1. **Hero** — brand “Cody” dominant; one headline; one supporting sentence; CTA “View on GitHub” → `https://github.com/Troy-LL/cody`; full-bleed blue atmospheric background (gradient/pattern), not an inset media card
2. **How it works** — three steps: Ask (Taglish/NL) → Match (reasons over files) → Point (OS reveal + voice)
3. **Demo moment** — short section selling the “finger on the file” feeling
4. **Closing CTA** — repeat GitHub link
5. **Footer** — minimal (product name + repo link)

## Motion

- Lenis smooth scroll on load
- GSAP: hero brand/headline/CTA staggered entrance; ScrollTrigger fade/slide for sections; one subtle “pointing” accent (e.g. cursor/line converging) in demo section
- Honor `prefers-reduced-motion: reduce` (disable Lenis smoothing + skip non-essential GSAP)

## Out of scope

- Auth, waitlist forms, blog, Next.js, downloading the desktop app installer
- Embedding live app UI or videos (placeholder visual OK)

## Success

- Looks like a product pitch in one viewport (brand-first)
- Works on mobile and desktop
- Live URL on Vercel after deploy
