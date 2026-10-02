| Step | Tool | On a finding |
|---|---|---|
| tool version | `check_dtschema_version` | stops |
| YAML lint | `yamllint` (`cmd_yamllint`) | prints only |
| meta-schema | `dt-doc-validate` (`cmd_chk_bindings`) | prints only |
| example DTS style | `scripts/dtc/dt-check-style` (`cmd_chk_style`) | prints only |
| processed schema | `dt-mk-schema` (`cmd_mk_schema`) | non-zero exit stops |
| extract example | `dt-extract-example` (`cmd_extract_ex`) | non-zero exit stops |
| compile example | C preprocessor and `dtc` (`cmd_dtc` in `scripts/Makefile.dtbs`) | non-zero exit stops |
| example against schema | `dt-validate` (`cmd_dtb_check` in `scripts/Makefile.dtbs`) | prints only |

- `cmd_chk_bindings`, `cmd_chk_style`, `cmd_yamllint`: each has
  `&& touch $@ || true`; a non-zero exit from the tool leaves the stamp file
  untouched and the recipe still succeeds.
- `cmd_mk_schema`, `cmd_extract_ex`: no `|| true`; `cmd` in
  `scripts/Kbuild.include` runs them under `set -e`.
- `check_dtschema_version`: fails when `dt-doc-validate` is missing or older
  than `DT_SCHEMA_MIN_VERSION`; it is a prerequisite of `processed-schema.json`
  and of every `%.example.dts`, not of the three stamp targets.
- `yamllint` not installed: `DT_SCHEMA_LINT` is empty and the
  `.yamllint.checked` recipe is empty; the "skipping" warning goes to stderr
  and the build continues.
- Stamp missing or older than a schema file after a failing lint step: the
  step runs again on the next invocation and reprints.
- `.example.dtb` with `dt-validate` findings: the file is still created, so the
  next run does not rerun `dt-validate` for it unless a prerequisite or the
  command line changed (`processed-schema.json` is a prerequisite, and it
  depends on every schema file).
- A zero exit status covers only: tool version, schema processing, example
  extraction, `dtc` compiling the example.
- A zero exit status does not cover: `yamllint`, meta-schema, style, or
  example-against-schema findings; those are in the log only.
- Style in strict mode: not run at all; see "Example style checker".
