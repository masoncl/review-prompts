Read the prompts {{REVIEW_DIR}}/slop-indicators.md and {{REVIEW_DIR}}/subsystem/subjective-review.md

This is a standalone run of the subjective slop pass (normally part of agent/review.md's
PHASE 4.5, gated by agent/report.md), for testing and calibration.

Assess the top commit, or the provided patch/commit, for the SLOP-* stylistic tells. Apply the
confidence discipline in {{REVIEW_DIR}}/false-positive-guide.md section 11.1: high bar, cluster
requirement, compare to neighbouring code, defer correctness to a real review, debate yourself,
and a hard cap of 3 observations.

Output findings as gentle, question-posed comments per {{REVIEW_DIR}}/inline-template.md
("this isn't a bug, but ..."), naming the specific code or prose. Never mention the author and
never imply the code was machine-generated. If nothing clears the bar, say so and emit nothing.
