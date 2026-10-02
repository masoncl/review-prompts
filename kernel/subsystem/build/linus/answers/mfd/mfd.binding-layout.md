- `Documentation/devicetree/bindings/mfd/mfd.txt`: does not require a
  device-specific compatible in front of `simple-mfd`, and says nothing about
  fallback order.
- Example in `mfd.txt`: `compatible = "syscon", "simple-mfd"`, no `ranges`,
  and a child `led@8.0` with `offset` and `mask` and no `reg`.
- `Documentation/devicetree/bindings/mfd/syscon-common.yaml`: holds the
  specific-compatible rule; when the list contains `simple-mfd` it sets
  `minItems: 3`. The schema selects only nodes whose list contains `syscon`.
- The `mfd.txt` example does not satisfy `syscon-common.yaml`; a new binding
  follows the schema.
- `Documentation/devicetree/bindings/writing-bindings.rst`: has the explicit
  rule "DON'T use 'simple-mfd' compatible for non-trivial devices, where
  children depend on some resources from the parent".
- `writing-bindings.rst` also has "DON'T use 'syscon' alone without a specific
  compatible string".
- `mfd.txt` gives two conditions for `simple-mfd`: the subnodes are separate
  and independent, "not needing any resources to be provided by the parent
  device"; and the nexus driver does not have to probe registers to find the
  children.
- `mfd.txt` has no sentence about using `simple-mfd` to avoid writing a
  driver; the nearest text is "DON'T create nodes just for the sake of
  instantiating drivers" in `writing-bindings.rst`.
- `ranges` in `mfd.txt`: listed under optional properties; the file does not
  mention empty `ranges`, regmap children, or when `ranges` is expected.
- `#address-cells` and `#size-cells` in `mfd.txt`: listed as optional, each
  with "Must be present if ranges is used".
