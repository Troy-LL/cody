# Cody cursor assets

SVG pointers for the fullscreen overlay demo (follow mouse → point at source).

| File | Use | Notes |
|------|-----|--------|
| `cursor-default.svg` | Companion / idle | Drawn small (~28px) in demo |
| `cursor-point.svg` | Point / arrive | Same asset family |

**Demo behavior:** OS cursor stays. Cody is a separate sprite parked **lower-right** of the mouse (`+18px, +22px`), spring-smoothed (not glued). On point, it leaves that slot and flies to the source.

**Brand:** fill `#1B4FD8`, outline `#0A1628`, face wash `#E8F0FE`.

**Demo:** [`../../demo/cody-cursor/overlay.html`](../../demo/cody-cursor/overlay.html) · host iframe: [`../../demo/cody-cursor/host.html`](../../demo/cody-cursor/host.html).

License: original for Cody sprint; free to replace with final art using the same hotspot.
