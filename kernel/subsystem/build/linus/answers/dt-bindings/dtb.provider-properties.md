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
