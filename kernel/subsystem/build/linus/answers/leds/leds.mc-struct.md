- `max_intensity`: is a member of `struct mc_subled` in
  `include/linux/led-class-multicolor.h`; it is the per-channel upper bound
  for `intensity`.
- `max_intensity` of 0: means "use `led_cdev.max_brightness`"; resolved at
  each use by `led_mc_get_max_intensity()` in
  `drivers/leds/led-class-multicolor.c`, not at registration.
- `max_intensity` readers: only `multi_intensity_store()` and
  `multi_max_intensity_show()`, through `led_mc_get_max_intensity()`.
- `intensity` range, as written through `multi_intensity`:
  0..`led_cdev.max_brightness` only while `max_intensity` is 0; otherwise
  0..`max_intensity`, which may be larger than `max_brightness` (see
  `uniwill_rgb_kbd_led_init()` in
  `drivers/platform/x86/uniwill/uniwill-acpi.c`).
- The two driver models that the kerneldoc of `struct mc_subled` describes
  decide which member goes to the hardware:

| Hardware | `max_intensity` | Channel register gets | Global brightness |
|---|---|---|---|
| no global brightness | 0 | `brightness`, after `led_mc_calc_color_components()` | folded into `brightness` |
| has global brightness | hardware maximum | `intensity`, unscaled | callback argument, own register |

- Second model, for example: `lp50xx_brightness_set()` in
  `drivers/leds/leds-lp50xx.c` and `ncp5623_brightness_set()` in
  `drivers/leds/rgb/leds-ncp5623.c`; `brightness` of the sub-LED is unused
  there.
- Neither model: a driver may leave `max_intensity` 0 and scale `intensity`
  itself without the helper, for example `leds_gmc_set()` in
  `drivers/leds/rgb/leds-group-multicolor.c`.
- `brightness` and `intensity` initial values: a driver may set them before
  registration, for example `drivers/leds/leds-turris-omnia.c` sets both to
  255.
