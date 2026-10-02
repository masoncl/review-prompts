# Device Tree Bindings Subsystem Details

## Main structures

### Objects and how they relate

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

## Where to look

**Authoritative documents**

| Subject | Authority | Easy to miss |
|---|---|---|
| How devicetree patches are reviewed and applied | `Documentation/process/maintainer-devicetree.rst`, the `P:` entry of both `MAINTAINERS` sections whose name starts "OPEN FIRMWARE AND FLATTENED DEVICE TREE" | It says who reviews and who applies core OF code and bindings, and that review of DTS and drivers by DT maintainers is generally not expected. It defines the Patchwork statuses: "Not Applicable" means reviewed, someone else applies. It says when to drop a DT maintainer's tag on a new version. |
| Which binding patches the DT maintainers apply themselves | No document lists them | `maintainer-devicetree.rst` says only "except in certain cases". Section II of `Documentation/devicetree/bindings/submitting-patches.rst` says the binding stays with its driver and DTS never goes through a driver subsystem tree. |
| DTS coding style: indentation and wrapping | `Documentation/process/coding-style.rst` | `Documentation/devicetree/bindings/dts-coding-style.rst` delegates these two; it keeps naming, ordering, array formatting and file organisation. |
| Indentation of YAML and of the example DTS in a binding | Section "Coding style" of `Documentation/devicetree/bindings/writing-schema.rst` | Two spaces for YAML, four spaces for the example. |
| DTS style checker | `scripts/dtc/dt-check-style` | New binding examples should pass strict mode (`submitting-patches.rst`, item I.2). New DTS code must have no warnings in relaxed mode (`Documentation/process/maintainer-soc.rst`, "Validating Devicetree Files"). |
| DTS structure, such as MMIO devices under a bus node and non-empty `ranges` | Section "Board/SoC .dts Files" of `Documentation/devicetree/bindings/writing-bindings.rst` | These rules are not in `dts-coding-style.rst`. |
| ABI stability of DTS changes | Section "Devicetree ABI Stability" of `Documentation/process/maintainer-soc.rst` | `Documentation/devicetree/bindings/ABI.rst` covers bindings and drivers only. `writing-bindings.rst` adds that node names are not ABI and property constraints are. |

**Schemas outside the tree**

- `$schema` value: `http://devicetree.org/meta-schemas/core.yaml#` in every
  binding except three, which name
  `http://devicetree.org/meta-schemas/base.yaml#`:
  `Documentation/devicetree/bindings/nvmem/nvmem-consumer.yaml`,
  `Documentation/devicetree/bindings/nvmem/nvmem-provider.yaml` and
  `Documentation/devicetree/bindings/thermal/thermal-zones.yaml`.
- Relative `$ref` with `../`: in use across the tree for targets that exist
  under `Documentation/devicetree/bindings/`, for example
  `$ref: ../connector/usb-connector.yaml#` in
  `Documentation/devicetree/bindings/usb/maxim,max33359.yaml`.
- Refs to external schemas, absolute form: for example
  `/schemas/types.yaml#/definitions/uint32` and
  `/schemas/graph.yaml#/properties/port`.
- Refs to external schemas, bare file name: also in use, from a binding whose
  `$id` is in the same namespace directory, for example
  `$ref: reserved-memory.yaml` in
  `Documentation/devicetree/bindings/reserved-memory/ramoops.yaml`.
- External schemas in a namespace directory that also exists in the tree:
  `/schemas/i2c/i2c-controller.yaml`, `/schemas/pci/pci-host-bridge.yaml` and
  `/schemas/reserved-memory/reserved-memory.yaml` have no file under
  `Documentation/devicetree/bindings/i2c/`,
  `Documentation/devicetree/bindings/pci/` or
  `Documentation/devicetree/bindings/reserved-memory/`.
- External schemas at the top level: `/schemas/graph.yaml` and
  `/schemas/simple-bus.yaml` have no file in the tree either.
- Telling in-tree from external: look for the file under
  `Documentation/devicetree/bindings/`; the `$ref` itself looks the same.
- Stub files: a search of the tree for a moved common binding finds a short
  `.txt` pointer, for example `Documentation/devicetree/bindings/graph.txt`,
  `Documentation/devicetree/bindings/clock/clock-bindings.txt` and
  `Documentation/devicetree/bindings/reserved-memory/reserved-memory.txt`.
- Not every stub points outside the tree: for example
  `Documentation/devicetree/bindings/spi/spi-bus.txt` points to the in-tree
  `spi-controller.yaml`.
- `DT_SCHEMA_MIN_VERSION`: set to `2024.4` in
  `Documentation/devicetree/bindings/Makefile`; `check_dtschema_version`
  compares it with the output of `dt-doc-validate --version`.
- Tool invocations: `dt-doc-validate -u $(src)` and `dt-mk-schema` are in
  `Documentation/devicetree/bindings/Makefile`.
- `dt-validate`: invoked from `cmd_dtb_check` in `scripts/Makefile.dtbs`, with
  `-u` naming the bindings directory and `-p` naming `processed-schema.json`.

## Checks and tools

**Make targets**

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

**Steps of the binding check**

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

**Example style checker**

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

**checkpatch warnings for bindings**

| Type | Fires when | Reads |
|---|---|---|
| `DT_SPLIT_BINDING_PATCH` | two consecutive files in the patch differ in whether the path starts with `Documentation/devicetree/` or `include/dt-bindings/` | file names from `diff --git` and `+++` lines |
| `DT_SCHEMA_BINDING_PATCH` | `new file mode` line for a `.txt` file anywhere under `Documentation/devicetree/bindings/` | that line and the file name |
| `UNDOCUMENTED_DT_STRING` (string) | `grep -Erq` of the bindings directory finds no match | added line, working tree |
| `UNDOCUMENTED_DT_STRING` (vendor) | `"^vendor,.*":` not in `vendor-prefixes.yaml` | added line, that file |
| `SPDX_LICENSE_TAG` (headers) | file under `include/dt-bindings/` whose tag lacks `GPL-2.0-only OR <anything>` (`GPL-2.0 OR` also passes) | added SPDX line |
| `UNCOMMENTED_RGMII_MODE` | `phy-mode` or `phy-connection-type` set to `"rgmii"`, `"rgmii-rxid"` or `"rgmii-txid"` with no comment | added line of a `.dts`, `.dtsi` or `.dtso` file |

- `DT_SPLIT_BINDING_PATCH` path test: all of `Documentation/devicetree/`, not
  only `Documentation/devicetree/bindings/`.
- `DT_SPLIT_BINDING_PATCH` and `MAINTAINERS`: that file is skipped, so a
  binding patch that also edits `MAINTAINERS` does not warn.
- `DT_SPLIT_BINDING_PATCH` count: one warning per switch between the two kinds,
  in the order the files appear in the patch.
- `UNDOCUMENTED_DT_STRING` files: only `.dts` and `.dtsi` (line starts
  `compatible = "`) and `.c` and `.h` (line contains `.compatible = "`);
  `.dtso` and `.yaml` files are not tested, so binding examples are not.
- `UNDOCUMENTED_DT_STRING` lines: only an added line that itself holds
  `compatible =`; every quoted string on that line is tested, strings on
  continuation lines are not.
- `UNDOCUMENTED_DT_STRING` skips strings that start `pciclass,`, `pci` plus
  2-4 hex digits and a comma, or `usb`/`usbif` plus 1-4 hex digits and a comma.
- `UNDOCUMENTED_DT_STRING` lookup: plain `grep`, not `git grep`; the string is
  used as an unanchored extended regex, so a match inside a longer string in
  any file under the bindings directory silences the warning.
- `UNDOCUMENTED_DT_STRING` with `--no-tree`: skipped unless `--root` is given,
  since the test is `defined $root`.
- `SPDX_LICENSE_TAG` for headers: always `WARN`, and `--fix` does not rewrite
  it; the binding-document variant is `CHK` with `-f` and is rewritten by
  `--fix`.
- Both `SPDX_LICENSE_TAG` licence tests: read only line 1 of the file (line 2
  after a `#!` line), and only when the patch adds that line.

## Schema structure

**Schema identifier**

- Path match: nothing in this tree compares `$id` with the file's path;
  `writing-schema.rst` only says the URI "typically" contains filename and
  path and must begin `http://devicetree.org/schemas/`.
- `dt-doc-validate`: comes from the dtschema package, not from this tree; any
  `$id`-against-path check and its message text live there and cannot be
  read here.
- Leading-slash `$ref`: `writing-schema.rst` says only the hostname is
  prepended, so the reference must spell `/schemas/` itself; every
  leading-slash `$ref` under `Documentation/devicetree/bindings/` does.
- `$ref` beginning `../`: in use in about thirty binding files, for example
  `Documentation/devicetree/bindings/display/panel/panel-simple.yaml`;
  `writing-schema.rst` has no rule against it.
- Trailing `#`: every `$id` under bindings ends in `#`; a `$ref` often does
  not, for example `$ref: spi-peripheral-props.yaml` in
  `Documentation/devicetree/bindings/spi/spi-controller.yaml`.

**additionalProperties and unevaluatedProperties**

- `additionalProperties: false` with a `$ref`: `writing-schema.rst` asks for
  it when the binding allows only a subset of the referenced schema's
  properties; each allowed one is then listed, as `reg: true` and
  `spi-max-frequency: true` are in
  `Documentation/devicetree/bindings/display/sitronix,st7735r.yaml`.
- `unevaluatedProperties: false`: `writing-schema.rst` asks for it only when
  all properties of the referenced schema should be allowed; it does not tie
  it to properties defined under `then`.
- Comment above `additionalProperties: false` in
  `Documentation/devicetree/bindings/example-schema.yaml`: says the keyword
  "can't be used" where another schema is referenced; `writing-schema.rst`
  and the in-tree schema above do otherwise.
- Nested `additionalProperties: true`: allowed by `writing-schema.rst` only
  when the node lists just the expected compatible and another schema
  matching that compatible ends in one of the `false` forms; see
  `child-node-with-own-schema` in `example-schema.yaml`.
- `spi-controller.yaml` child pattern: `"@[0-9a-f]+$"`, with no leading
  `^.*`.
- `spi-controller.yaml` child, properties defined in place: only
  `spi-3wire`, `spi-cpha` and `spi-cpol`; `reg`, `spi-max-frequency` and the
  rest come from `$ref: spi-peripheral-props.yaml`.
- Fit with the nested-node rule: the child does not fit its wording; it
  names no compatible value, pulls in a `$ref` and adds properties of its
  own.
- Why it is open: the child pattern sets `additionalProperties: true` and
  `spi-peripheral-props.yaml` ends `additionalProperties: true`, so nothing
  in `spi-controller.yaml` closes the child; that is left to the device's
  own schema.
- Device schemas that close an SPI child: some end
  `additionalProperties: false` (`sitronix,st7735r.yaml`), not all
  `unevaluatedProperties: false`.
- `slave` child in `spi-controller.yaml`: `type: object` requiring
  `compatible`, with neither `additionalProperties` nor
  `unevaluatedProperties`.

**Properties inside if/then blocks**

- `unevaluatedProperties: false`: a property defined only in a `then` is
  accepted on nodes whose `if` matched.
  `Documentation/devicetree/bindings/mmc/renesas,sdhi.yaml` relies on this
  for `vqmmc-regulator`, which
  `arch/arm64/boot/dts/renesas/r9a09g047.dtsi` uses.
- **Potentially unsafe usage**: defining a property only inside an
  `if`/`then` block.
  - Unsafe: when the schema ends `additionalProperties: false` and no
    top-level `properties` or `patternProperties` entry matches the name;
    the property is rejected on every node.
  - Unsafe: on a node where the `if` does not match, under either keyword.
  - Safe: when the schema ends `unevaluatedProperties: false` and the
    property is wanted only where the `if` matches, as `vqmmc-regulator` in
    `renesas,sdhi.yaml`; `writing-schema.rst` still says not to.
  - Safe: under `additionalProperties: false` when a top-level
    `patternProperties` entry matches the name, as
    `"^vs(ys|[12])-ldo[1-9]-supply$"` does for `vsys-ldo1-supply` in
    `Documentation/devicetree/bindings/mfd/mediatek,mt6397.yaml`;
    `writing-schema.rst` defines the keyword as acting on properties not
    matched by the schema's 'properties' or 'patternProperties'.
- Wording in `writing-schema.rst`: "should be constrained for each device.
  This usually means", then three bullets; it is guidance with "usually",
  not "must".
- Parenthetical in the third bullet of `writing-schema.rst`: names
  'additionalItems'; the text says nothing about `unevaluatedProperties` and
  `if`/`then`.
- `Documentation/devicetree/bindings/writing-bindings.rst`: has no rule
  about `if`/`then`; its only related line is the choice between the two
  keywords.

**Conditions on compatible**

- Schemas that show both an `if` on a fallback string and an `if` on a
  specific string:
  `Documentation/devicetree/bindings/serial/renesas,scif.yaml` and
  `Documentation/devicetree/bindings/mmc/renesas,sdhi.yaml`.
- `renesas,scif.yaml`: one `if` lists the family fallbacks
  (`renesas,rcar-gen1-scif` and later generations); another lists only
  `renesas,scif-r7s72100`.
- `Documentation/devicetree/bindings/i2c/snps,designware-i2c.yaml`: does not
  show both; its single `if` is `not: contains: const: mscc,ocelot-i2c`,
  which matches every node except that one.
- A string can be both specific and a fallback: `renesas,scif-r9a07g044`,
  `renesas,scif-r9a09g057` and `renesas,sdhi-r9a09g057` each stand alone in
  the top-level `compatible` and end another `items` list.
- An `if` that names such a string: matches the nodes of every SoC that
  falls back to it; `vqmmc-regulator` in `renesas,sdhi.yaml` reaches
  `renesas,sdhi-r9a09g047` nodes that way.
- New string in the top-level list only: every `else` branch of a
  non-matching `if` applies to it, for example
  `else: required: interrupt-names` in `renesas,scif.yaml`.
- New string that shares a fallback but needs different constraints:
  `renesas,sdhi.yaml` tests the specific strings in the outer `if` and the
  fallback only in a nested `else: if:`, so the fallback block is skipped
  for them.
- Sibling `if` blocks in `allOf`: all that match apply together; a
  `renesas,scif-r9a09g047` node matches both blocks that name
  `renesas,scif-r9a09g057`.
- Generic last fallback `renesas,scif`: named by no `if` in
  `renesas,scif.yaml`; listing it gives a node no block.

## Properties

**Property naming**

- `Documentation/devicetree/bindings/writing-bindings.rst`: a DO/DON'T list of
  "common review feedback items"; its first paragraph says every rule has
  exceptions.
- Character set of a property name: not in `writing-bindings.rst`. It is in
  `Documentation/devicetree/bindings/dts-coding-style.rst`, "Naming and Valid
  Characters": lowercase letters, digits and dash; underscore is listed for
  labels only.
- Registered vendor prefix: `writing-bindings.rst` says only "DO use a vendor
  prefix on device-specific property names"; it does not say the prefix must
  be registered. The schema
  `Documentation/devicetree/bindings/vendor-prefixes.yaml` enforces it:
  `select: true`, `additionalProperties: false`, and its catch-all patterns for
  unprefixed names accept a comma only after `@` (names starting with `#`
  always pass).
- Deducible from compatible: the bullet holds two DON'Ts. "DON'T add properties
  to avoid a specific compatible" and "DON'T add properties if they are implied
  by (deducible from) the compatible".
- Remedy for a deducible property: none is stated; the file does not mention
  match data or what a driver should do.

**Vendor property schemas**

- Boolean vendor property: the only exception to the type reference that
  `Documentation/devicetree/bindings/writing-schema.rst` names; it still needs
  `description`. `Documentation/devicetree/bindings/example-schema.yaml`
  writes it as `type: boolean`.
- Vendor property with a standard unit suffix: needs no type either; see
  `vendor,property-in-standard-units-microvolt` in `example-schema.yaml`.
- `$ref: /schemas/types.yaml#/definitions/flag`: not mentioned in the `.rst`
  guides or `example-schema.yaml`, but used by in-tree bindings for boolean
  vendor properties, for example `upisemi,continuous` in
  `Documentation/devicetree/bindings/iio/light/upisemi,us5182.yaml`. Both forms
  are in the tree.
- Meta-schemas and types.yaml: not in this tree; they come from the external
  dtschema package. There is no vendor-props.yaml here.
- Narrowing inside `if`/`then`: carries the constraint only, with no type and
  no `description`; see `vendor,int-property` under `allOf` in
  `example-schema.yaml`.

**Implicit array constraints**

- Fixup code: not in this tree; it is in the external dtschema package.
  `Documentation/devicetree/bindings/Makefile` runs the installed tools and
  checks their version against `DT_SCHEMA_MIN_VERSION`.
- Constraints the tools add, as far as this tree states them: only that
  `minItems`, `maxItems` and `additionalItems` are added from the number of
  entries in an `items` list. This is in the "Property Schema" section of
  `Documentation/devicetree/bindings/writing-schema.rst` and in the comments
  of `Documentation/devicetree/bindings/example-schema.yaml`.
- `maxItems` alone: `example-schema.yaml` writes a single-entry property as
  `maxItems: 1` with no `minItems` ("Cases that have only a single entry just
  need to express that with maxItems"), see `clocks` and `foo-gpios`.
- Not stated in this tree: what the tools do with a lone `minItems`, whether
  they add `type: array`, and whether any fixup is skipped inside
  `if`/`then`/`else`.
- `clocks` in `example-schema.yaml`: not a list-form `items`. List forms there
  are, for example, `reg`, `reg-names` and `interrupts`.
- `items` as a single schema rather than a list: the documented rule gives no
  count. `vendor,int-array-variable-length-and-constrained-values` in
  `example-schema.yaml` writes both `minItems` and `maxItems` by hand.

**Ordered lists and names**

- When to include `-names`: the only condition in
  `Documentation/devicetree/bindings/writing-bindings.rst` is "if there is
  more than one phandle". It has no condition about optional entries or
  expected future growth.
- Adding entries to an existing list: neither the `.rst` guides nor
  `Documentation/devicetree/bindings/example-schema.yaml` say where new
  entries go. `writing-bindings.rst` says only that order is one of the
  constraints that "represent the ABI".
- Form of the names: `example-schema.yaml` uses one `const` per position. It
  says "pattern matching names are discouraged", in the `description` of
  `clocks` and `interrupts`.

**Provider properties**

- Provider-specific rule: none in the `.rst` guides under
  `Documentation/devicetree/bindings/`. Only the general "DO define properties
  in terms of constraints" in
  `Documentation/devicetree/bindings/writing-bindings.rst` applies.
- `required`: the `.rst` guides and
  `Documentation/devicetree/bindings/example-schema.yaml` do not say whether a
  cell-count property is listed there.
- `example-schema.yaml`: has no `#clock-cells`. It defines `'#interrupt-cells'`
  with `const: 2`; `required` lists `interrupt-controller` but not
  `'#interrupt-cells'`.
- `dependencies` in `example-schema.yaml`: covers only `vendor,bool-property`
  and `vendor,string-array-property`; nothing ties `interrupt-controller` to
  `'#interrupt-cells'` in that file.
- `$ref: /schemas/interrupt-controller.yaml#`: the referenced schema is not in
  this tree, so what it requires cannot be read here.
- In-tree bindings do both. Not listed in `required`:
  `Documentation/devicetree/bindings/interrupt-controller/arm,gic.yaml`
  (`"#interrupt-cells"` `const: 3`, `required` is `compatible` and `reg`).
  Listed: `Documentation/devicetree/bindings/clock/fixed-clock.yaml` and
  `Documentation/devicetree/bindings/clock/qcom,gcc.yaml`.
- **Potentially unsafe usage**: a provider's cell-count property, such as
  `#clock-cells`, written as `true` in the top-level `properties`.
  - Unsafe: in a device binding, when no `if`/`then`/`else` branch and no
    referenced schema constrains the value; nothing in the binding then
    limits the cell count.
  - Safe: when every compatible gets a `const` in an `if`/`then`/`else`
    branch, as `'#interrupt-cells'` in
    `Documentation/devicetree/bindings/interrupt-controller/sifive,plic-1.0.0.yaml`
    and `"#clock-cells"` in
    `Documentation/devicetree/bindings/phy/qcom,sc8280xp-qmp-pcie-phy.yaml`;
    `Documentation/devicetree/bindings/writing-schema.rst` defines this
    layout (broadest constraint at top level, narrowed in `if:then:`).
  - Safe: when a referenced in-tree schema constrains the value, as
    `'#interconnect-cells'` in
    `Documentation/devicetree/bindings/interconnect/qcom,rpmh.yaml`, which
    `$ref: qcom,rpmh-common.yaml#` limits to `enum: [ 1, 2 ]`.
  - Safe: in a common schema that ends `additionalProperties: true`, when the
    binding that references it gives the value, as `'#sound-dai-cells'` in
    `Documentation/devicetree/bindings/sound/dai-common.yaml`, which
    `Documentation/devicetree/bindings/sound/adi,adau1372.yaml` references
    and sets to `const: 0`; `writing-schema.rst` says such schemas are
    meant to be referenced by other schemas.

## Compatible strings and ABI

**Compatible string rules**

- Preface of `Documentation/devicetree/bindings/writing-bindings.rst`: "With
  every rule, there are exceptions"; every DO and DON'T below is under it.
- Wildcards and device-family names: one DON'T bullet covers both, with no
  exception for a well-defined family.
- Versioned IP blocks: discouraged, in a bullet under "Typical cases and
  caveats", not under "Properties".
  - Scope of that bullet: "sub-blocks/components of bigger device (e.g. SoC
    blocks)", and "custom versioning".
  - Its example: `vendor,soc1234-i2c` instead of `vendor,i2c-v2`.
  - No `.rst` file under `Documentation/devicetree/` states an exception for a
    vendor-documented version scheme.
- `syscon` alone without a specific compatible: the DON'T bullet is under
  "Overall design"; see "Nodes and generic compatibles".
- New features or bugs: DO add a new compatible.

**Fallback compatibles**

- Fallback is right: when the device is "the same as or a superset of prior
  implementations", per
  `Documentation/devicetree/bindings/writing-bindings.rst`.
- Named cases where a fallback applies: a shared programming interface, or
  variants that software can discover.
- Devices that look compatible in the diff but get no fallback: the commit
  message has to explain why they are not compatible (a DO bullet).
- SoC-specific fallback: "preferred", not required; the document does not say
  which SoC's string to pick.
- Fallback-alone branch in
  `Documentation/devicetree/bindings/example-schema.yaml`: a one-element
  `items` list holding `const`.
- Bare `- const:` branch directly under `oneOf`: also in the tree, beside
  `items` branches, for example in
  `Documentation/devicetree/bindings/serial/8250.yaml`.
- `Documentation/devicetree/bindings/writing-schema.rst`: says single entries
  in schemas are fixed up by the tools to match the array encoding.

**Vendor-prefix and trivial-device schemas**

- `Documentation/devicetree/bindings/vendor-prefixes.yaml`: has `select: true`,
  so it is applied to every node.
- `vendor-prefixes.yaml` checks names only: property names and child-node
  names; it does not look at the strings inside `compatible`.
- Prefix inside a `compatible` value: checked by `scripts/checkpatch.pl`, which
  warns `UNDOCUMENTED_DT_STRING` when the prefix has no `"^prefix,.*":` line in
  `vendor-prefixes.yaml`.
  - Lines it looks at: added `compatible =` in `.dts` and `.dtsi`, added
    `.compatible =` in `.c` and `.h`.
- New prefix in its own patch: no document here requires it;
  `Documentation/devicetree/bindings/submitting-patches.rst` only asks that
  binding changes be separate from code and come first in the series.
- `Documentation/devicetree/bindings/trivial-devices.yaml` properties:
  `compatible`, `reg`, `interrupts`, `spi-max-frequency`; no supply property.
- `status` and `pinctrl-*`: a comment in
  `Documentation/devicetree/bindings/example-schema.yaml` says the tooling adds
  them to a schema automatically, so `additionalProperties: false` is not meant
  to refuse them.
- Per-class trivial lists: glob `Documentation/devicetree/bindings/` for
  `trivial-*.yaml`; a trivial RTC goes in
  `Documentation/devicetree/bindings/rtc/trivial-rtc.yaml`, which also allows
  `start-year`.
- `Documentation/devicetree/bindings/gpio/trivial-gpio.yaml`: accepts a
  two-string fallback list; `trivial-devices.yaml` accepts one string only.
- `Documentation/devicetree/bindings/incomplete-devices.yaml`: rejects every
  node that uses one of its compatibles.
  - How: it requires `broken-usage-of-incorrect-compatible`, which
    `additionalProperties: false` refuses.
  - Its `description`: such compatibles are not allowed in Devicetree sources
    "even if they come from immutable firmware".
- Purpose of `incomplete-devices.yaml`: compatibles found in drivers count as
  documented for `dt_compatible_check` in
  `Documentation/devicetree/bindings/Makefile`.
- `scripts/checkpatch.pl` documented-compatible check: a text grep over
  `Documentation/devicetree/bindings/`, so a line in `incomplete-devices.yaml`
  silences it too.
- Patch touches `incomplete-devices.yaml`: when a driver gains a compatible
  that will get no binding; one branch is for kernel unit tests and sample
  code, for example `gpio-mockup`.
- Entry in `incomplete-devices.yaml` is not a step towards a binding: a
  compatible that a DTS uses needs a real schema.

**Changes that break old device trees**

- Direction that `Documentation/devicetree/bindings/ABI.rst` guarantees: a
  newer kernel does not break on an older device tree; it says nothing of a
  newer device tree on an older kernel.
- DTS change incompatible with old kernels:
  `Documentation/process/maintainer-soc.rst` allows it, applied no earlier than
  the driver change, and pointed out in the patch description and pull request.
- Incompatible binding change, two requirements from two documents:
  - `ABI.rst`: change the compatible string at the same time; the driver can
    bind against both old and new.
  - `Documentation/devicetree/bindings/writing-bindings.rst`: DON'T break the
    ABI without "explicit and detailed rationale" and a statement of impact.
- Other users of the ABI, by document; none names a specific project:

  | Document | Wording |
  |---|---|
  | `writing-bindings.rst` | "other open-source upstream projects" |
  | `Documentation/devicetree/bindings/submitting-patches.rst` | "multiple projects other than the Linux Kernel" |
  | `maintainer-soc.rst` | "bootloaders or other operating systems" |
  | `ABI.rst` | names none |

- Constraints are ABI: `writing-bindings.rst` counts the number of entries,
  the possible values and the order of a property as ABI.
- `deprecated: true`: no `.rst` file under `Documentation/devicetree/` mentions
  it; it is practice in the schemas, not a written requirement.
- **Potentially unsafe usage**: renaming a property of an existing binding
  under the same compatible.
  - Unsafe: when the driver reads only the new name; a device tree written to
    the old binding then breaks, against rule II.3 of `ABI.rst`.
  - Safe: when the driver still reads the old names, as
    `fwnode_get_phy_node()` in `drivers/net/phy/phy_device.c` does for `phy`
    and `phy-device`, which
    `Documentation/devicetree/bindings/net/ethernet-controller.yaml` marks
    `deprecated: true`.

## Design rules and examples

**Nodes and generic compatibles**

- `Documentation/devicetree/bindings/writing-bindings.rst`: describes itself
  as a list of common review feedback items, and says every rule has
  exceptions and bindings have many gray areas.
- Child nodes of a multi-function device: needed only when the child nodes
  have their own DT resources; the file gives no other allowance and names no
  driver mechanism.
- One node, several providers: the same bullet says a single node can be
  multiple providers, for example clocks and resets.
- `syscon`: not to be used alone; the specific compatible must be unique
  enough to infer the register layout of the entire block, at a minimum.
- `syscon` compatible order: the `syscon` bullet says nothing about which
  entry comes first.
- `simple-mfd`: the rule is not "never alone"; it is not to be used for
  non-trivial devices where children depend on some resources from the
  parent.
- `simple-bus`: same bullet as `simple-mfd`; not for complex buses, and a
  'regs' property (the file's spelling) means the device is not a simple bus.
- "syscon" as a property name: a second item, under "Typical cases and
  caveats", says it is not a generic property; use vendor and type, e.g.
  "vendor,power-manager-syscon".
- Node names: the file says DON'T treat them as a stable ABI; find sibling
  devices by phandle or compatible instead.
- Node name exception: sub-nodes of a given device could be treated as ABI if
  the binding documents them explicitly, so a binding may require a child
  node name.

**Driver-neutral hardware description**

- Completeness example in
  `Documentation/devicetree/bindings/writing-bindings.rst`: if the device has
  an interrupt, include `interrupts` even if the driver is polled-only.
- Stated basis, given in the Linux and driver bullet: bindings are based on
  what the hardware has, not what an OS and driver currently support; the
  file does not give ABI breakage as the reason here.
- Linux and driver rule: covers references to Linux or "device driver"; it
  says nothing about `linux,`-prefixed property names.
- Instance index rule: sits under "Typical cases and caveats", worded "Do not
  add instance index (IDs) properties or custom OF aliases", not under
  "Overall design" or "Properties".
- Alternatives the file gives, in full:
  - devices with a different programming model might need different
    compatibles
  - devices that use some other device differently (e.g. program the phy
    differently) use cell/phandle arguments
- Standard aliases, unit address, `reg`: the file names none of them as a
  substitute for an instance index.
- `cell-index`: not mentioned in the file.

**Example contents**

- Completeness: `Documentation/devicetree/bindings/writing-schema.rst` asks
  for an example that is "complete as much as possible - have most of the
  properties", not a minimal one and not only the required properties.
- `examples`: optional, but expected outside bindings that describe common
  properties or sub-blocks of more complex devices.
- Leave out, per the file:
  - unrelated device nodes, e.g. consumer nodes in a provider binding
  - other nodes referenced by phandles
  - node labels not directly referenced in the example itself
  - the `status` property, "in typical cases"
- Phandles: the file says they do not have to be resolvable.
- Readability: the file asks for known defines for interrupt or GPIO flags.
- Parent bus nodes and variant examples: the file has no rule against either.
- Wrapper and include rule: not in the text of
  `Documentation/devicetree/bindings/writing-schema.rst`; they are comments
  under `examples:` in
  `Documentation/devicetree/bindings/example-schema.yaml`, which that file
  pulls in.
- Wrapper, as far as this tree states it: examples get a default
  `#address-cells` and `#size-cells` of 1; this "can be overridden or an
  appropriate parent bus node should be shown (such as on i2c buses)".
- `dt-extract-example`: not in this tree; `cmd_extract_ex` in
  `Documentation/devicetree/bindings/Makefile` runs it by name
  (`DT_EXTRACT_EX`), so the exact wrapper text cannot be read here.
- Injected labels: `collect_labels_and_refs()` in
  `scripts/dtc/dt-check-style` skips labels starting `fake_intc`; its
  docstring says `dt-extract-example` injects them.
- Includes: "Any includes used have to be explicitly included" is the whole
  rule; neither file restricts which headers.
- Unused labels: `strict` mode of `scripts/dtc/dt-check-style` reports a
  label that is defined and never `&`-referenced in the same example; see
  `check_unused_labels()`.

**Schema and DTS indentation**

- DTS example width: `Documentation/devicetree/bindings/writing-schema.rst`
  says four-space is "preferred";
  `Documentation/devicetree/bindings/example-schema.yaml` says "Use 4-space
  indentation".
- `scripts/dtc/dt-check-style`: checks example style in this tree; it has
  modes `relaxed` (default) and `strict`; the rule table is `RULES`.
- `strict` mode: `Documentation/devicetree/bindings/submitting-patches.rst`
  asks it for examples in new bindings; `indent-unit-strict` accepts only
  four spaces, so a two-space example is reported.
- `strict` mode also checks: the indent of a line against depth times the
  unit (`indent-consistent`, which skips, for example, blank, preprocessor
  and continuation lines and the lines of a block comment after its first),
  and continuation lines aligned under the first `<` or `"`
  (`continuation-alignment`).
- Tabs in an example: `tab-in-yaml` tests the whole line for a tab, not only
  the indent; preprocessor lines are exempt.
- yamllint: `Documentation/devicetree/bindings/.yamllint` sets two-space
  YAML with `indent-sequences: true`; `check-multi-line-strings: false` means
  it does not check indentation inside the example.
- `Documentation/devicetree/bindings/dts-coding-style.rst` in
  `Documentation/devicetree/bindings/writing-schema.rst`: cited for the order
  of entries in `properties` and `required`, not for the example; node and
  property order in examples is checked by `strict` mode.
- Line length: `Documentation/devicetree/bindings/writing-schema.rst` sets
  none; `Documentation/devicetree/bindings/.yamllint` warns above 110
  columns; the `line-length` rule of `strict` mode has a limit of 80 columns.

## Patches

**Patch split and order**

- Separate binding patch: item I.1 of
  `Documentation/devicetree/bindings/submitting-patches.rst` names "the
  Documentation/ and include/dt-bindings/ portion", so a header under
  `include/dt-bindings/` goes in the binding patch, not in the driver patch.
- DTS placement: item I.7 gives two accepted forms, a separate posting, or
  the end of the patchset when combined with driver patches.
- Reasons for keeping DTS apart: item I.7 gives exactly two.
  - DTS is driver-independent hardware description, so placing it last
    shows that the drivers do not depend on the DTS.
  - DTS is applied through a separate tree or branch anyway, so any other
    order indicates a non-bisectable series.
- Merge conflicts, merge timing and ABI stability across kernel versions:
  not given as reasons anywhere in the file.
- ABI: mentioned only in section III, as a pointer to
  `Documentation/devicetree/bindings/ABI.rst`.
- Use by projects other than Linux: item I.9 gives it as a reason for care
  when changing existing bindings, not as a reason for the DTS split.
- Reversed subject prefix `<binding dir>: dt-bindings: ...`: the file lists
  ASoC, media, regulators, SCSI, SPI and UFS.
- Words to keep out of the subject: "Documentation", "doc" and "YAML", and
  a repeated "binding".

**Documenting compatibles before use**

- Binding content when no driver matches the string yet: item I.8 of
  `Documentation/devicetree/bindings/submitting-patches.rst` asks that the
  documentation also include a compatible string that the driver does
  match.
- Completeness of the binding (`reg`, interrupts, clocks, "not a stub"): the
  file states no such requirement for this case.
- Check that the file names for the rule of item I.6: checkpatch only.
- `make dtbs_check`: not mentioned in the file.
- `make dt_binding_check`: appears only in item I.2, as validation of the
  binding files themselves.
- Vendor prefix: the file has no rule about it.
- `UNDOCUMENTED_DT_STRING` in `scripts/checkpatch.pl`: also fires on added
  `.compatible = "` lines in `.c` and `.h` files, which the DTS-only rule of
  item I.6 does not cover.
- `UNDOCUMENTED_DT_STRING` lookup: greps `Documentation/devicetree/bindings/`
  of the tree checkpatch runs in, so the binding has to be applied there
  already.

## Model gaps

### Other mistakes models make

- Models take a failing `dt-validate` to fail the build. `cmd_dtb_check` in
  `scripts/Makefile.dtbs` ends in `|| true`, so its exit status is dropped.
- Models take a fallback to be right when the device is a "subset" of the
  earlier one. `Documentation/devicetree/bindings/writing-bindings.rst`:
  DON'T add fake fallback compatibles that software cannot use to match and
  bind to a device and still operate correctly.
- Models take new `include/dt-bindings/` macros to be the normal way to name
  IDs. `Documentation/process/maintainer-soc.rst` says to avoid them for
  constants derivable from a datasheet and to use them "only ... as a last
  resort".
- Models do not know that
  `Documentation/devicetree/bindings/writing-schema.rst` ("Coding style")
  asks for `properties` and `required` entries in the same order, following
  `Documentation/devicetree/bindings/dts-coding-style.rst`.
- Models take `Documentation/process/` to have no devicetree handbook.
  `Documentation/process/maintainer-devicetree.rst` exists: bindings are
  reviewed by DT maintainers but should be applied by subsystem maintainers
  "except in certain cases"; DTS and driver review by them is generally not
  expected.
