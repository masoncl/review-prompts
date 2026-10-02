- Preface of `Documentation/devicetree/bindings/writing-bindings.rst`: "With
  every rule, there are exceptions"; every DO and DON'T below is under it.
- Wildcards and device-family names: one DON'T bullet covers both, with no
  exception for a well-defined family.
- Versioned IP blocks: discouraged, in a bullet under "Typical cases and
  caveats", not under "Properties".
  - Scope of that bullet: "sub-blocks/components of bigger device (e.g. SoC
    blocks)", and "custom versioning".
  - Its example: `vendor,soc1234-i2c` instead of `vendor,i2c-v2`.
  - No `.rst` file under `Documentation/devicetree/` states an exception for a
    vendor-documented version scheme.
- `syscon` alone without a specific compatible: the DON'T bullet is under
  "Overall design"; see "Nodes and generic compatibles".
- New features or bugs: DO add a new compatible.
