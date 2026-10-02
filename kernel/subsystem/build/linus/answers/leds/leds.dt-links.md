- `trigger-sources`: sits on the LED node and is defined in `common.yaml`;
  `trigger-source.yaml` defines only `#trigger-source-cells` (0 or 1) for
  the source node.
- `trigger-source.yaml`: no binding under `Documentation/devicetree/bindings`
  references it.
- `leds-consumer.yaml`: has `select: true`; `leds` may be either a child
  node or a phandle-array with one cell per entry.
- LED readers of `trigger-sources`:

| Reader | File | How it parses |
|---|---|---|
| `usbport_trig_port_observed()` | `drivers/usb/core/ledtrig-usbport.c` | `of_count_phandle_with_args()` and `of_parse_phandle_with_args()` with `#trigger-source-cells`; compares only the node, ignores the cells |
| `gpio_trig_activate()` | `drivers/leds/trigger/ledtrig-gpio.c` | `gpiod_get_optional()` with con_id `trigger-sources`; parsed as a GPIO specifier with `#gpio-cells` |

- `of_find_trigger_gpio()` in `drivers/gpio/gpiolib-of.c`: the quirk that
  lets `trigger-sources` resolve as a GPIO; it returns `-ENOENT` without
  `CONFIG_LEDS_TRIGGER_GPIO`.
- `ledtrig-usbport.c` is built by `CONFIG_USB_LEDS_TRIGGER_USBPORT` from
  `drivers/usb/core/Makefile`, not from `drivers/leds/trigger/`.
- `drivers/net/`: nothing there reads `trigger-sources`.
- Non-LED readers of the same property names: for example
  `drivers/spi/spi-offload.c` and `drivers/iio/adc/ad7768-1.c`; the bindings
  of their trigger sources are outside `leds/`, for example under
  `Documentation/devicetree/bindings/trigger-source/`.
