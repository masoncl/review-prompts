- `dt-validate` input: the compiled `.dtb`, not the source; see
  `cmd_dtb_check` in `scripts/Makefile.dtbs`. The in-tree dtc is built with
  `-DNO_YAML` (`scripts/dtc/Makefile`).
- Source-level style: checked by `scripts/dtc/dt-check-style`, not by the
  schemas.
- `dt-check-style` on `.dts` files: the only Makefile that calls it is the
  bindings one, on schemas, so no build target checks a board `.dts`.
  `dt_style_selftest` runs it on fixtures, to test the checker itself.
- `%.example.dtb`: built and validated by the same `cmd_dtc` and
  `cmd_dtb_check` as a board DTB. `scripts/Makefile.build` includes
  `scripts/Makefile.dtbs` whenever `targets` holds a `%.dtb`.
- `dt-validate` call site: `scripts/Makefile.dtbs`, not
  `scripts/Makefile.lib`.
- `processed-schema.json`: always built from every schema (`find_all_cmd`),
  whatever `DT_SCHEMA_FILES` holds.
- `DT_SCHEMA_FILES`: narrows `find_cmd`, which picks the files that are linted
  and whose examples are built. It also changes the default
  `DT_CHECKER_FLAGS` from `-m` to `-l $(DT_SCHEMA_FILES)`.
- Overlay (`.dtso` source, `.dtbo` output): never validated on its own,
  because `dtb-check-enabled` matches `%.dtb` only. It is checked only as part
  of a composite `.dtb` that a `-dtbs` variable names and `fdtoverlay` builds.
  `scripts/Makefile.dtbs` warns about a `.dtbo` applied to no base.
- `select: true`: 15 in-tree schemas apply to every node, whatever its
  `compatible`. Examples are
  `Documentation/devicetree/bindings/vendor-prefixes.yaml` and consumer
  schemas such as
  `Documentation/devicetree/bindings/gpio/gpio-consumer-common.yaml`.
- `$ref: /schemas/...` targets with no file under
  `Documentation/devicetree/bindings/`, such as
  `/schemas/i2c/i2c-controller.yaml#` and `/schemas/types.yaml`: they come
  from the installed dtschema package.
- In-tree common schemas:
  `Documentation/devicetree/bindings/spi/spi-controller.yaml` and
  `Documentation/devicetree/bindings/spi/spi-peripheral-props.yaml` are files
  in this tree.
- `additionalProperties: false` with a `$ref` in the top-level `allOf`: used
  by several hundred bindings, for example
  `Documentation/devicetree/bindings/rtc/arm,pl031.yaml`, which lists
  `start-year: true`.
- Binding and `struct of_device_id` table: the checks run from code to binding
  only. `dt_compatible_check` (compatibles in `.c` files) and
  `UNDOCUMENTED_DT_STRING` (added lines in `.c`, `.h`, `.dts` and `.dtsi`
  files) want a compatible in a driver or DTS to be documented.
- `dt_compatible_check`: pipes `scripts/dtc/dt-extract-compatibles` output
  into `dt-check-compatible` against `processed-schema.json`.
- `Documentation/devicetree/bindings/trivial-devices.yaml`: ends
  `additionalProperties: false`, so a device that needs a supply or a GPIO
  needs its own binding.
- Licence checks in `scripts/checkpatch.pl`: a file under
  `Documentation/devicetree/bindings/` must be `GPL-2.0` or `GPL-2.0-only`
  `OR BSD-2-Clause`. A header under `include/dt-bindings/` may pair GPL-2.0
  with any second licence.
