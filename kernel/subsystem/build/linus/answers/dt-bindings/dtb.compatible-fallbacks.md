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
