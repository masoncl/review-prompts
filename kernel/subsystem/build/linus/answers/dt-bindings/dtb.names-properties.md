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
