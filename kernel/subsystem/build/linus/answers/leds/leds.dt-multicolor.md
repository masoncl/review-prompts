- `$nodename` pattern in `leds-class-multicolor.yaml`:
  `^multi-led(@[0-9a-f]|-[0-9]+)?$`. That is `multi-led`, `multi-led@` plus
  one hex digit, or `multi-led-` plus decimal digits.
- `LED_COLOR_ID_RGB`: the comment in `include/dt-bindings/leds/common.h`
  defines it as an LED "that can do arbitrary color", including RGBW and
  similar; it is not limited to three-channel red/green/blue.
- Some drivers accept only `LED_COLOR_ID_RGB` on the multi-led node and fail
  probe otherwise, for example `drivers/leds/leds-sun50i-a100.c`; the class
  schema alone does not show this.
- Sub-LED nodes: `leds-class-multicolor.yaml` defines none. Each controller
  binding adds its own `patternProperties` under the multi-led node, for
  example `^led@[0-9a-f]+$` with `reg` in `leds-lp50xx.yaml` and
  `^led-[0-9a-z]+$` with `pwms` in `leds-pwm-multicolor.yaml`.
- Sub-LEDs by reference: `leds-group-multicolor.yaml` has no child nodes;
  the multi-led node lists ordinary monochrome LEDs in a `leds` phandle
  property.
- `leds_gmc_probe()` in `drivers/leds/rgb/leds-group-multicolor.c`: takes
  each sub-LED color from the referenced LED's `led_cdev->color`.
