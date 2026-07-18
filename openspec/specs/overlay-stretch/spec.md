## Purpose

The stretch pointing overlay optionally highlights the real Explorer file icon via Windows UI Automation after reveal succeeds; it is never required for demo success and must fail silently.

## Requirements

### Requirement: Same path input as reveal
Overlay SHALL accept an `OverlayRequest` path shape matching reveal input (`spec.md` §6.8).

#### Scenario: Post-reveal call
- **GIVEN** reveal has opened Explorer on a resolved path
- **WHEN** overlay is attempted
- **THEN** it MUST use that same path without new upstream dependencies

### Requirement: Silent failure
If icon coordinates cannot be resolved, overlay MUST return `false` (or no-op) without breaking baseline reveal or in-app animation.

#### Scenario: Timing race
- **GIVEN** Explorer is not yet painted or view mode hides the icon
- **WHEN** accessibility lookup fails
- **THEN** the demo MUST continue on baseline §6.5 + §6.7 with nothing visibly broken

### Requirement: Optional cutoff
Overlay work SHALL be attempted only after a primary component is done and MUST be dropped if not visibly working by the 2:00 sprint cutoff.

#### Scenario: Cutoff reached without reliable overlay
- **GIVEN** overlay is flaky at the 2:00 mark
- **WHEN** the stretch cutoff hits
- **THEN** the team MUST ship without overlay and treat baseline as the demo
