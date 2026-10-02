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
