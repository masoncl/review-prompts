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
