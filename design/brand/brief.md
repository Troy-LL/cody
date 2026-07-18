# Clicky pointer overlay brand brief (§6.8 stretch)

## Scope

This brief directs the optional, non-blocking §6.8 stretch overlay only: an arrow or ring that lands on the real Explorer file icon after `reveal()` has already succeeded. The demo-critical animation is Troy's §6.7 in-app breadcrumb inside `orchestration/`. That work is untouched here and is not restyled or replaced by anything in this brief.

## Metaphor

Pointing at a specific file. One arrow (or ring) makes a single confident arrival at a known location, then holds. Not a system cursor. Not a generic AI orb or sparkle. The asset should read as "there, that one" in under a second, the same certainty as a person tapping a screen.

## Palette rationale

Signal blue (`design/brand/palette.json`) reads as action and pointing: traffic signage, link-blue, "click here" affordance. It avoids the purple AI-glow default that would make the overlay look like an assistant hovering rather than a precise indicator finishing a job. Charcoal and paper are neutrals for outline/contrast against whatever Explorer theme is active; they are not accent colors.

- Primary `#2563EB`: the pointer's fill/stroke, the one color a viewer's eye should land on.
- Light `#93C5FD`: highlight edge or short motion trail, never the dominant color.
- Deep `#1E3A8A`: contact shading where the tip meets the icon, sells "arrived" over "floating."
- Charcoal `#0F172A` / Paper `#F8FAFC`: outline stroke for contrast, pick whichever contrasts the Explorer background.

## Must communicate at a glance

- Confidence: one shape, one color family, no hesitation frames.
- Precision: the tip is the focal point, not the tail or body.
- Arrival: the motion ends in a stop or settle, not a loop.

## Must avoid

- Generic clipart arrows or stock cursor art.
- AI sparkle, shimmer, or particle effects.
- Purple or violet glow of any kind.
- Rounded-pill or blob mascot shapes.
- Continuous mouse-follow behavior. The asset lands on a fixed icon location; it never tracks the live OS cursor.

## Handoff to clicky-pointer-svg: exact tip behavior

- The arrow tip (or the ring's inner edge) converges on the target icon's bounding-box corner or center. Pick one convergence point per asset and keep it consistent across all size variants.
- The asset renders and lands only after `reveal()` has returned success for that path. Never draw before that signal, never draw on a `reveal()` failure.
- No mouse-follow motion at any point in the animation. The path from entry to landing is a fixed, pre-authored trajectory to the icon's known screen coordinates, not a live cursor track.
- This overlay is never a stand-in for Troy's §6.7 breadcrumb. If the icon lookup fails or times out, the asset must no-op silently per the `overlay-stretch` spec; the in-app breadcrumb and baseline reveal are already the complete demo without it.
