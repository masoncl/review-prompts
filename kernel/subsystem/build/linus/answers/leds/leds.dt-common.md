- `deprecated:` keyword: `Documentation/devicetree/bindings/leds/common.yaml`
  does not use it on any property.
- `label`: deprecated in its description text only ("use 'function' and
  'color' properties instead").
- `nand-disk` value of `linux,default-trigger`: marked deprecated in a YAML
  comment only, which points to `mtd`.
- `retain-state-suspended`: not in `common.yaml`; `leds-gpio.yaml` and
  `leds-lgm.yaml` declare it in their own child-node schema, and any other
  binding that wants it and closes its LED node with
  `unevaluatedProperties: false` or `additionalProperties: false` must do
  the same.
- `power-supply`: not in `common.yaml`.
- linux,default-trigger-delay-ms and flash-led-max-microamp: defined nowhere
  in this tree.
- Easy to miss in `common.yaml`: `default-intensity`, `max-brightness`,
  `default-brightness`, `active-high`, `inactive-high-impedance`.
- `allOf` in `common.yaml`: a node with `active-low` may not also have
  `active-high`.
- `additionalProperties: false` beside `$ref: common.yaml#`: used in-tree as
  a whitelist; only common properties re-listed as `name: true` are accepted.
  See `regulator-led.yaml` and the sub-LED nodes of
  `leds-pwm-multicolor.yaml`.
- `unevaluatedProperties: false` beside the `$ref`: accepts every property
  of `common.yaml`; see `leds-gpio.yaml`.
- `Documentation/devicetree/bindings/leds/backlight/common.yaml`: a separate
  schema for backlights; a relative `$ref: common.yaml#` in a file under
  `backlight/` names that one, not the LED one.
