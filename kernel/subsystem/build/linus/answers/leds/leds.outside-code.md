- `sound/core/control_led.c`: registers the `audio-mute` and `audio-micmute`
  triggers itself with `led_trigger_register_simple()` in `snd_ctl_led_init()`
  and fires them with `led_trigger_event()`; it registers no LED class device.
- There is no ledtrig-audio file under `drivers/leds/trigger/` and no
  ledtrig_audio function; only `enum led_audio` remains, in
  `include/linux/leds.h`.
- Sound class devices: `sound/hda/codecs/generic.c` and
  `sound/usb/line6/toneport.c` call `led_classdev_register()`.
- `of_phy_led()` in `drivers/net/phy/phy_device.c`: calls
  `led_classdev_register_ext()`, not the devm form; only the `struct phy_led`
  memory is devm-allocated.
- `phy_leds_unregister()`: unregisters the PHY LEDs, from `phy_remove()` and
  when `of_phy_leds()` fails part-way.
- There is no phy_leds.c; PHY class device code is all in
  `drivers/net/phy/phy_device.c`, with no `#if` around the functions (only the
  `hw_control_` assignments inside `of_phy_led()` are under
  `#ifdef CONFIG_LEDS_TRIGGERS`); its calls from `phy_probe()` and
  `phy_remove()` are guarded by `IS_ENABLED(CONFIG_PHYLIB_LEDS)`.
- `drivers/net/phy/phy_led_triggers.c`: the per-speed link triggers, built
  under `CONFIG_LED_TRIGGER_PHY`; header `include/linux/phy_led_triggers.h`.
- `drivers/usb/core/ledtrig-usbport.c`: the usbport trigger lives here, not
  under `drivers/leds/trigger/`; it uses `module_led_trigger()`.
- `drivers/ata/libata-core.c`: registers nothing; it calls
  `ledtrig_disk_activity()`, and `drivers/leds/trigger/ledtrig-disk.c` owns the
  triggers.
- `drivers/mmc/core/host.c`: registers its own trigger per host with
  `led_trigger_register_simple()`; it does not use the disk trigger.
- `drivers/block/`, `drivers/usb/` and `drivers/mfd/`: no file registers an LED
  class device; `drivers/block/` registers no trigger either.
- Finding the rest: search outside `drivers/leds/` for
  `led_classdev_register` (over 100 files, mostly `drivers/hid/`,
  `drivers/platform/x86/`, `drivers/net/wireless/`, `drivers/input/`) and for
  `led_trigger_register` (under 20 files).
- Flash class outside `drivers/leds/`: `drivers/staging/greybus/light.c` is the
  only registrant, and the only `v4l2_flash_init()` caller outside
  `drivers/leds/flash/`.
