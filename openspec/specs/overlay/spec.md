## Purpose

Cody’s desktop AI cursor (Clicky-style) follows the user then points at the real Explorer file icon after reveal.

## Requirements

### Requirement: Follow / point / stop contract
The overlay SHALL expose `start_follow()`, `point_at(path) -> bool`, and `stop()`.

#### Scenario: Point at existing file
- **GIVEN** an existing file path and follow armed
- **WHEN** `point_at` is called
- **THEN** the cursor MUST animate toward the icon (or soft geometric fallback) and return `true` on success

#### Scenario: Missing file
- **GIVEN** a path that is not an existing file
- **WHEN** `point_at` is called
- **THEN** it MUST return `false` and MUST NOT raise

### Requirement: Soft-fail without UI Automation
If UI Automation is unavailable, `point_at` MUST still attempt a visible soft fallback after reveal rather than crashing.
