- `include/dt-bindings/leds/common.h` does not define `LED_ON`, `LED_OFF` or
  any default-state value; besides colors and functions it holds only
  `LEDS_TRIG_TYPE_EDGE`, `LEDS_TRIG_TYPE_LEVEL` and the three boost modes
  that start at `LEDS_BOOST_OFF`.
- `LED_ON` and `LED_OFF`: `enum led_brightness` in `include/linux/leds.h`,
  kernel-only.
- `default-state`: a string in DT (`on`, `off`, `keep`);
  `led_init_default_state_get()` in `drivers/leds/led-core.c` maps it to
  `enum led_default_state`.
- No `LED_FUNCTION_*` macro in the header is marked obsolete; the "Obsolete"
  comments quote old LED names that the macro below them replaces.
- `color` with no fitting constant: its description in `common.yaml` says the
  same as for `function`, add a new `LED_COLOR_ID_*` to the header.
- `function` is not checked against the header: `common.yaml` gives it no
  `enum`, and `led_parse_fwnode_props()` takes any string.
- `color` is checked: `maximum: 14` in `common.yaml`, and
  `led_parse_fwnode_props()` logs an error and drops a value that is
  `>= LED_COLOR_ID_MAX` from the name.
