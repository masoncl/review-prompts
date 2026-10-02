- Path match: nothing in this tree compares `$id` with the file's path;
  `writing-schema.rst` only says the URI "typically" contains filename and
  path and must begin `http://devicetree.org/schemas/`.
- `dt-doc-validate`: comes from the dtschema package, not from this tree; any
  `$id`-against-path check and its message text live there and cannot be
  read here.
- Leading-slash `$ref`: `writing-schema.rst` says only the hostname is
  prepended, so the reference must spell `/schemas/` itself; every
  leading-slash `$ref` under `Documentation/devicetree/bindings/` does.
- `$ref` beginning `../`: in use in about thirty binding files, for example
  `Documentation/devicetree/bindings/display/panel/panel-simple.yaml`;
  `writing-schema.rst` has no rule against it.
- Trailing `#`: every `$id` under bindings ends in `#`; a `$ref` often does
  not, for example `$ref: spi-peripheral-props.yaml` in
  `Documentation/devicetree/bindings/spi/spi-controller.yaml`.
