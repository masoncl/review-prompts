- There is no simple/ directory; the Siemens Simatic IPC drivers are in
  `drivers/leds/simatic/`.
- `drivers/leds/blink/`: holds `drivers/leds/blink/leds-lgm-sso.c` and
  `drivers/leds/blink/leds-bcm63138.c`, no other driver.
- Gates: `drivers/leds/flash/`, `drivers/leds/rgb/` and
  `drivers/leds/trigger/` are gated twice, by `drivers/leds/Makefile`
  (`CONFIG_LEDS_CLASS_FLASH`, `CONFIG_LEDS_CLASS_MULTICOLOR`,
  `CONFIG_LEDS_TRIGGERS`) and by an `if` inside the subdirectory Kconfig that
  encloses its driver entries.
- `drivers/leds/blink/` and `drivers/leds/simatic/`: entered with `obj-y`; each
  driver depends on `LEDS_CLASS` or `LEDS_GPIO` by itself.
- Multicolor class drivers are not all in `drivers/leds/rgb/`: eight top-level
  files register multicolor devices, for example `drivers/leds/leds-lp50xx.c`,
  `drivers/leds/leds-cros_ec.c` and `drivers/leds/leds-pca963x.c`; search
  `drivers/leds/` for `led_classdev_multicolor_register`.
- Flash class drivers: within `drivers/leds/`, every driver that calls
  `led_classdev_flash_register` is under `drivers/leds/flash/`; top-level
  `drivers/leds/leds-lm355x.c` and `drivers/leds/leds-lm3642.c` drive flash
  chips through the plain class.
- Sort order: the "keep this sorted" comment is on the driver list in
  `drivers/leds/Makefile`; the entries of `drivers/leds/Kconfig` are not in
  alphabetical order.
