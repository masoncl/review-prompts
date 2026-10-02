- There is no of_led_get() here; the static `fwnode_led_get()` in
  `drivers/leds/led-class.c` does the firmware lookup.
- Exported getters: `led_get()`, `devm_led_get()`, `devm_of_led_get()` and
  `devm_of_led_get_optional()`; no non-devm getter by index is exported.
- `fwnode_led_get()`: works on `dev_fwnode()` of the consumer, so
  `devm_of_led_get()` is not limited to devicetree despite its name.
- `fwnode_led_get()`: resolves the `leds` reference with
  `fwnode_find_reference()` and searches with `class_find_device_by_fwnode()`.
- `device_match_fwnode()`: compares only the LED class device's own node; the
  node of the LED's parent is not considered.
- Class device node: set only by `device_set_node()` in
  `led_classdev_register_ext()`, and only when `init_data->fwnode` is set.
- Provider registered without `init_data->fwnode`: the firmware search never
  matches and the consumer gets `-EPROBE_DEFER` on every attempt.
- `led_get()`: calls `fwnode_led_get()` first, with `con_id` looked up in the
  `led-names` property, and searches the lookup table only on `-ENOENT`.
- `led_get()` when firmware names the LED and it is not registered: returns
  `-EPROBE_DEFER` without looking at the lookup table.
- `con_id` not found in `led-names` on an OF node: the negative match result
  is used as the index, `of_fwnode_get_reference_args()` returns `-ENOENT`
  for it, and `led_get()` goes on to the lookup table.
- Lookup-table path: finds the LED with `class_find_device_by_name()` on
  `leds_class` after `leds_lookup_lock` is dropped; `leds_list_lock` is not
  taken.
- `led_get()` and `devm_led_get()`: have no optional form; a caller for which
  the LED is optional tests for `-ENOENT` itself, as
  `v4l2_subdev_get_privacy_led()` does.
