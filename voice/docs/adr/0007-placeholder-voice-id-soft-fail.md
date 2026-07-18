# Placeholder speaker / reference soft-fail

Missing, blank, or placeholder-looking `speaker` values soft-fail as `false`. When `tone_convert` is true, a missing/placeholder `reference_wav` also soft-fails without calling the synthesizer.
