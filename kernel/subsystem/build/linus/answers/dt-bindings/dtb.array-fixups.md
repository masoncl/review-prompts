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
