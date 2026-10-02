- Trigger ABI files: only `sysfs-class-led-trigger-netdev`,
  `sysfs-class-led-trigger-oneshot`, `sysfs-class-led-trigger-pattern`,
  `sysfs-class-led-trigger-tty` and `sysfs-class-led-trigger-usbport` exist
  under `Documentation/ABI/testing/`.
- Triggers with sysfs files and no ABI file: for example timer (`delay_on`,
  `delay_off`), transient (`activate`, `duration`, `state`), heartbeat and
  activity (`invert`), gpio (`desired_brightness`); the code in
  `drivers/leds/trigger/` is the authority.
- Transient trigger: documented only as prose, in
  `Documentation/leds/ledtrig-transient.rst`.
- `inverted`: documented in `Documentation/ABI/testing/sysfs-class-led`, which
  says gpio and backlight triggers; only
  `drivers/leds/trigger/ledtrig-backlight.c` creates it.
- `Documentation/leds/leds-class.rst`, section "Hardware accelerated blink of
  LEDs": tells the reader to stop blinking with led_brightness_set(), which is
  defined nowhere; the function is `led_set_brightness()`.
- `led_brightness_set` in this tree is only a callback member of
  `struct phy_driver` in `include/linux/phy.h`.
- `Documentation/leds/leds-class-flash.rst`: says `v4l2_flash_init()` takes six
  arguments including of_node and iled_cdev; in
  `include/media/v4l2-flash-led-class.h` it takes five, with `fwn`, and the
  indicator LED goes through `v4l2_flash_indicator_init()`.
- `Documentation/leds/leds-class-flash.rst` example driver: the file is at
  `drivers/leds/flash/leds-max77693.c`, not the path the document gives.
