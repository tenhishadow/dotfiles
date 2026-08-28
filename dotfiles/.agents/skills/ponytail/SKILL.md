---
name: ponytail
description: >
  Apply an intentionally minimal coding approach only when the user explicitly
  invokes Ponytail or asks for Ponytail mode. Prefer existing code, standard
  library features, and the smallest complete change. Default to lite; full and
  ultra are explicit intensities. Do not invoke implicitly for ordinary coding
  tasks, generic requests for simplicity, or non-coding work.
license: MIT
metadata:
  source: "https://github.com/DietrichGebert/ponytail"
  upstream_version: "4.9.0"
  local_policy: "opt-in-lite"
---

# Ponytail

Use a deliberately minimal engineering approach without reducing correctness,
scope, or validation. This local adaptation is opt-in and defaults to lite.

## Activation

Activate only when the user explicitly invokes Ponytail. Apply it to the
current request unless the user explicitly asks for it to persist through the
session. Use lite unless the user selects full or ultra. Stop when the user
says `stop ponytail` or `normal mode`.

## Method

Stop at the first rung that holds:

1. Understand the requested behavior and trace the affected flow.
2. Reuse an existing helper, type, or pattern when it fits.
3. Prefer the standard library or a native platform feature.
4. Prefer an already-installed dependency over a new dependency.
5. Implement the smallest complete solution that preserves the requested
   behavior and repository conventions.

For bugs, fix the shared root cause when evidence supports it. Do not replace a
requested solution with a smaller, incomplete substitute. Question speculative
scope before implementing it when doing so would materially change the result.

## Intensity

| Level | Behavior |
| ----- | -------- |
| **lite** | Implement the full request with a narrow diff and avoid speculative machinery. This is the default. |
| **full** | Apply the method strictly and identify meaningful scope or dependency reductions before coding. |
| **ultra** | Challenge speculative requirements first and favor deletion, but obtain direction before materially reducing requested scope. |

## Completeness and validation

Never simplify away trust-boundary validation, data-loss prevention, security,
accessibility, explicit requirements, or necessary compatibility behavior.
Follow the user's and repository's validation contract. Choose checks in
proportion to risk and reuse the existing test framework and fixtures. Ponytail
does not cap the number or size of tests; run every applicable required check
and report blockers.

## Output

Follow the user's requested format and the active repository instructions.
Mention omitted optional work only when it helps the user evaluate a real
tradeoff.
