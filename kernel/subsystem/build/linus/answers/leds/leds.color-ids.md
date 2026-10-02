- `led_colors[]` uses designated initializers (`[LED_COLOR_ID_RED] = "red"`),
  so the position of a new line in the source does not matter; a missing
  line leaves a NULL slot.
- Schema limit: `maximum: 14` on `color` in
  `Documentation/devicetree/bindings/leds/common.yaml`, which is
  `LED_COLOR_ID_MAX` minus one and must be raised with it.
- Change together when adding a color:
  - the new `LED_COLOR_ID_*` define and `LED_COLOR_ID_MAX` in
    `include/dt-bindings/leds/common.h`;
  - the `led_colors[]` entry;
  - `maximum` on `color` in `common.yaml`.
- `led_get_color_name()`: returns NULL for an id past the table.
- `led_compose_name()`: indexes `led_colors[]` with no check of its own; it
  relies on `led_parse_fwnode_props()` having set `color_present` only for
  an id below `LED_COLOR_ID_MAX`.
