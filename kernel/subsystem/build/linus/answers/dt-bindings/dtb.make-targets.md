| Job | Target | Rule is in | Work is done in |
|---|---|---|---|
| build the processed schema | `dt_binding_schemas` | top-level `Makefile` only | default build of `Documentation/devicetree/bindings/Makefile`, through `always-y += processed-schema.json` |
| validate built DTBs | `dtbs_check` | top-level `Makefile` only (`dtbs_check: dtbs`) | `cmd_dtb_check` in `scripts/Makefile.dtbs`, appended to the `.dtb` build command |
| one schema with its example | `make sram/sram.yaml` | `%.yaml: dtbs_prepare` in top-level `Makefile` | builds `<name>.example.dtb` and `dt_binding_check_one` in the bindings Makefile |

- `%.yaml` goal: a path relative to `Documentation/devicetree/bindings`; the
  recipe prefixes `$(dtbindingtree)/` itself.
- `dt_binding_check_one`: the three lint stamps (`.dt-binding.checked`,
  `.yamllint.checked`, `.dt-style.checked`) without any example;
  `dt_binding_check` is that plus `$(CHK_DT_EXAMPLES)`.
- `%.yaml` rule: does not set `DT_SCHEMA_FILES`, so the lint steps still cover
  every schema `find_cmd` selects; only the example build is limited to the
  named file.
- `dtbs_prepare`, `dtbs_check` and the `CHECK_DTBS=y` export for `%.yaml`
  goals: inside `ifneq ($(dtstree),)`, so they exist only when
  `arch/$(SRCARCH)/boot/dts/` does; the `%.yaml` rule itself is outside it.
- `dt_binding_check`: has its own `CHECK_DTBS=y` export outside that block and
  does not depend on `dtbs_prepare`.
- `dtbs_check` builds `processed-schema.json` only through
  `dtbs_prepare: dt_binding_schemas`, which is added when `CHECK_DTBS` is set.
