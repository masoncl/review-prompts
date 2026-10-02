- `additionalProperties: false` with a `$ref`: `writing-schema.rst` asks for
  it when the binding allows only a subset of the referenced schema's
  properties; each allowed one is then listed, as `reg: true` and
  `spi-max-frequency: true` are in
  `Documentation/devicetree/bindings/display/sitronix,st7735r.yaml`.
- `unevaluatedProperties: false`: `writing-schema.rst` asks for it only when
  all properties of the referenced schema should be allowed; it does not tie
  it to properties defined under `then`.
- Comment above `additionalProperties: false` in
  `Documentation/devicetree/bindings/example-schema.yaml`: says the keyword
  "can't be used" where another schema is referenced; `writing-schema.rst`
  and the in-tree schema above do otherwise.
- Nested `additionalProperties: true`: allowed by `writing-schema.rst` only
  when the node lists just the expected compatible and another schema
  matching that compatible ends in one of the `false` forms; see
  `child-node-with-own-schema` in `example-schema.yaml`.
- `spi-controller.yaml` child pattern: `"@[0-9a-f]+$"`, with no leading
  `^.*`.
- `spi-controller.yaml` child, properties defined in place: only
  `spi-3wire`, `spi-cpha` and `spi-cpol`; `reg`, `spi-max-frequency` and the
  rest come from `$ref: spi-peripheral-props.yaml`.
- Fit with the nested-node rule: the child does not fit its wording; it
  names no compatible value, pulls in a `$ref` and adds properties of its
  own.
- Why it is open: the child pattern sets `additionalProperties: true` and
  `spi-peripheral-props.yaml` ends `additionalProperties: true`, so nothing
  in `spi-controller.yaml` closes the child; that is left to the device's
  own schema.
- Device schemas that close an SPI child: some end
  `additionalProperties: false` (`sitronix,st7735r.yaml`), not all
  `unevaluatedProperties: false`.
- `slave` child in `spi-controller.yaml`: `type: object` requiring
  `compatible`, with neither `additionalProperties` nor
  `unevaluatedProperties`.
