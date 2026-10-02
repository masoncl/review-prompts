- `Documentation/devicetree/bindings/vendor-prefixes.yaml`: has `select: true`,
  so it is applied to every node.
- `vendor-prefixes.yaml` checks names only: property names and child-node
  names; it does not look at the strings inside `compatible`.
- Prefix inside a `compatible` value: checked by `scripts/checkpatch.pl`, which
  warns `UNDOCUMENTED_DT_STRING` when the prefix has no `"^prefix,.*":` line in
  `vendor-prefixes.yaml`.
  - Lines it looks at: added `compatible =` in `.dts` and `.dtsi`, added
    `.compatible =` in `.c` and `.h`.
- New prefix in its own patch: no document here requires it;
  `Documentation/devicetree/bindings/submitting-patches.rst` only asks that
  binding changes be separate from code and come first in the series.
- `Documentation/devicetree/bindings/trivial-devices.yaml` properties:
  `compatible`, `reg`, `interrupts`, `spi-max-frequency`; no supply property.
- `status` and `pinctrl-*`: a comment in
  `Documentation/devicetree/bindings/example-schema.yaml` says the tooling adds
  them to a schema automatically, so `additionalProperties: false` is not meant
  to refuse them.
- Per-class trivial lists: glob `Documentation/devicetree/bindings/` for
  `trivial-*.yaml`; a trivial RTC goes in
  `Documentation/devicetree/bindings/rtc/trivial-rtc.yaml`, which also allows
  `start-year`.
- `Documentation/devicetree/bindings/gpio/trivial-gpio.yaml`: accepts a
  two-string fallback list; `trivial-devices.yaml` accepts one string only.
- `Documentation/devicetree/bindings/incomplete-devices.yaml`: rejects every
  node that uses one of its compatibles.
  - How: it requires `broken-usage-of-incorrect-compatible`, which
    `additionalProperties: false` refuses.
  - Its `description`: such compatibles are not allowed in Devicetree sources
    "even if they come from immutable firmware".
- Purpose of `incomplete-devices.yaml`: compatibles found in drivers count as
  documented for `dt_compatible_check` in
  `Documentation/devicetree/bindings/Makefile`.
- `scripts/checkpatch.pl` documented-compatible check: a text grep over
  `Documentation/devicetree/bindings/`, so a line in `incomplete-devices.yaml`
  silences it too.
- Patch touches `incomplete-devices.yaml`: when a driver gains a compatible
  that will get no binding; one branch is for kernel unit tests and sample
  code, for example `gpio-mockup`.
- Entry in `incomplete-devices.yaml` is not a step towards a binding: a
  compatible that a DTS uses needs a real schema.
