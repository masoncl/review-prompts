| Group | Built by | Stub when off |
|---|---|---|
| class registration, suspend, resume, lookup (`led_classdev_register_ext()`, `led_classdev_suspend()`, `led_get()`, `devm_of_led_get()`) | `CONFIG_LEDS_CLASS`, `drivers/leds/led-class.c` | none |
| brightness, blink, naming (`led_set_brightness()`, `led_blink_set()`, `led_compose_name()`) | `CONFIG_NEW_LEDS`, `drivers/leds/led-core.c` | none |
| `include/linux/led-class-multicolor.h`, `include/linux/led-class-flash.h` | their class symbol | none; no conditional in either header |
| trigger consumer (`led_trigger_event()`, `led_mc_trigger_event()`, `led_trigger_set()`, `led_trigger_get_brightness()`) | `CONFIG_LEDS_TRIGGERS` | yes |
| trigger registration (`led_trigger_register()`, `devm_led_trigger_register()`, `module_led_trigger()`, `led_trigger_get_drvdata()`) | `CONFIG_LEDS_TRIGGERS` | none |
| per-trigger hooks (`ledtrig_disk_activity()`, `ledtrig_cpu()`) | each trigger's symbol | yes |

- `led_classdev_register()` and `devm_led_classdev_register()`: inline wrappers
  around functions with no stub, so they do not link without the class.
- `led-core.c` functions: link from built-in code whenever `NEW_LEDS=y`, also
  with `LEDS_CLASS=m` or `=n`.
- `led_trigger_register_simple()` stub: `void` with an empty body; it does not
  write `*trigger`, so the pointer keeps whatever the caller put there.
- `led_set_trigger_data()` stub: takes one parameter; a two-argument call
  compiles only with `CONFIG_LEDS_TRIGGERS`.
- `struct led_classdev` under `CONFIG_LEDS_TRIGGERS`: also holds `trigger_type`
  and every `hw_control_` member; the struct itself is always defined.
- Assigning a `hw_control_` member: needs `#ifdef CONFIG_LEDS_TRIGGERS` even in
  code the compiler drops, as `of_phy_led()` in `drivers/net/phy/phy_device.c`
  does.
- Without `#ifdef`: the option depends on `LEDS_TRIGGERS`, as
  `NET_DSA_QCA8K_LEDS_SUPPORT` does.
- Per-trigger hook guards differ: `ledtrig_flash_ctrl()` and
  `ledtrig_torch_ctrl()` get real prototypes at `=m` too;
  `ledtrig_backlight_blank()` uses `IS_REACHABLE()`.
- Code that fills in `struct led_trigger` or calls `led_trigger_register()`: built
  only under `CONFIG_LEDS_TRIGGERS`, as `power_supply_leds.o` in
  `drivers/power/supply/Makefile` is.
- **Unsafe usage**: guarding class calls with `IS_ENABLED(CONFIG_LEDS_CLASS)` in
  code that can be built in while `LEDS_CLASS=m`; it is true at `LEDS_CLASS=m`
  and the link fails.
  - Safe: `#if IS_REACHABLE(CONFIG_LEDS_CLASS)`, as `sdhci_led_register()` in
    `drivers/mmc/host/sdhci.c`; the LED is dropped when the class is a module
    and the caller is built in.
  - Safe: `#ifdef CONFIG_LEDS_CLASS`, as `cap11xx_init_leds()` in
    `drivers/input/keyboard/cap11xx.c`; it is true only at `=y`.
  - Safe: `IS_ENABLED()` of the caller's own bool whose Kconfig excludes the
    combination, as `IS_ENABLED(CONFIG_PHYLIB_LEDS)` in
    `drivers/net/phy/phy_device.c`.
  - Safe: `IS_ENABLED(CONFIG_LEDS_CLASS)` around a struct member only, as in
    `struct sdhci_host` in `drivers/mmc/host/sdhci.h`.
