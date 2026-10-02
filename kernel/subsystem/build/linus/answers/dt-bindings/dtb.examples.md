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
