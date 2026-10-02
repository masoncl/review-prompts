- Purpose, `struct led_classdev`, `struct led_trigger`, per-LED trigger data,
  the two brightness callbacks and software blink: see
  `include/linux/leds.h` and `drivers/leds/led-core.c`.
- LED to trigger: one trigger drives many LEDs, an LED has at most one
  trigger; it is not many-to-many.
- `led_cdev->trigger`: the back pointer; `led_cdev->trig_list` is the LED's
  node on `trig->led_cdevs`. `struct led_classdev` has no member named
  `trig`.
- `struct led_trigger` has no device of its own: `led_trigger_set()` adds
  `trig->groups` to the LED's class device, so a trigger's sysfs handlers
  receive the LED's `struct device`.
- `struct led_init_data`: has no color or function member; they are fwnode
  properties read into `struct led_properties` by `led_parse_fwnode_props()`
  in `drivers/leds/led-core.c`.
- Locks, by role:

| Lock | Kind | Guards |
| --- | --- | --- |
| `leds_list_lock` | rwsem | `leds_list` |
| `triggers_list_lock` | rwsem | `trigger_list` |
| `led_cdev->trigger_lock` | rwsem | which trigger the LED has; attach, detach |
| `led_cdev->led_access` | mutex | class sysfs stores, `LED_SYSFS_DISABLE` |
| `trig->leddev_list_lock` | spinlock | writers of `trig->led_cdevs` in `led_trigger_set()` |

- `led_cdev->led_access` does not serialise trigger attachment;
  `led_cdev->trigger_lock` does, and every caller of `led_trigger_set()` in
  this tree holds it for write.
- `led_trigger_register()`: binds a default trigger only to LEDs that have no
  trigger attached at that moment.
- `struct led_hw_trigger_type`: an identity token; a trigger with a non-NULL
  `trigger_type` attaches only to LEDs whose `trigger_type` is the same
  pointer.
- `trigger_relevant()` makes that check for `led_trigger_write()` and
  `led_match_default_trigger()`; `led_trigger_set()` itself makes no such
  check.
- `hw_control_trigger`: names the one trigger allowed to offload to the LED's
  hardware; core files never read it, `supports_hw_control()` in
  `drivers/leds/trigger/ledtrig-netdev.c` does.
- `led_mc_calc_color_components()`: called by the driver from its brightness
  callback, for example in `drivers/leds/leds-cros_ec.c`; no core file calls
  it, so `subled_info[].brightness` is stale unless the driver does.
- `struct v4l2_flash` in `include/media/v4l2-flash-led-class.h`: points at a
  flash LED (`fled_cdev`) or at an indicator LED (`iled_cdev`);
  `v4l2_flash_init()` sets only the first, `v4l2_flash_indicator_init()` only
  the second. `struct led_classdev_flash` holds nothing of V4L2.
- `struct led_pattern`: also the element type of the software pattern that
  `drivers/leds/trigger/ledtrig-pattern.c` plays with its own timers;
  `pattern_set` receives it only for `PATTERN_TYPE_HW`.
- Consumer reference: `class_find_device_by_fwnode()` or
  `class_find_device_by_name()` pins the class device, `led_module_get()`
  pins the module of `led_cdev->dev->parent->driver`; `led_put()` drops both.
- In-kernel consumers that take over an LED may call `led_sysfs_disable()`,
  under `led_access`, for example `v4l2_flash_open()`,
  `v4l2_subdev_get_privacy_led()` and
  `drivers/leds/rgb/leds-group-multicolor.c`.
