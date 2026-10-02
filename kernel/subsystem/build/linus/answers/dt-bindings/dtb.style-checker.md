- `scripts/dtc/dt-check-style`: in-tree Python checker for the rules of
  `Documentation/devicetree/bindings/dts-coding-style.rst`; needs
  `ruamel.yaml`.
- Input: `.yaml` files (each `examples:` entry is one block) and
  `.dts`/`.dtsi`/`.dtso` files (whole file is one block).
- `dt_binding_check`: runs it through `dt_binding_check_one` and
  `.dt-style.checked`, with `cmd_chk_style` in
  `Documentation/devicetree/bindings/Makefile`.
- Options passed by `cmd_chk_style`: none besides the `@argfile` list from
  `find_cmd`; no `--mode`, so the default `relaxed`; no `-j`, worker count
  comes from `PARALLELISM`, which `scripts/jobserver-exec` sets when it finds
  a make jobserver, else from `os.cpu_count()`.
- Relaxed mode on a `.yaml` file: only `trailing-whitespace`, `tab-in-yaml` and
  `unclosed-block-comment` run.
- Strict-only rules on a `.yaml` file: every other rule whose `applies_to`
  includes `yaml`, for example indentation, node and property order, line
  length and unused labels; see `RULES` in the script, or `--list-rules`.
- Findings: printed to stderr, exit status 1.
- `Documentation/devicetree/bindings/submitting-patches.rst`: the example DTS
  in new bindings should pass `scripts/dtc/dt-check-style` in 'strict' mode
  without warnings.
- `Documentation/process/maintainer-soc.rst`: new DTS code must have no
  relaxed-mode warnings and should address most strict-mode warnings; it notes
  strict mode may give false positives.
- A clean `dt_binding_check` therefore does not show the documented
  requirement is met; that needs
  `scripts/dtc/dt-check-style --mode=strict <file>.yaml` run by hand.
- `scripts/checkpatch.pl`: does not call `dt-check-style`.
- `dt_style_selftest` in the top-level `Makefile`: runs
  `scripts/dtc/dt-style-selftest/run.sh` over the `good/` and `bad/` fixtures;
  a patch that changes a rule needs matching fixture and `expected/` updates.
