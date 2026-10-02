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
