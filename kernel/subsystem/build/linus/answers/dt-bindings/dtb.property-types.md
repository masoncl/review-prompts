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
