# LED Subsystem

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

- `drivers/leds/leds.h`: holds only inline `led_get_brightness()`, the
  prototypes of `led_init_core()`, `led_stop_software_blink()`,
  `led_set_brightness_nopm()`, `led_set_brightness_nosleep()`,
  `led_trigger_read()`, `led_trigger_write()`, and the externs `leds_list_lock`
  and `leds_list`.
- `led_init_default_state_get()`, `led_update_brightness()`,
  `led_compose_name()`, `led_trigger_set()`, `led_trigger_remove()`: declared
  in `include/linux/leds.h`, not in `drivers/leds/leds.h`.
- `trigger_list` and `triggers_list_lock`: `static` in
  `drivers/leds/led-triggers.c`; no header declares them.
- `led_colors[]`: `static` in `drivers/leds/led-core.c`; other files reach it
  through `led_get_color_name()`.
- `drivers/leds/leds.h` users: `drivers/leds/led-class.c`,
  `drivers/leds/led-core.c`, `drivers/leds/led-triggers.c`,
  `drivers/leds/leds-ns2.c` and most files in `drivers/leds/trigger/`; no file
  outside `drivers/leds/` includes it.
- Every symbol `drivers/leds/leds.h` declares is `EXPORT_SYMBOL_GPL()`, so a
  modular trigger can call it.

**LED code elsewhere**

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

**Driver directories**

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

**Authoritative documentation**

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

**Tests and tools**

- `drivers/leds/led-test.c`: KUnit suite named `led`, two cases,
  `led_test_class_register()` and `led_test_class_add_lookup_and_get()`.
- `led_test_class_register()` checks: `max_brightness` defaults to `LED_FULL`;
  `brightness` is read back from `brightness_get` at registration; a duplicate
  name registers as `led-test_1` while `cdev->name` stays `led-test`; with
  `LED_REJECT_NAME_CONFLICT` the duplicate fails with `-EEXIST`.
- `led_test_class_add_lookup_and_get()` checks: `led_add_lookup()`, then
  `devm_led_get()` by `con_id`, then `led_remove_lookup()`.
- Not covered: brightness clamping, triggers, blink, the multicolor and flash
  classes, sysfs files, suspend and resume.
- `CONFIG_LEDS_KUNIT_TEST`: tristate, `depends on KUNIT && LEDS_CLASS`,
  `default KUNIT_ALL_TESTS`.
- `drivers/leds/.kunitconfig` exists; run with
  `tools/testing/kunit/kunit.py run --kunitconfig drivers/leds`.
- `tools/leds/Makefile`: builds only `uledmon` and `led_hw_brightness_mon`,
  with `-I../../include/uapi` so they use this tree's
  `include/uapi/linux/uleds.h`; `make -C tools leds` also works.
- `tools/leds/get_led_device_info.sh`: a script, not built; it prints the
  parent device details of an LED and validates the LED name against
  `include/dt-bindings/leds/common.h`, found relative to the script or given as
  a second argument.
- `led_hw_brightness_mon`: the file it polls exists only with
  `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED` and `LED_BRIGHT_HW_CHANGED` set in the
  LED's `flags`.
- `tools/testing/selftests/`: has no LED directory.

## Kconfig and header stubs

**Configuration symbols**

- `CONFIG_LEDS_TRIGGERS`: a `menuconfig` in `drivers/leds/trigger/Kconfig`,
  sourced from `drivers/leds/Kconfig` inside `if NEW_LEDS`.
- `led-triggers.o`: its own object in `drivers/leds/Makefile`, not part of
  `led-class.o`; always built in, also when `LEDS_CLASS=m`.
- `led-triggers.o` and `led-core.o`: reference no symbol of
  `drivers/leds/led-class.c`, so both link built in while the class is a module.
- Optional LED: no Kconfig file in this tree uses `LEDS_CLASS || !LEDS_CLASS` or
  `LEDS_CLASS || LEDS_CLASS=n`, for the class, multicolor or flash symbols.
- Optional LED, forms this tree uses, for example: a bool sub-option with
  `depends on LEDS_CLASS=y || LEDS_CLASS=<TRISTATE>` (`PHYLIB_LEDS`,
  `MAC80211_LEDS`), or `depends on !(R8169=y && LEDS_CLASS=m)` (`R8169_LEDS`).
- `select LEDS_CLASS_MULTICOLOR` from outside: goes with `select NEW_LEDS` and
  `select LEDS_CLASS`, as `HID_MSI` in `drivers/hid/Kconfig` does.
- **Potentially unsafe usage**: a bool option with plain
  `depends on LEDS_CLASS`.
  - Unsafe: when its code calls a function of `drivers/leds/led-class.c`, for
    example `led_classdev_register_ext()`, and can be built in; Kconfig allows
    the bool at `y` with `LEDS_CLASS=m`, and the link fails.
  - Safe: when its code calls only `drivers/leds/led-triggers.c` and
    `drivers/leds/led-core.c` functions, as `BT_LEDS` with
    `net/bluetooth/leds.c` does; with `select LEDS_TRIGGERS` both objects are
    built in.
  - Safe: `depends on LEDS_CLASS=y`, as `PCI_NPEM` in `drivers/pci/Kconfig`.
  - Safe: `depends on LEDS_CLASS=y || LEDS_CLASS=<TRISTATE>`, where the tristate
    is the module the code is linked into, as `NET_DSA_QCA8K_LEDS_SUPPORT`.

**Stubs when configured out**

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

## Class device state

**Flags word**

- Lower half: holds only `LED_SUSPENDED` and `LED_UNREGISTERING`. Only
  `drivers/leds/led-class.c` writes them; drivers read them.
- Upper half (`LED_CORE_SUSPENDRESUME` to `LED_MULTI_COLOR`): not all
  driver-chosen. The core or an LED consumer writes these:

| Flag | Written by | Tested by |
|---|---|---|
| `LED_SYSFS_DISABLE` | `led_sysfs_disable()`, `led_sysfs_enable()`, called by LED consumers such as `drivers/video/backlight/led_bl.c` | only handlers that call `led_sysfs_is_disabled()` |
| `LED_INIT_DEFAULT_TRIGGER` | set by `led_match_default_trigger()`; cleared by `led_trigger_set()` when it removes a trigger, and by the activate of the timer, oneshot and pattern triggers | those three activates; `cht_wc_leds_blink_set()` |
| `LED_MULTI_COLOR` | `led_classdev_multicolor_register_ext()` | `led_mc_set_brightness()` logs once and returns; `led_mc_trigger_event()` skips the LED |
| `LED_RETAIN_AT_SHUTDOWN` | driver, or `led_classdev_register_ext()` from `retain-state-shutdown` | `led_classdev_unregister()` |

- `LED_SYSFS_DISABLE` scope: `brightness_store()`, `led_trigger_write()` and
  the three stores in `drivers/leds/led-class-flash.c` return `-EBUSY`; an
  attribute whose handler does not call `led_sysfs_is_disabled()` stays
  writable.
- `LED_BRIGHT_HW_CHANGED`: tested in `led_classdev_register_ext()` and again
  in `led_classdev_unregister()`.
  `led_classdev_notify_brightness_hw_changed()` tests
  `brightness_hw_changed_kn`, not the flag.
- Locks when `flags` is written after registration:

| Bit | Lock held |
|---|---|
| `LED_SUSPENDED`, `LED_UNREGISTERING` | none taken by the LED core |
| `LED_SYSFS_DISABLE` | `led_access`, by `lockdep_assert_held()` |
| `LED_INIT_DEFAULT_TRIGGER` | `trigger_lock` for write, taken by the callers of `led_match_default_trigger()` and `led_trigger_set()` |

- The locks differ per bit and every write is a plain `|=` or `&=` on the
  same `int`, so no lock excludes two writers of different bits.

**Work flags**

- Not private to `drivers/leds/led-core.c`:
  `drivers/leds/trigger/ledtrig-heartbeat.c` and
  `drivers/leds/trigger/ledtrig-activity.c` set `LED_BLINK_SW` in activate,
  clear it in deactivate, and consume `LED_BLINK_BRIGHTNESS_CHANGE` in their
  own timer functions.
- `multi_intensity_store()` in `drivers/leds/led-class-multicolor.c` reads
  `LED_BLINK_SW`.
- No file outside `drivers/leds/` touches `work_flags` of
  `struct led_classdev`.
- `LED_BLINK_SW` set: does not mean `blink_timer` is armed; the two triggers
  above run their own timers.
- `LED_BLINK_SW` in the core: set only in `led_set_software_blink()`; cleared
  in `led_stop_software_blink()`, `led_blink_set()` and
  `led_timer_function()`.
- `led_stop_software_blink()`: clears `LED_BLINK_SW` only.
  `LED_BLINK_ONESHOT` is cleared only by `led_blink_set()`.
- `LED_BLINK_ONESHOT` set, which only `led_blink_set_oneshot()` does:
  `led_blink_setup()` skips the driver's `blink_set` and uses software blink.
- `LED_SET_BLINK`: set by `led_blink_set_nosleep()` when the driver has both
  `blink_set` and `brightness_set_blocking`; `set_brightness_delayed()` then
  calls `led_blink_set()`.
- `led_set_brightness_nopm()` deferring 0: clears pending `LED_SET_BRIGHTNESS`
  and `LED_SET_BLINK` before it sets `LED_SET_BRIGHTNESS_OFF`.
- `LED_SET_BRIGHTNESS` setters besides `led_set_brightness_nopm()`:
  `led_set_brightness()` with a non-zero value when a set or a blink disable
  is already pending, and `set_brightness_delayed()` after the off step when
  `delayed_set_value` is not `LED_OFF`.
- One non-atomic write: `led_classdev_register_ext()` stores
  `work_flags = 0`.

**Cached brightness value**

- `led_classdev_notify_brightness_hw_changed()`: writes
  `brightness_hw_changed`, never `brightness`.
- Drivers write `brightness` at run time too; for example
  `aat1290_led_flash_strobe_set()` zeroes it under the driver's own mutex.
- `led_access`: held by some callers of the three core writers
  (`led_set_brightness_nosleep()`, `led_set_brightness_sync()`,
  `led_update_brightness()`), for example `brightness_store()`,
  `brightness_show()` and `led_classdev_register_ext()`;
  `led_trigger_event()` and `led_timer_function()` do not take it, so it does
  not serialise writes to the field.
- `led_set_brightness()` returns without writing `brightness` when:
  - the value is non-zero and `LED_SET_BRIGHTNESS` or `LED_BLINK_DISABLE` is
    pending: the value goes to `delayed_set_value`;
  - the value is non-zero and `LED_BLINK_SW` is set: the value goes to
    `new_blink_brightness`;
  - the value is 0 and `LED_BLINK_SW` is set: `LED_BLINK_DISABLE` is queued.
- `set_brightness_delayed()`: its `LED_SET_BRIGHTNESS_OFF` and
  `LED_SET_BRIGHTNESS` steps call the driver and do not write `brightness`.
  After the first and third case above the hardware has the new value and the
  field keeps the old one.
- `led_update_brightness()`: stores the `brightness_get` result without
  limiting it to `max_brightness`; `led_classdev_register_ext()` calls it, so
  a driver's initial value is overwritten when `brightness_get` exists and
  returns no error.
- `led_classdev_suspend()`: turns the hardware off through
  `led_set_brightness_nopm()`, which does not write the field;
  `led_classdev_resume()` passes the field back to the same function.
- While `LED_SUSPENDED` is set: `led_set_brightness_nosleep()` and
  `led_set_brightness_sync()` write the field and skip the driver.

**Maximum brightness**

- Default: `led_classdev_register_ext()` sets `LED_FULL` when the field is
  zero; `led_init_core()` does not touch it.
- `max-brightness` fwnode property: read in `led_classdev_register_ext()`
  before the zero test, and only when `init_data` and `init_data->fwnode` are
  both set; `led_classdev_register()` passes no `init_data`.
- The property value replaces the driver's value with no comparison, so it
  can be larger than what the driver set.
- No other input: `max-brightness` is the only property that
  `led_classdev_register_ext()` reads into the field.
- Limit: the core limits a brightness to `max_brightness` in two places
  only, the `min()` in `led_set_brightness_nosleep()` and the `min()` in
  `led_set_brightness_sync()`.
- `brightness_store()`: neither rejects nor limits; it passes the parsed
  value to `led_set_brightness()`.
- `led_set_brightness()` with a non-zero value while `LED_SET_BRIGHTNESS` or
  `LED_BLINK_DISABLE` is pending: the value reaches the driver callback from
  `set_brightness_delayed()` without passing either `min()`.

**Brightness type and constants**

- Driver callbacks: `brightness_set` and `brightness_set_blocking` take
  `enum led_brightness`; `brightness_get` returns it. The core set functions,
  for example `led_set_brightness()`, take `unsigned int`.
- Trigger API is still enum-typed: `led_trigger_event()`,
  `led_mc_trigger_event()`, the `brightness` member of `struct led_trigger`,
  `led_trigger_get_brightness()`; also `led_mc_calc_color_components()`.
- `led_classdev_notify_brightness_hw_changed()`: takes `unsigned int`; its
  stub without `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED` takes
  `enum led_brightness`.
- Values above `LED_FULL` pass through the enum-typed parameters:
  `max_brightness` can exceed 255, for example `0xfff` in
  `drivers/leds/leds-dac124s085.c`.
- `enum led_brightness` status: marked only by the comment "obsolete/useless"
  above its definition; no attribute or build check enforces anything.
- `drivers/leds/TODO`: says "Get rid of it, or make it into typedef or
  something"; it names no replacement type.
- `LED_FULL` in the core: still the default `max_brightness`, and triggers
  pass it to mean "on", for example `led_panic_blink()`.
- `LED_FULL` through `led_set_brightness()`: limited to `max_brightness` when
  that is below 255; when it is above 255 the LED gets 255, not full.
- `defon_trig_activate()` in `drivers/leds/trigger/ledtrig-default-on.c`:
  passes `led_cdev->max_brightness` to `led_set_brightness_nosleep()`; it does
  not call `led_trigger_event()`.

## Sysfs interface

**Class sysfs attributes**

- `trigger`: created only with `CONFIG_LEDS_TRIGGERS`; a binary attribute
  handled by `led_trigger_read()` and `led_trigger_write()` in
  `drivers/leds/led-triggers.c`; `drivers/leds/` defines no `trigger_show()`
  or `trigger_store()`, and `led_trigger_group` is defined in
  `drivers/leds/led-class.c`.
- `brightness_show()`: with `CONFIG_LEDS_TRIGGERS`, takes
  `led_cdev->trigger_lock` for read inside `led_trigger_is_hw_controlled()`,
  drops it, then takes `led_access` around `led_update_brightness()`.
- `brightness_show()` with a trigger attached whose `trigger_type` is set
  (an LED-private trigger): returns `-ENODATA` and never calls
  `brightness_get`.
- `brightness_store()` and `led_trigger_write()` with `LED_SYSFS_DISABLE` set:
  return `-EBUSY`, tested under `led_access` before the input is parsed.
- `led_trigger_write()` with "none" or "default": goes through
  `led_trigger_remove()` or `led_trigger_set_default()`, still under
  `led_access`; only a named trigger takes `triggers_list_lock` in
  `led_trigger_write()` itself.
- Write of 0 to `brightness`: calls `led_trigger_remove()` for any attached
  trigger; a non-zero write never touches the trigger.
- Write of 0 with a trigger attached: `led_trigger_set()` stops the software
  blink synchronously (`cancel_work_sync()`, `led_stop_software_blink()`,
  then the trigger's `deactivate`) before `led_set_brightness()` runs.
- Write of 0 with no trigger attached and `LED_BLINK_SW` set (blink started
  by `led_blink_set()` from kernel code): `led_set_brightness()` sets
  `LED_BLINK_DISABLE` and queues `set_brightness_work`; the blink stops in
  the work item.
- `brightness_store()`: does not call `led_stop_software_blink()` itself
  (only through `led_trigger_remove()`) and does not call `flush_work()`;
  with a `brightness_set_blocking` driver the write can return before the
  hardware has changed.
- Hardware blink (driver `blink_set` succeeded): `LED_BLINK_SW` is not set, so
  `led_set_brightness()` passes every value to the driver; stopping the blink
  on 0 is the driver's job, see the comment at `blink_set` in
  `include/linux/leds.h`.
- Without `CONFIG_LEDS_TRIGGERS`: `led_trigger_remove()` is an empty inline in
  `include/linux/leds.h`.

**Hardware brightness changes**

- `led_classdev_notify_brightness_hw_changed()`: stores the value and calls
  `sysfs_notify_dirent()` on the cached node; it sends no uevent and does not
  touch the kobject.
- Calling context of `led_classdev_notify_brightness_hw_changed()`: nothing
  in it sleeps; `kernfs_notify()` in `fs/kernfs/file.c` takes its lock with
  `spin_lock_irqsave()` and defers the rest with `schedule_work()`.
- `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED`: no Kconfig entry in this tree selects
  or depends on it; a driver that sets the flag and calls the function builds
  either way, and with the symbol off there is silently no attribute.
- `brightness_hw_changed_show()`: returns `-ENODATA` only while the field is
  exactly -1, the value `led_classdev_register_ext()` stores.
- `thinkpad_acpi.c` is at `drivers/platform/x86/lenovo/thinkpad_acpi.c`.
- **Unsafe usage**: calling
  `led_classdev_notify_brightness_hw_changed()` on an LED registered without
  `LED_BRIGHT_HW_CHANGED`.
  - Unsafe: when the `struct led_classdev` was not zero-initialised; the only
    guard is `WARN_ON(!led_cdev->brightness_hw_changed_kn)`, and
    registration writes that field only when the flag is set.
  - Unsafe: on a zeroed structure the call warns and returns without
    notifying.
  - Safe: flag set before registration, as `t14s_kbd_backlight_probe()` in
    `drivers/platform/arm64/lenovo-thinkpad-t14s.c` does.
- **Unsafe usage**: an event source that can call
  `led_classdev_notify_brightness_hw_changed()` after
  `led_classdev_unregister()`.
  - Unsafe: `led_remove_brightness_hw_changed()` drops the node reference with
    `sysfs_put()` and leaves `brightness_hw_changed_kn` set, so the
    `WARN_ON()` does not fire and `sysfs_notify_dirent()` gets a stale node.
  - Safe: event source released before the LED, as in `t14s_ec_probe()`:
    `devm_led_classdev_register()` runs before
    `devm_request_threaded_irq()`, so devres frees the interrupt first.
  - Safe: the same order also covers the start: the LED is registered before
    the interrupt can fire.

**Driver sysfs attributes**

- `groups` with `led_classdev_multicolor_register_ext()`: overwritten
  unconditionally with the multicolor groups; a value the driver set is lost
  silently.
- Attributes added after registration: not forbidden; the core does it for
  `brightness_hw_changed` and for trigger `groups`, and multicolor drivers
  must, for example `devm_device_add_group()` on `led_cdev.dev` in
  `drivers/hid/hid-lenovo-go-s.c`.
- Files added after registration: appear after the `KOBJ_ADD` uevent sent by
  `device_add()`; files from `groups` exist before it.
- `groups` array lifetime: `device_create_with_groups()` stores the pointer
  and `device_remove_attrs()` reads it at unregistration, so the array must
  stay valid until `led_classdev_unregister()` returns.
- Attribute names: share one directory with the class attributes and with the
  `groups` of whichever trigger is attached; a clash with a trigger attribute
  makes `device_add_groups()` fail in `led_trigger_set()`, and the trigger is
  not attached.
- `led_access` and `LED_SYSFS_DISABLE`: the core applies neither to driver
  handlers; a handler that must respect them takes `led_access` and tests
  `led_sysfs_is_disabled()` itself, as `flash_strobe_store()` in
  `drivers/leds/led-class-flash.c` does.
- **Potentially unsafe usage**: a handler of an attribute in
  `led_cdev->groups` that runs without `led_access`.
  - Unsafe: when it calls a core function that uses `set_brightness_work`,
    `blink_timer` or `led_cdev->wq`, for example `led_set_brightness()` on an
    LED with only `brightness_set_blocking`; `led_classdev_register_ext()`
    sets these up after `device_create_with_groups()` has made the files
    visible.
  - Safe: the handler takes `led_access` first, as `flash_brightness_store()`
    does; `led_classdev_register_ext()` holds `led_access` from before the
    device is created until registration is complete.
  - Safe: the handler reads only driver data that was set before the register
    call, as `ns2_led_sata_show()` in `drivers/leds/leds-ns2.c` does.

## Registering an LED

**Registration steps**

- `led_access`: the lock held, from just before
  `device_create_with_groups()` until after `led_trigger_set_default()`.
- `leds_list_lock`: write-held only around the `list_add_tail()` onto
  `leds_list`, not across the default-trigger step.
- Order after device creation in `led_classdev_register_ext()`:
  1. `device_set_node()`, when `init_data->fwnode` is set
  2. `led_add_brightness_hw_changed()`, when `LED_BRIGHT_HW_CHANGED` is set
  3. `work_flags = 0`, `init_rwsem()` on `trigger_lock` (under
     `CONFIG_LEDS_TRIGGERS`), `brightness_hw_changed = -1` (under
     `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED`)
  4. `max_brightness` default
  5. `led_update_brightness()`
  6. `wq = leds_wq`, `led_init_core()`
  7. list add
  8. `led_trigger_set_default()`
- List add comes after `led_init_core()`: a trigger attaching from another
  task through `led_trigger_register()` can reach the LED only after
  `brightness_get()` has run and the work item and timer exist.
- `led_trigger_register()` attach: takes `trigger_lock`, not `led_access`, so
  it can run between the list add and the unlock at the end.
- `max_brightness_show()`: takes `led_access`, so it blocks until
  registration ends, like `brightness_store()`.
- Handlers that do not wait for `led_access`: `led_trigger_read()`,
  `brightness_hw_changed_show()`, and the `led_trigger_is_hw_controlled()`
  test at the top of `brightness_show()`.
- `led_trigger_set_default()` call: compiled only under
  `CONFIG_LEDS_TRIGGERS`; it returns at once when `default_trigger` is NULL.

**Properties the core reads**

- Read in `led_classdev_register_ext()` when `init_data->fwnode` is set:

  | Property | Effect |
  |---|---|
  | `linux,default-trigger` | replaces `led_cdev->default_trigger` |
  | `retain-state-shutdown` | sets `LED_RETAIN_AT_SHUTDOWN` |
  | `max-brightness` | replaces `led_cdev->max_brightness` |
  | `color` | replaces `led_cdev->color` |

- `led_cdev->color` at or above `LED_COLOR_ID_MAX`: `dev_warn()` only;
  registration continues and the value stays.
- `retain-state-suspended` and `panic-indicator`: not read by the core;
  drivers read them, for example `gpio_leds_create()` in
  `drivers/leds/leds-gpio.c`.
- `led-pattern`: read by `led_get_default_pattern()` in
  `drivers/leds/led-core.c` from the LED class device's node; triggers call
  it from `activate()` while `LED_INIT_DEFAULT_TRIGGER` is set, for example
  `timer_trig_activate()`.
- `trigger-sources`: read by triggers from the LED class device, for example
  `gpio_trig_activate()` and `usbport_trig_port_observed()`; neither core
  registration nor the LED driver parses it.
- `default-brightness`: within `drivers/leds` only
  `led_pwm_default_brightness_get()` in `drivers/leds/leds-pwm.c` reads it,
  for `LEDS_DEFSTATE_ON`.

**Name composition**

- Precedence in `led_compose_name()`, first match wins:

  | Source | Name |
  |---|---|
  | `label` | `label`, or `devicename:label` if `devicename` set |
  | `function` or valid `color` | `color:function`, `-N` appended when `function-enumerator` was read |
  | `init_data->default_label` | `devicename:default_label` |
  | OF node | node name |
  | software node | `fwnode_get_name()` |

- `function-enumerator`: read only when `function` is present.
- `function`/`color` row: the colon is always printed, a missing part is
  empty; `devicename:` is prepended only with `devname_mandatory`.
- Output: `snprintf()` into the caller's buffer of `LED_MAX_NAME_SIZE`;
  nothing is allocated.
- Too long: `-E2BIG`, for the final name and for the intermediate
  `color:function` string; the name is never silently truncated here.
- `-EINVAL` cases:
  - NULL output buffer;
  - `default_label` reached with NULL `devicename`;
  - no source and the node is neither OF nor software node, including a
    NULL `fwnode`.
- `devname_mandatory` without `devicename`: checked only in
  `led_classdev_register_ext()`; `led_compose_name()` itself has no such
  test, and it is exported and called directly by
  `pci_npem_set_led_classdev()` in `drivers/pci/npem.c`.

**Name after registration**

- Registered name: lives only in the class device
  (`dev_name(led_cdev->dev)`); `led_cdev->name` is just the proposed name
  when no `struct led_init_data` is passed.
- `led_cdev->name`: never written by the core; the composed and final names
  are stack buffers in `led_classdev_register_ext()`.
- `led_classdev_next_name()`: returns `-ENOMEM` when the suffixed name does
  not fit `LED_MAX_NAME_SIZE`, and registration fails with it.
- `led_cdev->name` of `LED_MAX_NAME_SIZE` characters or more, registered
  without `init_data`: the sysfs name is silently truncated by the
  `strscpy()` in `led_classdev_next_name()`, so it differs from
  `led_cdev->name`.

**Naming rules**

- `devicename`: in `Documentation/leds/leds-class.rst`, a unique identifier
  created by the kernel, such as phyN or inputN, not the hardware, product or
  vendor; vendor and product names are called deprecated.
- Sections that do not apply are left blank; the examples include
  `":kbd_backlight"` and `"input5::kbd_backlight"`.
- Keyboard with one brightness/colour setting: one (multicolor) LED class
  device, function part `kbd_backlight`, name must end with
  `:kbd_backlight`; the text sets no rule on the devicename or colour part.
- Keyboard with several zones: one LED class device per zone, named
  `<devicename>:<color>:kbd_zoned_backlight-<zone_name>`.
- `<devicename>`: must be the same for all zones of one keyboard.
- `<zone_name>`: descriptive of the part of the keyboard the zone covers and
  fit to show to a user; reuse values of similar keyboards, such as right,
  middle, left, corners, wasd, main, cursor, numpad.
- Exception: one big zone plus small extra areas; the big zone uses
  `kbd_backlight`, the small ones the zoned form.
- Per-key addressable backlights: must not use LED class devices.
- `include/dt-bindings/leds/common.h`: has `LED_FUNCTION_KBD_BACKLIGHT`; it
  has no define for the zoned function, and no code in this tree uses the
  zoned string.

**Shape of a small driver**

- Iteration: both `gpio_leds_create()` and `led_pwm_create_fwnode()` use
  `device_for_each_child_node_scoped()`; neither calls
  `fwnode_handle_put()`, and early `return` inside the loop is correct.
- No child nodes: `gpio_leds_create()` returns `-ENODEV`, `led_pwm_probe()`
  returns `-EINVAL`.
- `led_pwm_create_fwnode()`: returns `-EINVAL` for a child with neither
  `label` nor an OF node.
- `led_pwm_add()`: sets `cdev.name` to that label or node name and also
  passes `init_data` with the node, so the sysfs name comes from
  `led_compose_name()` and can differ from `cdev.name`.
- `led_pwm_add()` with `LEDS_DEFSTATE_KEEP`: reads `pwm_get_state()`; a
  period of 0 turns the state into `LEDS_DEFSTATE_OFF` and uses
  `pwm_init_state()`.
- `create_gpio_led()` after registering: calls
  `devm_pinctrl_get_select_default()` on the LED class device, which works
  through the node the core set; an error other than `-ENODEV` fails probe.
- `platform_set_drvdata()`: both drivers call it after all LEDs are
  registered; the callbacks reach their data with `container_of()`.

**Readiness before registration**

- **Potentially unsafe usage**: doing probe work after the register call.
  - Unsafe: when the work sets up something that a `struct led_classdev`
    callback, or a handler of an attribute in `led_cdev->groups`,
    dereferences. `led_update_brightness()` calls `brightness_get()` inside
    registration; `led_trigger_set_default()` runs `activate()` inside it;
    `led_trigger_register()` can do the same from another task once the LED
    is on `leds_list`.
  - Safe: work that no callback or handler depends on, such as
    `platform_set_drvdata()` at the end of `gpio_led_probe()`; the callbacks
    use `cdev_to_gpio_led_data()` and only `gpio_led_shutdown()` reads the
    drvdata.
  - Safe: work that needs the registered device, such as
    `gpiod_set_consumer_name()` in `gpio_leds_create()`, which needs the
    final name.
- Driver sets no `default_trigger` and passes `init_data->fwnode`: firmware
  can supply one through `linux,default-trigger`, so activation during
  registration cannot be ruled out from the driver source.
- `max_brightness`: firmware `max-brightness` replaces the driver's value
  before any callback runs; callbacks that scale by it see that value.
- `led_cdev->groups` handlers: exist from `device_create_with_groups()`,
  before `brightness_get()` runs, and are not held back by `led_access`
  unless the handler takes it itself.
- `brightness_get()` returning an error during registration: ignored;
  `led_cdev->brightness` keeps what the driver set and registration
  succeeds.
- `LED_BRIGHT_HW_CHANGED` and `LED_REJECT_NAME_CONFLICT`: acted on inside
  `led_classdev_register_ext()`; set afterwards, no attribute is created and
  no name is rejected. `led_classdev_unregister()` tests
  `LED_BRIGHT_HW_CHANGED` again.

**Child node references**

- `device_set_node()` in `led_classdev_register_ext()`: stores the pointer
  and takes no reference on the node.
- Node pointer after registration: stays in `led_cdev->dev` and is read
  later, for example by `led_get_default_pattern()` when a default trigger
  activates, by `fwnode_led_get()`, by `usbport_trig_port_observed()` and by
  `gpio_trig_activate()`.
- Trigger activation can happen at `led_trigger_register()` time, long
  after probe has returned and the iterator has put the child.
- **Unsafe usage**: saving the child pointer inside the loop without
  `fwnode_handle_get()` and passing it as `init_data->fwnode` after the
  loop; `fwnode_get_next_child_node()` has put that child by then.
  - Safe: register inside the body of
    `device_for_each_child_node_scoped()`, as `gpio_leds_create()` does; the
    iterator's reference covers the whole register call.
  - Safe: take `fwnode_handle_get()` in the loop and put it from a devm
    action that was added before the LEDs are registered, as
    `is31fl319x_parse_fw()` does with `is31_free_fwnode()`; devres releases
    in reverse order, so the put runs after the LEDs are unregistered.
- `of_node_get()` and `of_node_put()`: inlines that count nothing in
  `include/linux/of.h` without `CONFIG_OF_DYNAMIC`, so a missing or extra
  reference on an OF node shows no symptom in such a build.

## Removing an LED

**Unregistration steps**

- Order in `led_classdev_unregister()` (`drivers/leds/led-class.c`):
  1. return if `IS_ERR_OR_NULL(led_cdev->dev)`
  2. with `CONFIG_LEDS_TRIGGERS`: `led_trigger_set(led_cdev, NULL)` under
     `trigger_lock`, if a trigger is attached
  3. set `LED_UNREGISTERING`
  4. `led_stop_software_blink()`
  5. `led_set_brightness(led_cdev, LED_OFF)` unless `LED_RETAIN_AT_SHUTDOWN`
  6. `flush_work(&led_cdev->set_brightness_work)`
  7. `led_remove_brightness_hw_changed()` if `LED_BRIGHT_HW_CHANGED`
  8. `device_unregister()`
  9. `list_del()` under `leds_list_lock`
  10. `mutex_destroy(&led_cdev->led_access)`
- `cancel_work_sync()`: called only inside `led_trigger_set()`; unregister
  itself uses `flush_work()`, so pending work runs instead of being dropped.
- `led_access`: never locked by `led_classdev_unregister()`.
- Step 2 with `LED_RETAIN_AT_SHUTDOWN`: `led_trigger_set()` still calls
  `led_set_brightness(led_cdev, LED_OFF)`, and does so before
  `LED_UNREGISTERING` is set.
- `brightness_set()`: called directly in the caller's context from steps 2
  and 5.
- `brightness_set_blocking()`: used only when `brightness_set` is NULL; runs
  from `set_brightness_work`, which step 6 waits for.
- `LED_SUSPENDED` set: the `LED_OFF` set calls in steps 2 and 5 update
  `led_cdev->brightness` only.
- Trigger `deactivate()`: is driver code when the driver registered a private
  trigger, for example `omnia_hwtrig_deactivate()` in
  `drivers/leds/leds-turris-omnia.c`, which takes the driver's mutex and
  writes to the chip.
- `pattern_clear()`: called by `pattern_trig_deactivate()`.
- `hw_control_set()`: its only caller is `set_baseline_state()` in
  `drivers/leds/trigger/ledtrig-netdev.c`. Step 2 can reach it, with the mode
  unchanged: `unregister_netdevice_notifier()` in `netdev_trig_deactivate()`
  replays `NETDEV_DOWN` and `NETDEV_UNREGISTER` into `netdev_trig_notify()`.
  Nothing calls it to end hardware control; that is left to the `LED_OFF`
  set call in step 2.
- `blink_set()`: `led_stop_software_blink()` does not call it; it runs only if
  `LED_SET_BLINK` is still pending when `set_brightness_delayed()` runs.
- sysfs handlers: nothing in `drivers/leds/led-class.c` tests
  `LED_UNREGISTERING`, so `brightness_store()` and `brightness_show()` can
  call the set callbacks and `brightness_get()` from other tasks until step 8.
- Failed registration, value of `led_cdev->dev` after
  `led_classdev_register_ext()` returns an error:

  | Failure | `led_cdev->dev` |
  |---|---|
  | name composition, name conflict | not written |
  | `devres_alloc()` in `devm_led_classdev_register_ext()` | not written |
  | `device_create_with_groups()` | `ERR_PTR` |
  | `led_add_brightness_hw_changed()` | NULL |

- Guard on a never-registered LED: works only if the structure was zeroed;
  `asus_wmi_led_exit()` in `drivers/platform/x86/asus-wmi.c` relies on it to
  unregister LEDs that may not exist.
- After a successful unregister: `led_cdev->dev` and `LED_UNREGISTERING` are
  both left set. The guard does not catch a second call, and a later
  registration of the same structure starts with `LED_UNREGISTERING` set.

**Managed unregister**

- `drivers/leds/uleds.c`: `uleds_open()` allocates `struct uleds_device` and
  registers nothing; `uleds_write()` registers against
  `uleds_misc.this_device`; `uleds_release()` calls
  `devm_led_classdev_unregister()` only in `ULEDS_STATE_REGISTERED`, then
  `kfree()`. There is no uleds_device_release and no `dev` field in
  `struct uleds_device`.
- `devm_led_classdev_unregister()` is also needed when a callback uses a
  resource that is not released by devres: `asus_wireless_remove()` and the
  error path of `asus_wireless_probe()` in
  `drivers/platform/x86/asus-wireless.c` call it before
  `destroy_workqueue()`.
- No matching entry: `devres_release()` returns `-ENOENT` without a message;
  the `WARN_ON()` is in `devm_led_classdev_unregister()`, which returns void
  and leaves the LED registered.
- Match: `find_dr()` in `drivers/base/devres.c` needs the same release
  function and the same pointer. An LED registered with
  `devm_led_classdev_flash_register_ext()` or
  `devm_led_classdev_multicolor_register_ext()` is not matched; use
  `devm_led_classdev_flash_unregister()` or
  `devm_led_classdev_multicolor_unregister()` with the container pointer.
- **Unsafe usage**: `led_classdev_unregister()` on an LED registered with
  `devm_led_classdev_register_ext()`.
  - Unsafe: the devres entry stays, `devm_led_classdev_release()` unregisters
    again at release, and the guard does not stop it because `led_cdev->dev`
    is still set.
  - Safe: `devm_led_classdev_unregister()` with the device given at
    registration, as `uleds_release()` does.

**Errors after unplug**

- Quiet case: needs all three of `-ENODEV`, `LED_UNREGISTERING` and
  `LED_HW_PLUGGABLE`; any other negative result except `-ENOTSUPP` is logged.
- Only place the core tests these flags:
  `set_brightness_delayed_set_brightness()` in `drivers/leds/led-core.c`.
- `led_set_brightness_sync()`: returns the callback's error to its caller, no
  filtering. `led_set_brightness_nosleep()`: returns void.
- `set_brightness_delayed_set_brightness()`: tries `__led_set_brightness()`
  first; `brightness_set()` returns void, so for a driver that provides it
  the result is always 0 and nothing is logged.
- Work queued by trigger removal: can run before `LED_UNREGISTERING` is set,
  so its `-ENODEV` is logged even with `LED_HW_PLUGGABLE`.
- Driver-side test of `LED_UNREGISTERING`: a callback may return 0 without
  touching the hardware to skip the final switch-off, as `kbd_led_set()` in
  `drivers/platform/x86/asus-wmi.c` and `lg_g13_kbd_led_set()` in
  `drivers/hid/hid-lg-g15.c` do.

**Removal ordering**

- Probe error path: `really_probe()` in `drivers/base/dd.c` runs
  `device_unbind_cleanup()` after probe returns an error, so a managed LED is
  unregistered after the probe function's own unwinding, as after `remove()`.
- **Potentially unsafe usage**: managed registration, with `remove()` or the
  probe error path releasing by hand something the callbacks use.
  - Unsafe: when the LED is still registered at that point;
    `devm_led_classdev_release()` runs later and
    `led_classdev_unregister()` calls the set callback with `LED_OFF`; the
    callback then queues on a destroyed workqueue, writes to a powered-down
    chip, or locks a destroyed mutex.
  - Unsafe: `mutex_destroy()` is an empty inline without
    `CONFIG_DEBUG_MUTEXES` (`include/linux/mutex.h`), so the mutex case shows
    up only with that option.
  - Safe: every such resource acquired with devm before the LED is
    registered, as `an30259a_probe()` in `drivers/leds/leds-an30259a.c` does
    with `devm_mutex_init()` and `devm_regmap_init_i2c()`; `release_nodes()`
    in `drivers/base/devres.c` releases in reverse order.
  - Safe: power-down registered with `devm_add_action()` before the LED, as
    `lm3532_parse_node()` in `drivers/leds/leds-lm3532.c` does.
  - Safe: `devm_led_classdev_unregister()` first, then the manual release, as
    `asus_wireless_remove()` does.
- **Unsafe usage**: unmanaged registration, with a resource the callbacks use
  released before `led_classdev_unregister()`.
  - Safe: unregister every LED, then `mutex_destroy()` and `kfree()`, as
    `npem_free()` in `drivers/pci/npem.c` does.
- sysfs handlers, including the driver's own `led_cdev->groups`: need the
  same resources until `device_unregister()` inside
  `led_classdev_unregister()` returns.
- `led_classdev_flash_unregister()` and
  `led_classdev_multicolor_unregister()`: both end in
  `led_classdev_unregister()`, so the same ordering applies.

## Setting brightness

**Brightness setting functions**

- `led_set_brightness()` starts no blink of any kind.
- `LED_BLINK_DISABLE`: set only in `led_set_brightness()`;
  `led_set_brightness_nosleep()` and `led_set_brightness_sync()` neither set
  it nor stop a software blink.
- `led_set_brightness_nopm()`: makes no runtime-PM call; what it skips is the
  clamp, the write to `led_cdev->brightness` and the `LED_SUSPENDED` test.
- Triggers in `drivers/leds/trigger/`: several call
  `led_set_brightness_nosleep()` directly, for example
  `led_heartbeat_function()` from its own timer, and so bypass the blink
  handling in `led_set_brightness()`.
- `led_mc_set_brightness()`: defined in `drivers/leds/led-core.c`, declared
  in `include/linux/leds.h`; stores the intensities, then calls
  `led_set_brightness()`.

**Deferred brightness work**

- Workqueue: `led_cdev->wq`, which `led_classdev_register_ext()` sets to
  `leds_wq`; the core does not use `schedule_work()`.
- `leds_wq`: one `alloc_ordered_workqueue()` in `leds_init()` in
  `drivers/leds/led-class.c`, shared by every LED.
- `set_brightness_delayed()`: its brightness steps do not call
  `led_set_brightness_nopm()`; they call
  `set_brightness_delayed_set_brightness()`, which tries `brightness_set`
  first and `brightness_set_blocking` only on `-ENOTSUPP`.
- Off and non-zero requests: tracked by separate bits,
  `LED_SET_BRIGHTNESS_OFF` and `LED_SET_BRIGHTNESS`; of several pending
  non-zero values only the latest is delivered, a later 0 through
  `led_set_brightness_nopm()` drops a pending non-zero value, and a pending
  off is delivered as its own `LED_OFF` call before the latest non-zero
  value.
- `led_set_brightness()` with 0 then non-zero on a software-blinking LED,
  before the work runs: the second call is queued, so the handler stops the
  blink, sets `LED_OFF`, then sets the new value.
- Silent errors: `-ENOTSUPP` when `brightness_set` is NULL and
  `brightness_set_blocking` is NULL or returns it, and `-ENODEV` when both
  `LED_UNREGISTERING` and `LED_HW_PLUGGABLE` are set; every other negative
  value goes to `dev_err()`.
- `led_trigger_set()` removing a trigger: calls `cancel_work_sync()` on
  `set_brightness_work`, so a queued change may never reach the driver.

**Synchronous brightness setting**

- Blink test: reads `blink_delay_on` and `blink_delay_off`, not
  `LED_BLINK_SW`.
- Order: blink test, write to `led_cdev->brightness`, `LED_SUSPENDED` test,
  callback.
- Suspended and blinking: `-EBUSY`, and `led_cdev->brightness` is not
  written.
- Suspended with no `brightness_set_blocking`: 0.
- After a one-shot blink has finished: still `-EBUSY`, because
  `led_timer_function()` clears `LED_BLINK_SW` and leaves the delay fields;
  `led_stop_software_blink()` zeroes them.
- `drivers/leds/trigger/ledtrig-timer.c` and
  `drivers/leds/trigger/ledtrig-oneshot.c`: write the delay fields directly
  from sysfs, so `-EBUSY` can be returned with no timer running.
- Hardware blink started through `led_blink_set_nosleep()`: the delays are
  passed by value and not written to `blink_delay_on` or `blink_delay_off`,
  so this alone does not cause `-EBUSY`.

**Brightness get callback**

- `led_update_brightness()`: returns 0 on success, never the brightness; the
  value is only in `led_cdev->brightness`.
- `led_update_brightness()`: takes no lock and has no lockdep assertion.
- `led_classdev_register_ext()`: holds `led_access` around the call; it locks
  the mutex before `device_create_with_groups()` and unlocks at the end.
- Callers outside `drivers/leds/`: take `led_access` themselves if they need
  it, as `uniwill_notify_kbd_led()` does with `guard(mutex)`.
- `brightness_show()`: returns `-ENODATA` without calling the driver when
  `led_trigger_is_hw_controlled()`, that is when the attached trigger has
  `trigger_type` set; without `CONFIG_LEDS_TRIGGERS` that test is always
  false.
- Triggers: no file under `drivers/leds/trigger/` calls
  `led_update_brightness()`.

**Brightness set callbacks**

- Neither callback set: `led_classdev_register_ext()` makes no test of the
  callbacks and registers the LED.
- Both set: `led_set_brightness_nopm()` and the work handler both use
  `brightness_set`; in the core only `led_set_brightness_sync()` reaches
  `brightness_set_blocking`.
- `brightness_set` from the work item: happens even for a driver that has
  `brightness_set`, because `led_set_brightness()` queues the work itself
  when it stops a software blink or finds a change pending.
- Locks around `brightness_set`: `brightness_store()` holds `led_access`,
  `led_trigger_event()` holds `rcu_read_lock()`, `led_timer_function()` and
  the work item hold no LED lock; no lock is common to all paths.

## Blinking

**Blink functions**

- `led_blink_set_nosleep()`: takes the delays by value; `led_blink_set()` and
  `led_blink_set_oneshot()` take pointers.
- `led_blink_set_nosleep()` defers to `set_brightness_work` only when the
  driver sets both `blink_set` and `brightness_set_blocking`.
- `led_blink_set_nosleep()` in every other case: calls `led_blink_set()` in
  the caller's context, and with it `timer_delete_sync()` and the driver's
  `blink_set` if there is one.
- Hard IRQ context: `led_blink_set()` and the direct path of
  `led_blink_set_nosleep()` trip the `WARN_ON(in_hardirq() ...)` in
  `__timer_delete_sync()` in `kernel/time/timer.c`; `led_init_core()` sets up
  `blink_timer` without `TIMER_IRQSAFE`.
- `CONFIG_PREEMPT_RT`: the same `__timer_delete_sync()` calls
  `lockdep_assert_preemption_enabled()`, which tests only with
  `CONFIG_PROVE_LOCKING`.
- `led_blink_set_oneshot()`: 500/500 is substituted only when both delays are
  zero, in `led_blink_setup()`, the same as for the other two.
- A single zero delay on the software path, one-shot included: no blink
  starts; `led_set_software_blink()` sets the LED off (`delay_on` zero) or to
  `blink_brightness` (`delay_off` zero) and arms no timer.

**Brightness while blinking**

- Zero while `LED_BLINK_SW` is set: `led_set_brightness()` only sets
  `LED_BLINK_DISABLE` and queues `set_brightness_work`; the timer is stopped
  and the off value written later, in `set_brightness_delayed()`.
- Non-zero while `LED_BLINK_SW` is set: the value goes to
  `new_blink_brightness` with `LED_BLINK_BRIGHTNESS_CHANGE`;
  `led_set_brightness()` does not write `blink_brightness` or the hardware.
- Blink run by `blink_timer`: the recorded value reaches the hardware only in
  the off-to-on branch of `led_timer_function()`, not at the next tick if the
  LED is on.
- Blink that ends first, for example a one-shot at rest: the value is not
  written when the blink ends, and `LED_BLINK_BRIGHTNESS_CHANGE` stays set
  for the next blink's first off-to-on tick.
- Non-zero while `LED_BLINK_DISABLE` or `LED_SET_BRIGHTNESS` is pending: this
  test comes before the `LED_BLINK_SW` test; the value goes to
  `delayed_set_value` with `LED_SET_BRIGHTNESS` and the work is queued.

**One-shot blink**

- A request is dropped only when `LED_BLINK_ONESHOT` is set and
  `timer_pending()` is true for `blink_timer`.
- `LED_BLINK_ONESHOT` alone refuses nothing: `led_timer_function()` does not
  clear it when the blink ends.
- `invert`: selects only the resting state, that is which write sets
  `LED_BLINK_ONESHOT_STOP`: the off write when clear, the on write when set.
- First phase: `led_timer_function()` picks it from `led_cdev->brightness`,
  not from `invert`.
- Full cycle: happens only if the LED is in its resting state at the call
  (off for `invert` clear, on for `invert` set).
- LED not in its resting state at the call: the first tick writes the resting
  state and the blink ends with no visible cycle.

**Hardware blink callback**

- Sleeping: allowed only when the driver also sets `brightness_set_blocking`.
- Without `brightness_set_blocking`: `led_blink_set_nosleep()` calls
  `blink_set` in the caller's context, for example from the timer callback
  `tpt_trig_timer()` in `net/mac80211/led.c` through `led_trigger_blink()`.
- **Unsafe usage**: a `blink_set` that can sleep in a driver that does not
  set `brightness_set_blocking`.
  - Safe: set `brightness_set_blocking` too, as the driver of
    `pca955x_led_blink()` does; the test in `led_blink_set_nosleep()` then
    defers the call to `set_brightness_work`.
  - Safe: a `blink_set` that takes only a spinlock, with `brightness_set`,
    as `bcm6328_blink_set()` in `drivers/leds/leds-bcm6328.c`.
- Delays the hardware cannot match: either adjust them, write them back and
  return 0, or return non-zero; `led_blink_setup()` accepts both, and
  `pca955x_led_blink()` does both.
- Non-zero return: `led_blink_setup()` starts the software blink with the
  delays as the callback left them, so a failing callback must not leave
  values it does not mean.
- Written-back delays: on success the core does not copy them into
  `blink_delay_on` or `blink_delay_off`; they reach only the caller's
  pointers.
- `timer_trig_activate()` in `drivers/leds/trigger/ledtrig-timer.c`: passes
  `&led_cdev->blink_delay_on` and `&led_cdev->blink_delay_off` as the
  pointers, so there the driver writes those fields itself.
- Turning off: the contract covers only an off write (`LED_OFF`) to
  `brightness_set` or `brightness_set_blocking`.
- Non-zero write during a hardware blink: the core passes it to the driver
  and the effect is the driver's choice; for example `bcm6328_led_set()`
  stops the blink for any value.

**Stopping a blink**

- `led_stop_software_blink()`: declared in `drivers/leds/leds.h`, not in
  `include/linux/leds.h`.
- `led_stop_software_blink()`: leaves `LED_BLINK_ONESHOT` and
  `LED_BLINK_ONESHOT_STOP` as they are.
- `led_stop_software_blink()` context: the `timer_delete_sync()` limits given
  under "Blink functions" apply.
- `led_blink_set()`: does not call `led_stop_software_blink()`; it calls
  `timer_delete_sync()` itself and does not zero `blink_delay_on` and
  `blink_delay_off`.
- `led_set_brightness_sync()`: stops no software blink; it returns `-EBUSY`
  when either `blink_delay_on` or `blink_delay_off` is non-zero and never
  touches `blink_timer`.
- `led_set_brightness_sync()` and a hardware blink started by the timer
  trigger: also `-EBUSY` when either field is non-zero, because
  `timer_trig_activate()` passes those two fields as the pointers and the
  driver's written-back delays land there.
- **Potentially unsafe usage**: writing the LED past `led_set_brightness()`,
  with `led_set_brightness_nosleep()` or the driver's `brightness_set`.
  - Unsafe: while `LED_BLINK_SW` is set and the caller is not the timer that
    implements the blink; `blink_timer` or the trigger's own timer stays
    armed and a later tick overwrites the write.
  - Unsafe: a direct `brightness_set` call during a software blink also
    leaves `led_cdev->brightness` stale, and `led_timer_function()` picks
    its next phase from that field.
  - Safe: from the timer that implements the blink, as
    `led_timer_function()` and `led_heartbeat_function()` do with
    `led_set_brightness_nosleep()`.
  - Safe: after `led_classdev_unregister()` has returned, as
    `rt2x00leds_unregister_led()` does with `brightness_set`;
    `led_classdev_unregister()` has called `led_stop_software_blink()`.

**Triggers with their own timer**

- `LED_BLINK_SW` in the timer callback: not tested; `led_heartbeat_function()`
  and `led_activity_function()` re-arm regardless of it.
- `LED_BLINK_BRIGHTNESS_CHANGE`: the timer callback does
  `test_and_clear_bit()` on it and, if it was set, copies
  `new_blink_brightness` into `blink_brightness` before choosing the level.
- Zero through `led_set_brightness()`: `set_brightness_delayed()` calls
  `led_stop_software_blink()`, which clears `LED_BLINK_SW` and stops only the
  core's `blink_timer`; the trigger's timer keeps running and is not told.
- After that zero: non-zero `led_set_brightness()` calls go straight to
  `led_set_brightness_nosleep()` and a later tick of the trigger's timer
  overwrites them.
- `brightness_store()` in `drivers/leds/led-class.c`: avoids this by calling
  `led_trigger_remove()` before it writes zero.
- `heartbeat_trig_deactivate()` and `activity_deactivate()` clear
  `LED_BLINK_SW` themselves; the `err_add_groups` path of
  `led_trigger_set()` calls `deactivate` without
  `led_stop_software_blink()`.
- **Potentially unsafe usage**: a trigger timer that writes the LED without
  `LED_BLINK_SW` set.
  - Unsafe: when the trigger takes its on level from `blink_brightness`; a
    non-zero `led_set_brightness()` then goes to
    `led_set_brightness_nosleep()`, never sets
    `LED_BLINK_BRIGHTNESS_CHANGE`, and a later tick overwrites the value.
  - Safe: when the trigger computes every level itself and does not use
    `blink_brightness`, as `pattern_trig_timer_common_function()` in
    `drivers/leds/trigger/ledtrig-pattern.c`.
- **Unsafe usage**: calling `led_set_brightness()` from the trigger's own
  timer while `LED_BLINK_SW` is set; non-zero is only recorded in
  `new_blink_brightness` and zero queues `LED_BLINK_DISABLE`.
  - Safe: `led_set_brightness_nosleep()`, as `led_heartbeat_function()` and
    `led_activity_function()` use.
  - Safe: `led_set_brightness()` from a timer whose trigger never sets
    `LED_BLINK_SW`, as `pattern_trig_timer_common_function()`.

## Trigger core

**Attaching a trigger**

- Removal of the old trigger, in order: `list_del_rcu()` under
  `leddev_list_lock`, `synchronize_rcu()`, `cancel_work_sync()` on
  `set_brightness_work`, `led_stop_software_blink()`,
  `device_remove_groups()`, `deactivate`, clear `trigger`, `trigger_data`,
  `activated` and `LED_INIT_DEFAULT_TRIGGER`, then `led_set_brightness()` to
  `LED_OFF`.
- On removal, `deactivate` runs after the trigger's sysfs groups are gone and
  software blink is stopped, and while `led_cdev->trigger` still points at
  the old trigger.
- Attach, in order: `list_add_tail_rcu()`, set `led_cdev->trigger`,
  `synchronize_rcu()`, `flush_work()`, `activate` (or `led_set_brightness()`
  with `trig->brightness`), `device_add_groups()`, uevent.
- LED is on `trig->led_cdevs` before `activate` runs, so an `activate` that
  calls `led_trigger_event()` reaches its own LED, as
  `power_supply_led_trigger_activate()` does.
- `LED_OFF` on removal is unconditional; there is no LED_KEEP_TRIGGER flag in
  this tree.
- `activated`: `led_trigger_set()` never sets it to true and the error path
  does not write it; a trigger that uses it sets it in its own `activate`, as
  `pattern_trig_activate()` does.
- `trigger_lock`: must be held for write; nothing in `led_trigger_set()`
  asserts it.
- Callers of `led_trigger_set()`: all are in `drivers/leds/led-triggers.c` and
  `drivers/leds/led-class.c`; other code uses `led_trigger_remove()`.

**Trigger locks and their order**

- Nesting order: `led_access`, then `leds_list_lock` or `triggers_list_lock`,
  then `trigger_lock`, then `leddev_list_lock`.
- `triggers_list_lock` and `leds_list_lock`: the core never takes one while it
  holds the other; `led_trigger_register()` and `led_trigger_unregister()`
  release the first before taking the second.
- `led_access` outside `leds_list_lock`: `led_classdev_register_ext()` holds
  `led_access` while it takes `leds_list_lock` for write and while it calls
  `led_trigger_set_default()`.
- `led_trigger_register()`, `led_trigger_unregister()` and
  `led_trigger_read()`: do not take `led_access`.
- `leddev_list_lock`: a `spinlock_t`, taken with plain `spin_lock()` and only
  in `led_trigger_set()`; walkers of `trig->led_cdevs` do not take it.
- `activate` and `deactivate`: run with `trigger_lock` held for write, plus
  whatever the caller of `led_trigger_set()` holds; any lock a callback takes
  nests inside those.
- `led_trigger_unregister()`: tests `next_trig` with `list_empty_careful()`
  before it takes any lock.
- `led_trigger_panic_notifier()` in `drivers/leds/trigger/ledtrig-panic.c`:
  walks `leds_list`, and `led_trigger_set_panic()` rewrites
  `led_cdev->trigger` and `trig_list`, with no lock and no RCU list
  operation, from the panic notifier only.

**Trigger file**

- Declaration: `BIN_ATTR()` in `drivers/leds/led-class.c`, giving
  `bin_attr_trigger`; the LED class defines no `dev_attr_trigger`.
- Name matching: `sysfs_streq()`, for none, default and trigger names alike.
- Return value of `led_trigger_set()`: ignored by `led_trigger_write()`; the
  write returns `count` even when `activate` failed and the LED was left with
  no trigger.
- `none` and `default`: handled before the list walk, so a registered trigger
  with either name cannot be selected.
- `none` with no trigger attached: nothing changes, brightness included.
- `default` with `default_trigger` NULL: nothing changes; the write returns
  `count`.
- `default` when the named trigger is not registered: the current trigger
  stays attached, a module load is requested, and the write returns `count`.
- Read listing: " default" follows none when `led_cdev->default_trigger` is
  non-NULL; it is never bracketed.
- `led_trigger_read()`: takes `triggers_list_lock` then `trigger_lock`, both
  for read, and does not test `led_sysfs_is_disabled()`.

**Default trigger**

- Module alias: `led_trigger_set_default()` requests `"ledtrig:%s"`, with a
  colon.
- `led_trigger_write()`: requests no module itself; a load happens only
  through the word default.
- Modules with a `MODULE_ALIAS()` of that form: few; search the tree for
  `"ledtrig:`. For example `drivers/leds/trigger/ledtrig-default-on.c` has
  one and `drivers/leds/trigger/ledtrig-timer.c` does not.
- Lock order in `led_trigger_set_default()`: `triggers_list_lock` (read),
  then `trigger_lock` (write).
- `default_trigger` equal to "none": `led_trigger_set_default()` calls
  `led_trigger_remove()` and returns before it takes `triggers_list_lock`.
- Failed attach: `led_match_default_trigger()` returns true whatever
  `led_trigger_set()` returned, so no module is requested, the error is
  dropped, and `led_classdev_register_ext()` still succeeds.
- Trigger registered but not `trigger_relevant()` for the LED: counts as not
  found, and the module load is requested.
- Without `CONFIG_MODULES`: `request_module_nowait()` is a stub that returns
  `-ENOSYS`; the LED waits for `led_trigger_register()`.

**Private triggers**

- `brightness` read: `brightness_show()` returns `-ENODATA` while the attached
  trigger has a non-NULL `trigger_type`; see `led_trigger_is_hw_controlled()`
  in `drivers/leds/led-class.c`.
- `brightness_store()`: has no such test; a write of 0 still removes the
  trigger.
- `led_trigger_is_hw_controlled()`: tests `trigger_type` only, not
  `hw_control_trigger` or the `hw_control_set` family of callbacks.
- PHY LEDs with the netdev trigger: not private triggers; that trigger has no
  `trigger_type`, so `brightness` reads as usual.
- Users of `struct led_hw_trigger_type`: search for the type name; for
  example `drivers/leds/leds-cros_ec.c` and
  `drivers/leds/leds-turris-omnia.c`.
- `led_trigger_set()`: does not call `trigger_relevant()`; the test is made by
  its callers `led_trigger_write()` and `led_match_default_trigger()`.
- Duplicate names: `led_trigger_register()` returns `-EEXIST` only when the
  two types are equal or either is NULL; private triggers of different types
  may share a name.

**Simple triggers**

- Name: `led_trigger_register_simple()` stores the caller's pointer and does
  not copy the string; the string must outlive the trigger.
- Allocation: `kzalloc_obj()` of one `struct led_trigger`.
- `led_trigger_unregister_simple()`: frees only the structure, with `kfree()`,
  and never the name.
- Caller's pointer after `led_trigger_unregister_simple()`: not cleared, and
  it points at freed memory; the event-source rule under Trigger
  unregistration applies.
- Without `CONFIG_LEDS_TRIGGERS`: `led_trigger_unregister_simple()`,
  `led_trigger_blink()` and `led_trigger_blink_oneshot()` are empty inlines in
  `include/linux/leds.h` too, like `led_trigger_event()`.
- Caller that tests the pointer, as `ledtrig_panic_init()` does: with
  `CONFIG_LEDS_TRIGGERS` the pointer is always written, NULL on failure; code
  that also builds without it must start the storage as NULL, for example
  with `DEFINE_LED_TRIGGER()`.

**Trigger event context**

- Walk: `list_for_each_entry_rcu()` over `trig->led_cdevs` inside
  `rcu_read_lock()`; no lock is taken.
- `led_trigger_blink()`: calls `led_blink_set_nosleep()` for each LED, not
  `led_blink_set()`.
- Delays: `led_trigger_blink()` and `led_trigger_blink_oneshot()` take them by
  value.
- Driver `blink_set` without `brightness_set_blocking`: must not sleep,
  because it runs inline in the walk.
- `led_blink_set_oneshot()`: never calls the driver's `blink_set`; a oneshot
  blink always goes through `led_set_software_blink()`.
- `led_trigger_event()` and `led_trigger_blink_oneshot()`: reach no
  `timer_delete_sync()` in the core; `led_set_brightness()` defers stopping a
  software blink to the work item.
- **Potentially unsafe usage**: calling `led_trigger_blink()` from atomic
  context.
  - Unsafe: in hard interrupt context; `led_blink_set()` calls
    `timer_delete_sync()` on `blink_timer`, and `__timer_delete_sync()` in
    `kernel/time/timer.c` warns there, since the timer is not
    `TIMER_IRQSAFE`.
  - Safe: from a timer callback, as `tpt_trig_timer()` in
    `net/mac80211/led.c` does; `in_hardirq()` is false there, so the
    `WARN_ON()` in `__timer_delete_sync()` does not fire.
  - Safe: from process context, as `power_supply_update_status_leds()` does.

**Trigger unregistration**

- Walk: `led_trigger_unregister()` walks `leds_list` under `leds_list_lock`
  and compares `led_cdev->trigger`; it does not walk `trig->led_cdevs`.
- Context: process context only; it takes rwsems, and `led_trigger_set()`
  calls `synchronize_rcu()`.
- `synchronize_rcu()`: only inside `led_trigger_set()`, once per detached
  LED; with no LED attached, `led_trigger_unregister()` does not wait for RCU
  readers.
- Repeat call: returns at once through `list_empty_careful()`;
  `heartbeat_reboot_notifier()` followed by `heartbeat_trig_exit()` relies on
  it.
- `trigger_data`: per LED and owned by the trigger's `deactivate`; the core
  sets it to NULL after `deactivate` returns, and the caller of
  `led_trigger_unregister()` has none to free.
- After return: `trig->led_cdevs` is an empty list, so `led_trigger_event()`
  on a trigger that is still allocated reaches no LED.
- **Unsafe usage**: `led_trigger_unregister()` on a zeroed trigger that was
  never registered, or whose `led_trigger_register()` returned `-EEXIST`;
  `next_trig` is not an empty list, so `list_del_init()` runs on NULL links.
  - Safe: unregister only what registered, as `ieee80211_led_exit()` does by
    testing the `name` that `ieee80211_led_init()` clears on failure.
  - Safe: `devm_led_trigger_register()`, which adds its release action only
    on success.
  - Safe: `led_trigger_unregister_simple()` on NULL.
- **Potentially unsafe usage**: an event source that can still call
  `led_trigger_event()` when `led_trigger_unregister()` returns.
  - Unsafe: when the trigger is then freed; the event functions dereference
    `trig`, and `led_trigger_unregister()` does not stop the source.
  - Safe: when the trigger stays allocated until the source is stopped, as in
    `rfkill_global_led_trigger_unregister()`, which calls
    `cancel_work_sync()` after unregistering its static triggers.

## Writing a trigger

**Trigger data for each LED**

- `led_trigger_get_led()` and `led_trigger_get_drvdata()`: macros in
  `include/linux/leds.h`, defined only under `CONFIG_LEDS_TRIGGERS`.
- Failed `activate`: `led_trigger_set()` does not call `deactivate` and sets
  `trigger_data` to NULL, so `activate` frees what it stored before it returns
  the error, as `gpio_trig_activate()` does.
- `set_device_name()` in `drivers/leds/trigger/ledtrig-netdev.c`: tests
  `led_get_trigger_data()` for NULL to detect a call from inside
  `netdev_trig_activate()`; this relies on the core clearing the pointer on
  detach.
- The core removes only `trig->groups`; a file the trigger adds itself stays
  until the trigger removes it, for example `ports_group` in
  `drivers/usb/core/ledtrig-usbport.c`.
- **Unsafe usage**: in `activate`, starting an IRQ, notifier, timer or work
  whose handler calls `led_get_trigger_data()`, before
  `led_set_trigger_data()` has stored the pointer.
  - Unsafe: the handler can run as soon as it is registered and gets NULL.
  - Safe: store first, then register, as `gpio_trig_activate()` does before
    `request_threaded_irq()`; `gpio_trig_irq()` dereferences
    `led_get_trigger_data()` with no NULL test.
- **Unsafe usage**: taking `led_cdev->led_access` or `led_cdev->trigger_lock`
  in the handler of an attribute in `trig->groups`.
  - Unsafe: `led_trigger_write()` holds both across `device_remove_groups()`
    in `led_trigger_set()`, which waits for running handlers.
  - Safe: a lock inside the trigger data, as `device_name_show()` takes
    `trigger_data->lock` in `drivers/leds/trigger/ledtrig-netdev.c`.

**Default pattern at activation**

- `LED_INIT_DEFAULT_TRIGGER` set: only in `led_match_default_trigger()` in
  `drivers/leds/led-triggers.c`, when the trigger name equals
  `led_cdev->default_trigger` and `trigger_relevant()` passes.
- `led_classdev_register_ext()` does not set it itself, only through
  `led_trigger_set_default()`; the setter does not look at `led-pattern`.
- User space can cause it to be set: writing `default` to the sysfs `trigger`
  file makes `led_trigger_write()` call `led_trigger_set_default()`.
- Cleared in two places: by `timer_trig_activate()`, `oneshot_trig_activate()`
  and `pattern_trig_activate()` after their `pattern_init()`, and by the
  removal branch of `led_trigger_set()`.
- `led_trigger_set_default()` and `led_trigger_register()` do not clear it
  after the attach.
- Removal branch of `led_trigger_set()`: runs before the attach branch in the
  same call, so `activate` sees the flag only when the LED had no trigger
  attached.
- A default trigger whose `activate` does not clear the flag leaves it set
  for as long as that trigger stays attached.
- `cht_wc_leds_blink_set()` in `drivers/leds/leds-cht-wcove.c` relies on
  that: it reads the flag in `blink_set` to tell that the default trigger is
  still in use.

**Panic indicator**

- Takeover and lighting are separate steps: `led_trigger_panic_notifier()`
  relinks LEDs and zeroes their blink delays; nothing changes brightness until
  `led_panic_blink()` runs through `panic_blink`.
- `led_trigger_set_panic()`: does not call `led_trigger_set()`, `activate` or
  `deactivate`, and does not search `trigger_list`; it uses the file-static
  `trigger`.
- `led_trigger_set_panic()` list handling: plain `list_del()` and
  `list_add_tail()` on `trig_list`, without `leddev_list_lock`.
- `vpanic()` in `kernel/panic.c` holds the body; `panic()` is a wrapper.
- Notifier chain in `vpanic()`: runs after `panic_other_cpus_shutdown()`, with
  local interrupts disabled.
- `panic_blink` in `vpanic()`: called from the reboot countdown loop with
  local interrupts disabled (only when `panic_timeout` is positive), and from
  the final loop after `local_irq_enable()`.
- `brightness_set` of a panic indicator therefore has to work with local
  interrupts disabled and without scheduling.
- `panic-indicator`: the LED core does not parse it; each driver sets
  `LED_PANIC_INDICATOR` itself. Search for the flag to list them.
- No code rejects `LED_PANIC_INDICATOR` on an LED that lacks `brightness_set`;
  the only test of the flag is in `led_trigger_panic_notifier()`.
- `brightness_set_blocking` on its own: `led_set_brightness_nopm()` never
  calls it directly, it only queues `set_brightness_work`; making the blocking
  callback atomic-safe does not help.

**Activity hooks for other subsystems**

- `ledtrig_flash_ctrl()` and `ledtrig_torch_ctrl()`: no caller in this tree.
- `ledtrig_disk_activity()`: the only caller is `ata_qc_complete()` in
  `drivers/ata/libata-core.c`; no other block driver calls it.
- `ledtrig_cpu()` idle callers: only `arch_cpu_idle_enter()` and
  `arch_cpu_idle_exit()` in `arch/arm/kernel/process.c`.
- `CPU_LED_IDLE_START`: sent from `do_idle()` after `local_irq_disable()`.
- `CPU_LED_IDLE_END`: sent from `do_idle()` after `cpuidle_idle_call()` or
  `cpu_idle_poll()` has re-enabled local interrupts.
- `suspend_cpu()` in `drivers/firmware/psci/psci_checker.c`: also calls
  `arch_cpu_idle_enter()` and `arch_cpu_idle_exit()`, both with local
  interrupts disabled.
- `CONFIG_LEDS_TRIGGER_CPU`: depends on `!PREEMPT_RT` in
  `drivers/leds/trigger/Kconfig`.
- Per-CPU triggers: `ledtrig_cpu_init()` registers them only for CPUs 0 to 7.
- `ledtrig_cpu()` on a CPU numbered 8 or higher: `_trig` is NULL, so
  `led_trigger_event()` returns at once; the CPU still counts toward the
  shared `cpu` trigger.
- `ledtrig_backlight_blank()`: a hook of the same family, called from
  `drivers/video/fbdev/core/fbmem.c`; it takes
  `ledtrig_backlight_list_mutex`, so unlike the other hooks it may sleep.

**Activate and deactivate callbacks**

- Locks held around `led_trigger_set()`, besides `led_cdev->trigger_lock` for
  write:

| Path | Also held |
|---|---|
| trigger name written to sysfs `trigger` | `led_cdev->led_access`, `triggers_list_lock` (read) |
| `none` written to `trigger`; 0 written to `brightness`; `led_trigger_remove()` from `v4l2_flash_open()` or `v4l2_subdev_get_privacy_led()` | `led_cdev->led_access` |
| `led_trigger_set_default()` from `led_classdev_register_ext()` or from `default` written to `trigger` | `led_cdev->led_access`, `triggers_list_lock` (read); only `led_cdev->led_access` when `default_trigger` is `none` |
| `led_trigger_register()`, `led_trigger_unregister()` | `leds_list_lock` (read); `triggers_list_lock` is already released |
| `led_classdev_unregister()` | none |

- **Unsafe usage**: taking `led_cdev->led_access` in `activate` or
  `deactivate`.
  - Unsafe: `led_trigger_write()`, `brightness_store()` and
    `led_classdev_register_ext()` already hold it when the callback runs.
  - Safe: a lock owned by the trigger or the driver, as
    `omnia_hwtrig_activate()` takes `leds->lock`.
- Concurrency: every lock held is per LED or taken for read, so the callbacks
  of one trigger can run at the same time for two LEDs.
- State shared across LEDs needs its own protection, as `bl_trig_activate()`
  takes `ledtrig_backlight_list_mutex` and `ieee80211_assoc_led_activate()`
  uses an atomic counter.
- `led_cdev->trigger`: set before `activate` and still set during
  `deactivate`; `power_supply_led_trigger_activate()` and
  `ieee80211_assoc_led_deactivate()` rely on it.
- `deactivate` on the `err_add_groups` path of `led_trigger_set()`: runs right
  after a successful `activate`, with the LED still on `trig->led_cdevs`, and
  without the core's `cancel_work_sync()` and `led_stop_software_blink()`.
- Detach path: the core calls `led_set_brightness()` with `LED_OFF` after
  `deactivate` returns, so `deactivate` need not turn the LED off.
- There is no del_timer_sync() here; `timer_delete_sync()` and
  `timer_shutdown_sync()` do that job, and `heartbeat_trig_deactivate()` uses
  `timer_shutdown_sync()` before `kfree()`.

## Hardware control

**Hardware control providers**

- Hardware control fields in `of_phy_led()`: set only when the PHY driver has
  all three of `led_hw_is_supported`, `led_hw_control_set` and
  `led_hw_control_get`.
- `hw_control_get_device` in `of_phy_led()`: set to
  `phy_led_hw_control_get_device()` unconditionally under
  `CONFIG_LEDS_TRIGGERS`; `struct phy_driver` has no op behind it.
- Brightness in `of_phy_led()`: phylib fills `brightness_set_blocking`, never
  `brightness_set`.
- `of_phy_leds()` is not reached for a genphy driver: `phy_probe()` tests
  `IS_ENABLED(CONFIG_PHYLIB_LEDS) && !phy_driver_is_genphy(phydev)`.
- `of_phy_leds()` registers nothing and returns 0 without `CONFIG_OF_MDIO`, or
  when the driver has none of `led_brightness_set`, `led_blink_set`,
  `led_hw_control_set`.
- Qualcomm PHYs: the LED ops are in `drivers/net/phy/qcom/qca807x.c` and
  `drivers/net/phy/qcom/qca808x.c`; `drivers/net/phy/qcom/at803x.c` sets none.
- Providers outside phylib fill `struct led_classdev` themselves; search for
  assignments to `hw_control_trigger` to list them (DSA:
  `drivers/net/dsa/qca/qca8k-leds.c`, `drivers/net/dsa/mv88e6xxx/leds.c`;
  MAC: `drivers/net/ethernet/realtek/r8169_leds.c`,
  `drivers/net/ethernet/intel/igc/igc_leds.c`).
- `drivers/net/ethernet/realtek/r8169_leds.c`: registers LEDs with
  `hw_control_trigger` and the four `hw_control_` callbacks, and no
  brightness callback at all.
- `drivers/leds/leds-cros_ec.c`: sets `hw_control_trigger` to its private
  trigger name and sets none of the callbacks; its hardware mode is entered by
  the trigger's own `activate`, through `trigger_type`
  (`struct led_hw_trigger_type`), as in `drivers/leds/leds-turris-omnia.c`.
- Consumer: `drivers/leds/trigger/ledtrig-netdev.c` is the only code that
  reads `hw_control_trigger` or calls the four callbacks.

**Netdev trigger offload**

- `can_hw_control()` has two callers: `netdev_led_attr_store()` and the
  `NETDEV_UP` case of `netdev_trig_notify()`. The result is cached in
  `trigger_data->hw_control`; `set_baseline_state()` reads only the cache.
- `set_device_name()` and `interval_store()` do not call `can_hw_control()`:
  after a `device_name` write the cached value stands until the next mode
  write or `NETDEV_UP`.
- `netdev_trig_activate()` sets `hw_control = true` without calling
  `can_hw_control()`: when `supports_hw_control()` holds and
  `hw_control_get_device()` returns non-NULL, with no mode check.
- At the end of activate, `register_netdevice_notifier()` replays
  `NETDEV_REGISTER` (and `NETDEV_UP` if the device is up) into
  `netdev_trig_notify()`; that is where `hw_control_set()` is first called,
  with the mode read by `hw_control_get()` or 0 if that failed.
- `-EOPNOTSUPP` to user space: returned only by `netdev_led_attr_store()`,
  when `brightness_set` and `brightness_set_blocking` are both NULL and
  `can_hw_control()` returned false.
- On that `-EOPNOTSUPP` the new mode and `hw_control = false` stay stored;
  nothing is rolled back and `set_baseline_state()` is not called.
- `hw_control_set()` failure: `set_baseline_state()` discards the return
  value; the write still returns `size`.
- `hw_control_is_supported()` error other than `-EOPNOTSUPP`: `dev_warn()` and
  software fallback; the error does not reach user space.
- `interval_store()`: returns `-EINVAL` as its first test while `hw_control`
  is true; `blink_set` is not consulted.

**Netdev trigger locking**

- Order in `set_device_name()`: RTNL, then the netdev instance lock of the new
  device (`netdev_lock_ops()`), then `trigger_data->lock`.
- `netdev_lock_ops()` takes the instance lock only when
  `netdev_need_ops_lock()` is true; see `include/net/netdev_lock.h`.
- `get_device_state()` calls `netif_get_link_ksettings()`, not
  `__ethtool_get_link_ksettings()`; `netif_get_link_ksettings()` asserts
  `netdev_assert_locked_ops_compat()`: instance lock for an ops-locked device,
  RTNL otherwise.
- `__ethtool_get_link_ksettings()` takes `netdev_lock_ops()` itself, so it
  cannot replace that call: `set_device_name()` already holds the instance
  lock.
- `netdev_trig_notify()`: takes no instance lock; it relies on the caller.
  `netdev_debug_event()` in `net/core/lock_debug.c` shows which events are
  raised with it held.
- `netdev_trig_notify()` acts on six events: `NETDEV_UP`, `NETDEV_DOWN`,
  `NETDEV_CHANGE`, `NETDEV_REGISTER`, `NETDEV_UNREGISTER`,
  `NETDEV_CHANGENAME`.
- `netdev_led_attr_store()` and `interval_store()`: take neither RTNL nor
  `trigger_data->lock`; they only call `cancel_delayed_work_sync()` before
  writing `mode`, `hw_control` or `interval`.
- Hardware control callbacks run under RTNL and `trigger_data->lock` from the
  notifier and `set_device_name()`, and under neither from
  `netdev_led_attr_store()`.
- `netdev_trig_activate()` takes RTNL itself: always through
  `register_netdevice_notifier()`, and through `set_device_name()` when
  `supports_hw_control()` holds and `hw_control_get_device()` returns a
  device.
- `netdev_trig_deactivate()` takes RTNL through
  `unregister_netdevice_notifier()`.
- Every caller of `led_trigger_set()` can reach activate or deactivate, and
  so must run without RTNL when the netdev trigger is involved: for example
  `led_classdev_register_ext()` via `led_trigger_set_default()` when the
  default trigger is `"netdev"`, `led_classdev_unregister()`, and a write to
  the `trigger` attribute.
- Notifier replay: `register_netdevice_notifier()` takes RTNL and calls
  `netdev_trig_notify()` for existing devices while activate is still
  running; `call_netdevice_register_net_notifiers()` takes
  `netdev_lock_ops()` around each device.

**Hardware control callbacks**

- **Unsafe usage**: setting `hw_control_is_supported`, `hw_control_set` and
  `hw_control_get` while `hw_control_trigger` is NULL.
  - Unsafe: `supports_hw_control()` passes the NULL to `strcmp()` when the
    netdev trigger is activated on the LED.
  - Safe: set `hw_control_trigger` together with the three callbacks, as
    `of_phy_led()` does.
  - Safe: set `hw_control_trigger` with none of the three callbacks, as
    `drivers/leds/leds-cros_ec.c` does; `supports_hw_control()` returns false
    before the `strcmp()`.
- **Unsafe usage**: naming `"netdev"` with the three callbacks set and
  `hw_control_get_device` NULL.
  - Unsafe: `netdev_trig_activate()` and `validate_net_dev()` call it with no
    NULL test.
  - Safe: set it always, as `of_phy_led()` does even when the other callbacks
    are not set.
- **Unsafe usage**: `hw_control_get_device()` returning a device that is not
  the `dev` member of a `struct net_device`.
  - Unsafe: `validate_net_dev()` applies `to_net_dev()` to it, and
    `netdev_trig_activate()` uses its `dev_name()` as the interface name.
  - Safe: return `&ndev->dev`, or NULL when no netdev is attached, as
    `phy_led_hw_control_get_device()` does.
- **Potentially unsafe usage**: `hw_control_set()` with no check of its
  flags.
  - Unsafe: when it does not handle 0 or a flags value that
    `hw_control_is_supported()` would refuse; from activate,
    `set_baseline_state()` calls it with the flags from `hw_control_get()`,
    or 0 if that failed, with no support check.
  - Safe: validate the flags again in `hw_control_set()`, as
    `qca8k_cled_hw_control_set()` does with `qca8k_parse_netdev()`.
  - Safe: give every flags value a defined mode, as
    `igc_led_hw_control_set()` does; it starts from `IGC_LEDCTL_MODE_OFF` and
    tests only the bits it knows.
- `hw_control_set()` return value: discarded by `set_baseline_state()`, the
  only caller; only `hw_control_is_supported()` can refuse a mode.
- `hw_control_is_supported()` may change the hardware: for an LED with no
  software fallback it may switch the LED off before returning `-EOPNOTSUPP`;
  see `rtl8168_led_hw_control_is_supported()` and the header comment in
  `drivers/leds/trigger/ledtrig-netdev.c`.
- `hw_control_get()` error code: none is fixed; `netdev_trig_activate()` only
  tests for non-zero and then keeps mode 0 with `hw_control` true.
- Turning off: no call tells the driver to leave hardware control; the only
  signal is the brightness callback, which `led_trigger_set()` reaches with
  `LED_OFF` after `deactivate`.
- `netdev_trig_deactivate()` still reaches `hw_control_set()`:
  `unregister_netdevice_notifier()` replays `NETDEV_DOWN` (if the device is
  up) and `NETDEV_UNREGISTER` into `netdev_trig_notify()`, and
  `set_baseline_state()` passes the current mode while `hw_control` is true.
- Non-zero brightness must also leave hardware control: on software fallback
  `set_baseline_state()` may write the on value with no `LED_OFF` first. See
  `qca8k_led_brightness_set()` and `igc_led_brightness_set_blocking()`.
- LED with neither `brightness_set` nor `brightness_set_blocking`: the
  `led_set_brightness()` in `led_trigger_set()` reaches no driver code, so the
  LED keeps its last hardware mode after the trigger is removed.
- `blink_set`: not called by the netdev trigger's software path;
  `netdev_trig_work()` uses `led_blink_set_oneshot()`, and `led_blink_setup()`
  skips `blink_set` for one-shot blinks.

## Patterns

**Pattern trigger**

- Kinds: three, in `enum pattern_type`, chosen by the sysfs file written.

| `data->type` | File | Driven by |
|---|---|---|
| `PATTERN_TYPE_SW` | `pattern` | `struct timer_list timer` |
| `PATTERN_TYPE_HR` | `hr_pattern` | `struct hrtimer hrtimer` |
| `PATTERN_TYPE_HW` | `hw_pattern` | no timer; the driver's `pattern_set` |

- No fallback between kinds: `pattern_trig_store_patterns()` takes the type
  from the file written and never tries another one.
- `hw_pattern` without `pattern_set`: the file does not exist
  (`pattern_trig_attrs_mode()`); it does not return an error.
- Firmware `led-pattern` default: `pattern_init()` stores it as
  `PATTERN_TYPE_SW`; `pattern_trig_activate()` never calls `pattern_set`.
- Minimum for `PATTERN_TYPE_SW` and `PATTERN_TYPE_HR`: 2 tuples, which is
  4 numbers; `npatterns` counts tuples.
- Exactly 1 tuple in `pattern` or `hr_pattern`:
  `pattern_trig_start_pattern()` returns `-EINVAL`.
- 0 tuples (a write of only a newline): `pattern_trig_start_pattern()`
  returns 0 before the minimum test; the write succeeds and the running
  pattern stays stopped.
- More than `MAX_PATTERNS` tuples: `pattern_trig_store_patterns_string()`
  stops parsing and returns 0; the first `MAX_PATTERNS` tuples run, with no
  error.
- Timer handlers: `pattern_trig_timer_common_function()` does not take
  `data->lock`.
- `data->lock`: held only by the show and store functions, and by
  `pattern_init()` through `pattern_trig_store_patterns()`; a store cancels
  the timer synchronously before it changes `patterns`, `curr`, `next` or
  `repeat`.
- `pattern_trig_timer_cancel()`: stops one timer, selected by `data->type`;
  it is correct only because the store assigns the new `data->type` after
  the cancel.
- `pattern_trig_deactivate()`: the one place that stops both timers.
- Handler context for `PATTERN_TYPE_HR`: the hrtimer is set up with
  `HRTIMER_MODE_REL`, without `HRTIMER_MODE_SOFT`; the handler writes the LED
  only through `led_set_brightness()`.
- `led_set_brightness()` from the handlers: calls `brightness_set` directly,
  through `led_set_brightness_nopm()`, if the driver has one, and otherwise
  queues `set_brightness_work`.

**Pattern callbacks**

- One-callback check: made only by `pattern_trig_activate()`; the NULLs it
  writes stay in `struct led_classdev` after the trigger is deactivated.
- `led_cdev->pattern_clear()` in `pattern_trig_store_patterns()` and
  `repeat_store()`: called with no NULL test; this relies on the activate
  check and on `hw_pattern` being hidden without `pattern_set`.
- Call sites and conditions:

| Callback | Called from | Condition |
|---|---|---|
| `pattern_set` | `pattern_trig_start_pattern()` | `data->type` is `PATTERN_TYPE_HW` and `npatterns != 0` |
| `pattern_clear` | `pattern_trig_store_patterns()` | the type before this write was `PATTERN_TYPE_HW` |
| `pattern_clear` | `repeat_store()` | `data->type` is `PATTERN_TYPE_HW` |
| `pattern_clear` | `pattern_trig_deactivate()` | pointer is non-NULL, whatever the type |

- `pattern_set` is reached from a `hw_pattern` write, and from a `repeat`
  write while the type is `PATTERN_TYPE_HW`; never from `pattern`,
  `hr_pattern` or activate.
- `data->type` after a failed `hw_pattern` write: stays `PATTERN_TYPE_HW`
  with `npatterns` 0, so the next store calls `pattern_clear` although
  `pattern_set` never succeeded.
- Context: sysfs store calls run under the mutex `data->lock` and may sleep;
  the `pattern_trig_deactivate()` call runs without `data->lock`, and before
  the software timers are stopped.
- `pattern_clear` return value: ignored at all three call sites.
- `repeat` argument: `data->repeat`, not `data->last_repeat`.
- `data->repeat` before any `repeat` write: 0, because
  `pattern_trig_activate()` sets only `last_repeat` to -1 and
  `is_indefinite`; the `repeat` file reads -1 while `pattern_set` gets 0.
- `data->repeat` after a finite software pattern:
  `pattern_trig_update_patterns()` has decremented it, and a later
  `hw_pattern` write passes what is left.
- `pattern_set` that returns `-EINVAL` for `repeat == 0`: every
  `hw_pattern` write fails until `repeat` has been written.
- Tuple meaning in software patterns: brightness goes linearly from this
  tuple's `brightness` to the next tuple's `brightness` over this tuple's
  `delta_t`; the last tuple ramps to the first
  (`pattern_trig_compute_brightness()`); a `delta_t` below
  `UPDATE_INTERVAL` gives no ramp.
- Values the trigger guarantees to `pattern_set`: `len` from 1 to
  `MAX_PATTERNS`, `brightness` from 0 to `max_brightness`; `delta_t` is any
  `u32`, 0 included; the 2-tuple minimum is not applied.
- `pattern` array: writable; `hw_pattern` reads back `data->patterns`, so a
  driver may store the values it programmed, as `sc27xx_led_pattern_set()`
  does with the rounded `delta_t`.
- **Unsafe usage**: a `pattern_clear` that needs a hardware pattern to be
  running.
  - Safe: reset the hardware unconditionally, as
    `sc27xx_led_pattern_clear()` does; `pattern_trig_deactivate()` calls it
    for software patterns too.
  - Safe: free only what was allocated, as `lpg_pattern_clear()` does;
    `lpg_lut_free()` returns early when both indexes are 0.
- **Unsafe usage**: a `pattern_set` that keeps the `pattern` pointer after
  it returns.
  - Safe: program the hardware before returning, as
    `sc27xx_led_pattern_set()` does; the array is `patterns` inside
    `struct pattern_trig_data`, rewritten by `pattern_trig_store_patterns()`
    and freed by `pattern_trig_deactivate()`.
  - Safe: copy into the driver's own allocation, as `lpg_pattern_set()`
    does.
- **Potentially unsafe usage**: `pattern_set` reading `pattern[i]` with no
  test of `len`.
  - Unsafe: for `i >= 1`; with a shorter `len` the entry holds zeros or a
    tuple from an earlier write, because a store resets `npatterns` and not
    the array.
  - Safe: `pattern[0]` alone, as `ncp5623_pattern_set()` reads;
    `pattern_trig_start_pattern()` returns before the callback when
    `npatterns` is 0.
  - Safe: after a test of `len`, as `cht_wc_leds_pattern_set()` does with
    `len != 2`.

## Multicolor class

**Multicolor structures**

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

**Multicolor registration**

- Checks: `-EINVAL` for NULL `mcled_cdev`, for `num_colors` of 0, and for
  `num_colors > LED_COLOR_ID_MAX`; nothing else.
- `LED_COLOR_ID_MAX` bound: `multi_intensity_store()` parses into a stack
  array of `LED_COLOR_ID_MAX` entries.
- `subled_info`, each `color_index`, each `max_intensity`: not checked and
  not modified by `led_classdev_multicolor_register_ext()`.
- `led_cdev.color`: not written by
  `led_classdev_multicolor_register_ext()`; the driver sets it itself, for
  example `LED_COLOR_ID_MULTI` in `leds_gmc_probe()`, and
  `led_classdev_register_ext()` replaces it with the fwnode "color" property
  when `init_data->fwnode` has one.
- Members written: `flags` (ORs in `LED_MULTI_COLOR`) and `groups` (assigned
  `led_multicolor_groups`, generated by `ATTRIBUTE_GROUPS(led_multicolor)`);
  there is no led_mc_groups.
- Driver attributes: the multicolor class has no hook for them; add the group
  to `led_cdev.dev` after registration with `devm_device_add_group()`, as
  `oxp_cfg_probe()` in `drivers/hid/hid-oxp.c` does, or with
  `device_add_group()`.

**Component calculation**

- Formula: `DIV_ROUND_CLOSEST(brightness * intensity,
  led_cdev->max_brightness)`; the result is rounded to nearest, not
  truncated.
- Divisor: always `led_cdev->max_brightness`;
  `led_mc_calc_color_components()` does not read `max_intensity`.
- `intensity` above `max_brightness`: gives a `subled_info[i].brightness`
  above `max_brightness` at full brightness; the helper does not clamp.
- Drivers with hardware global brightness, for example
  `drivers/leds/leds-lp50xx.c`: write `intensity` to the channel register
  directly and have no call to `led_mc_calc_color_components()`.
- Drivers that set a nonzero `max_intensity` (search `.max_intensity =`):
  none of them calls the helper for that LED.
- Callers outside the brightness callback: a driver may call it with a
  brightness of its own choice, for example `LED_FULL` after setting a
  pattern in `drivers/leds/rgb/leds-qcom-lpg.c`, or `cdev->max_brightness`
  in `drivers/leds/leds-turris-omnia.c`.
- Software-scaling example: `led_pwm_mc_set()` in
  `drivers/leds/rgb/leds-pwm-multicolor.c`.

**Multicolor sysfs files**

- Files: three, not two; `multi_max_intensity` (read-only) is added beside
  `multi_intensity` and `multi_index`.
- `multi_max_intensity`: prints `led_mc_get_max_intensity()` for each
  sub-LED, computed at read time, so a channel with `max_intensity` 0 shows
  the current `led_cdev.max_brightness`.
- Limit on a written value: `multi_intensity_store()` stores
  `min(value, led_mc_get_max_intensity())`, that is `max_intensity` if
  nonzero, else `led_cdev.max_brightness`.
- Over-limit value: clamped silently; the write still returns `size`, not an
  error.
- `led_sysfs_is_disabled()`: not called by `multi_intensity_store()`; a
  write succeeds while sysfs access is disabled for `brightness`.
- `LED_BLINK_SW` set in `work_flags`: `multi_intensity_store()` skips
  `led_set_brightness()`; only `intensity` is updated and the driver is not
  called by the store.
- `LED_BLINK_SW` clear: `led_set_brightness(led_cdev, led_cdev->brightness)`
  is the only path to the hardware; for a driver with only
  `brightness_set_blocking` the write to hardware happens later, from
  `set_brightness_work`.

**Multicolor from kernel code**

- Signature: `led_mc_set_brightness(led_cdev, intensity_value, num_colors,
  brightness)`; `brightness` is last.
- Return type: `led_mc_set_brightness()` and `led_mc_trigger_event()` both
  return void; a caller cannot detect failure.
- `led_mc_set_brightness()` on a LED without `LED_MULTI_COLOR`:
  `dev_err_once()`, no change, no fallback to `led_set_brightness()`.
- `led_mc_set_brightness()` with wrong `num_colors`: `dev_err_once()`, no
  change to intensities or brightness.
- `led_mc_trigger_event()` on a LED without `LED_MULTI_COLOR`: skips it
  itself, with no log message; only a `num_colors` mismatch reaches the
  `dev_err_once()` in `led_mc_set_brightness()`.
- `led_mc_trigger_event()`: does not blink; it only calls
  `led_mc_set_brightness()` for each LED on `trig->led_cdevs` that has
  `LED_MULTI_COLOR`.
- Clamping: `led_mc_set_brightness()` stores `intensity_value[i]` as given;
  neither `max_intensity` nor `max_brightness` limits it, unlike
  `multi_intensity_store()`.
- `trig->brightness`: not written by `led_mc_trigger_event()`, while
  `led_trigger_event()` writes it.
- LED bound to the trigger after the event: `led_trigger_set()` applies only
  `trig->brightness` unless the trigger has `activate`; a multicolor trigger
  resends the color from `activate`, as
  `power_supply_led_trigger_activate()` in
  `drivers/power/supply/power_supply_leds.c` does.
- **Potentially unsafe usage**: calling `lcdev_to_mccdev()` on a
  `struct led_classdev`.
  - Unsafe: when the LED comes from a list or lookup that can hold plain
    LEDs, such as `trig->led_cdevs`, and `LED_MULTI_COLOR` was not tested;
    the `container_of()` result does not point at a
    `struct led_classdev_mc`.
  - Safe: after testing `led_cdev->flags & LED_MULTI_COLOR`, as
    `led_mc_set_brightness()` in `drivers/leds/led-core.c` does; the flag is
    set only by `led_classdev_multicolor_register_ext()`.
  - Safe: in a callback of the driver that registered the LED with
    `led_classdev_multicolor_register_ext()`, as `lp50xx_brightness_set()`
    in `drivers/leds/leds-lp50xx.c` does; `lp50xx_probe_dt()` installs it
    only on the `led_cdev` member of its `struct led_classdev_mc`.

## Flash class

**Flash structures**

- `struct led_classdev_flash`: three `struct led_flash_setting` members,
  `brightness`, `timeout` and `duration`.
- `struct led_flash_ops`: seven members; besides the five setters and getters
  for brightness, strobe and timeout it has `fault_get` and `duration_set`.
- `duration` and `duration_set`: reached only through
  `led_set_flash_duration()` in `drivers/leds/led-class-flash.c`, which has no
  caller in this tree.
- `duration_set`: no driver in this tree sets it.
- `duration`: no sysfs group, no control in
  `drivers/media/v4l2-core/v4l2-flash-led-class.c`, and `led_flash_resume()`
  does not re-apply it.
- `duration` unit: the only statement is the header comment, which says
  microseconds.
- `flash_brightness_set`, `flash_brightness_get`, `strobe_get`, `timeout_set`,
  `fault_get`, `duration_set`: optional; registration never fails for lack of
  one.
- Without `LED_DEV_CAP_FLASH`: no op is required and `ops` may be NULL, as in
  `qcom_flash_register_led_device()` for a node with no
  "flash-max-microamp".

**Flash registration**

- `LED_DEV_CAP_FLASH`: set by the driver in `led_cdev.flags` before the call;
  `led_classdev_flash_register_ext()` only tests it.
- With the flag, in order: `led_cdev.brightness_set_blocking` must be set,
  then `ops` and `ops->strobe_set`; each failure returns `-EINVAL`.
- With the flag: `led_cdev->flash_resume` is set to `led_flash_resume()`.
- Without the flag: none of these checks run, `ops` may be NULL, and no flash
  attribute is created.
- `led_access`: initialised by `led_classdev_register_ext()`, not by the flash
  code.
- There is no led_flash_groups array; `led_flash_init_sysfs_groups()` fills
  `fled_cdev->sysfs_groups`.
- Group selection: strobe always; brightness if `ops->flash_brightness_set`;
  timeout if `ops->timeout_set`; fault if `ops->fault_get`.
- `led_cdev->groups` with the flag: overwritten with
  `fled_cdev->sysfs_groups`, so groups a driver put there before the call are
  dropped.
- `sysfs_groups` terminator: `led_flash_init_sysfs_groups()` never writes the
  NULL entry.
  - `LED_FLASH_SYSFS_GROUPS_SIZE` is 5, four groups plus the terminator.
- **Unsafe usage**: registering with `LED_DEV_CAP_FLASH` a
  `struct led_classdev_flash` whose `sysfs_groups` is not zeroed.
  - Safe: the structure comes from zeroed memory, as in `mt6370_led_probe()`,
    which allocates it with `devm_kzalloc()`; the entry after the last group
    is then NULL when `led_classdev_register_ext()` passes `led_cdev->groups`
    to `device_create_with_groups()`, and `internal_create_groups()` in
    `fs/sysfs/group.c` walks the array up to the first NULL.
- `__fill_ctrl_init_data()` in
  `drivers/media/v4l2-core/v4l2-flash-led-class.c`: also tests the flag; for an
  `fled_cdev` without it, it warns and creates no flash or torch control.

**Flash setting helpers**

- Value between two steps: rounded to the nearest step counted from `min`, a
  tie goes up; `led_clamp_align()` adds `step / 2` before it clamps.
- LED suspended (`LED_SUSPENDED`): `led_set_flash_brightness()` and
  `led_set_flash_timeout()` both return 0, not `-EBUSY`; the op is not called
  and the aligned value stays in `val`.
- Cached value: `led_flash_resume()` writes it to the driver when
  `led_classdev_resume()` runs.
- Missing op: `-EINVAL` only when the LED is not suspended; while suspended
  the helper returns 0.
- `val`: written before the op is called, and kept when the op fails or is
  missing.
- `step`: a divisor in `led_clamp_align()`; it must be non-zero before either
  helper is called.
- `fled_cdev`: must be non-NULL; the helpers write `val` before
  `has_flash_op()` tests the pointer.
- `ops`: must be non-NULL; `has_flash_op()` in
  `drivers/leds/led-class-flash.c` dereferences it without a test.

**V4L2 flash wrapper**

- `v4l2_flash_init()`: rejects only a NULL `config`; a NULL `fled_cdev` or a
  NULL `ops` is accepted.
- `struct v4l2_flash`: allocated with `devm_kzalloc()` on `dev` in
  `__v4l2_flash_init()`; `v4l2_flash_release()` does not free it.
- LED pointer: stored bare in `struct v4l2_flash`; the wrapper takes no
  reference on the LED.
- `v4l2_flash_init()` drives the LED before any open:
  `v4l2_flash_init_controls()` calls `v4l2_ctrl_handler_setup()`, which runs
  `v4l2_flash_s_ctrl()` for each control that is neither a button nor
  read-only, until one returns an error.
  - This reaches `led_set_flash_strobe()`, `led_set_flash_timeout()`,
    `led_set_flash_brightness()` and `led_set_brightness_sync()`.
  - Sysfs is not disabled and `led_access` is not held at that point.
  - The return value of `v4l2_ctrl_handler_setup()` is ignored.
- **Unsafe usage**: calling `v4l2_flash_init()` on a flash LED that has not
  passed `led_classdev_flash_register_ext()`.
  - Safe: register first, then init, as `mt6370_led_register()` does;
    registration is what guarantees `ops->strobe_set`.
- `v4l2_flash_open()` and `v4l2_flash_close()`: act only when
  `v4l2_fh_is_singular()`, that is on the first open and the last close.
- `v4l2_flash_open()`: calls `led_trigger_remove()` for the flash LED and for
  the indicator, under `led_access`.
- `v4l2_flash_close()`: does not restore the trigger.
- `v4l2_flash_close()`: sets the `STROBE_SOURCE` control back to software when
  that control exists, under `led_access`, before `led_sysfs_enable()`.
- `LED_SYSFS_DISABLE`: stops only store handlers that test
  `led_sysfs_is_disabled()`; show handlers such as `flash_strobe_show()` and
  `flash_brightness_show()` still call the driver while the sub-device is
  open.
- `led_set_brightness_sync()`: returns `-EBUSY` while `blink_delay_on` or
  `blink_delay_off` is set, and `-ENOTSUPP` without
  `brightness_set_blocking`.
- Indicator LED: neither `led_classdev_register_ext()` nor
  `v4l2_flash_indicator_init()` checks its `brightness_set_blocking`; without
  it `__sync_device_with_v4l2_controls()` fails and `v4l2_flash_open()`
  returns the error.
- `V4L2_CID_FLASH_LED_MODE` set to none or flash: the result of
  `led_set_brightness_sync()` with `LED_OFF` is ignored.

**Flash strobe helpers**

- `led_set_flash_strobe()`: calls `ops->strobe_set` with no test of `ops` or
  of the op; a NULL there is a NULL dereference, not `-EINVAL`.
- `led_get_flash_strobe()`: tests `ops->strobe_get` but not `ops`.
- `LED_SUSPENDED`: neither helper tests it; the op is called on a suspended
  LED.
- **Unsafe usage**: calling either helper on a `struct led_classdev_flash`
  that has not passed `led_classdev_flash_register_ext()` with
  `LED_DEV_CAP_FLASH` set.
  - Safe: `flash_strobe_store()` and `flash_strobe_show()`; the `flash_strobe`
    attribute is created only by `led_flash_init_sysfs_groups()`, which runs
    after the `ops` and `strobe_set` checks.
  - Safe: `v4l2_flash_s_ctrl()` on an LED registered before
    `v4l2_flash_init()`; `__fill_ctrl_init_data()` creates the mode and strobe
    controls only when the flag is set.
- `flash_strobe_store()`: holds `led_cdev->led_access` around
  `led_set_flash_strobe()`.
- `flash_strobe_show()`: takes no lock around `led_get_flash_strobe()`, and
  does not test `led_sysfs_is_disabled()`.
- `v4l2_flash_s_ctrl()` and `v4l2_flash_g_volatile_ctrl()`: call the helpers
  without `led_access`.
- `led_access` therefore does not serialise `strobe_get` against `strobe_set`;
  the helpers take no lock of their own.

## LED consumers

**Getting an LED**

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

**Consumer references**

- There is no __led_get() here; `led_module_get()` in
  `drivers/leds/led-class.c` takes the module reference.
- Module reference: blocks only unloading of the provider module; unbinding
  the provider device, for example through `unbind_store()`, is not blocked.
- Getters: create no device link between consumer and provider; for an OF
  `leds` property fw_devlink may create one (`parse_leds()` in
  `drivers/of/property.c`).
- After a provider unbind: `led_classdev_unregister()` has run, and the
  consumer's device reference keeps only `led_cdev->dev` allocated, not the
  provider-owned `struct led_classdev`.
- `led_put()` after a provider unbind: reads
  `led_cdev->dev->parent->driver`, which `device_unbind_cleanup()` has set to
  NULL.
- `led_module_get()` and `led_put()`: read
  `led_cdev->dev->parent->driver->owner` with no NULL test.
- **Unsafe usage**: a lookup entry or `leds` reference that resolves to an LED
  whose parent is NULL or has no bound driver, such as the LEDs of
  `drivers/input/input-leds.c`, whose parent is a `struct input_dev`.
  - Safe: an LED whose parent is the device its driver is bound to, as
    `skl_int3472_register_led()` registers with `int3472->dev` when
    `skl_int3472_discrete_probe()` has set that to its own platform device.
- **Unsafe usage**: `led_put()` on NULL or on an `ERR_PTR()`; `led_put()`
  dereferences its argument with no test.
  - Safe: test first, as `v4l2_subdev_put_privacy_led()` does with
    `IS_ERR_OR_NULL()`.
- **Unsafe usage**: `led_put()` on an LED from `devm_led_get()`,
  `devm_of_led_get()` or `devm_of_led_get_optional()`; `devm_led_release()`
  puts it a second time.
  - Safe: `led_put()` paired with `led_get()`, as in
    `v4l2_subdev_put_privacy_led()`.

**Lookup table**

- `provider`: compared with the class device name, not with
  `led_cdev->name`; registration does not rewrite `led_cdev->name` when it
  appends a suffix.
- Name collision: the LED that already holds the plain name is the one
  `class_find_device_by_name()` finds, so `led_get()` returns that other LED
  and does not defer.
- Entry use: `led_get()` reads the entry only under `leds_lookup_lock` and
  keeps no pointer to it; the returned LED does not depend on the entry.
- **Potentially unsafe usage**: a `struct led_lookup_data`, or a string it
  points to, in memory that is not static.
  - Unsafe: when the memory, or a string it points to, is released while the
    entry is still on `leds_lookup_list`; every later `led_get()` that
    reaches the table walks it.
  - Safe: an entry embedded in driver data and removed before that data is
    freed, as `skl_int3472_unregister_leds()` does for entries added by
    `skl_int3472_register_led()`.
  - Safe: an entry added just before the get and removed just after, as
    `yogabook_probe()` does around `devm_led_get()`.
- **Unsafe usage**: adding an entry with a NULL `dev_id` or `con_id`, or
  calling `led_get()` with a NULL `con_id`; `led_get()` passes them to
  `strcmp()` untested.
  - Safe: fill every string before `led_add_lookup()`, as `yogabook_probe()`
    sets `dev_id` from `dev_name()` first.
- **Unsafe usage**: `led_remove_lookup()` on an entry that is not on the
  list, either never added or already removed; it tests only for a NULL
  pointer before `list_del()`.
  - Safe: remove only what was added, as `skl_int3472_unregister_leds()`
    loops over the `n_leds` entries that `skl_int3472_register_led()` added.

## Suspend and shutdown

**Suspend and resume**

- `led_classdev_suspend()`: saves nothing; `led_cdev->brightness` is the only
  copy of the value that `led_classdev_resume()` writes back.
- `led_classdev_suspend()`: flushes `set_brightness_work`, so a
  `brightness_set_blocking` driver too has been called with `LED_OFF` on
  return; `led_classdev_resume()` does not flush.
- `led_classdev_resume()`: calls `flash_resume` when the pointer is set, before
  it clears `LED_SUSPENDED`; `led_classdev_flash_register_ext()` sets the
  pointer when the driver has `LED_DEV_CAP_FLASH`.
- `LED_SUSPENDED` seen by the driver: set before the suspend write and cleared
  after the resume write, so a `brightness_set` callback sees it set in both.
- `LED_CORE_SUSPENDRESUME`: opt-in; without it `led_suspend()` and
  `led_resume()` do nothing.
- `LED_CORE_SUSPENDRESUME` from firmware: the core never sets it;
  `retain-state-suspended` is parsed by drivers only, for example
  `gpio_leds_create()` in `drivers/leds/leds-gpio.c`.
- `LED_SUSPENDED` in `drivers/leds/led-core.c`: tested only by
  `led_set_brightness_nosleep()` and `led_set_brightness_sync()`; a value is
  cached and applied at resume only if the call reaches one of them.
- `led_set_brightness()` with `LED_BLINK_SW` set, non-zero value, and neither
  `LED_SET_BRIGHTNESS` nor `LED_BLINK_DISABLE` pending: stored in
  `new_blink_brightness`, not in `led_cdev->brightness`.
- `led_set_brightness()` with `LED_BLINK_SW` set, value 0: queues
  `set_brightness_delayed()`, which calls the driver with `LED_OFF` while
  suspended and does not store to `led_cdev->brightness`.
- `led_blink_set()` while suspended: calls the driver's `blink_set` callback;
  nothing on that path tests `LED_SUSPENDED`.
- `blink_timer`: not stopped by `led_classdev_suspend()`; resume writes
  whichever blink phase the timer stored last.
- `led_update_brightness()`: no `LED_SUSPENDED` test; with a `brightness_get`
  callback it overwrites `led_cdev->brightness` with the hardware value, and
  resume restores that. `brightness_show()` calls it.
- **Potentially unsafe usage**: calling `led_update_brightness()` on an LED
  that has `brightness_get`.
  - Unsafe: while `LED_SUSPENDED` is set; the value that
    `led_classdev_resume()` restores is replaced by what the hardware reports.
  - Safe: before `led_classdev_suspend()`, as `kbdlight_suspend()` in
    `drivers/platform/x86/lenovo/thinkpad_acpi.c` does; `led_classdev_resume()`
    is what reads the field.

**State at shutdown**

- System shutdown: the core does nothing; `leds_class` in
  `drivers/leds/led-class.c` sets no `shutdown_pre`, and there is no
  led_classdev_shutdown() in this tree.
- `led_classdev_register_ext()`: sets `LED_RETAIN_AT_SHUTDOWN` itself when
  `init_data->fwnode` has `retain-state-shutdown`; `led_parse_fwnode_props()`
  and `led_init_core()` do not parse it.
- Driver `.shutdown`: a driver's own shutdown callback has to test the flag,
  as `gpio_led_shutdown()` in `drivers/leds/leds-gpio.c` does before it sets
  each LED to `LED_OFF`; the flag to test is in `led_cdev->flags` after
  registration; `ncp5623_shutdown()` in `drivers/leds/rgb/leds-ncp5623.c`
  relies on the core having set the flag.
- Hibernation: `SIMPLE_DEV_PM_OPS()` in `drivers/leds/led-class.c` installs
  `led_suspend()` as `.poweroff` under `CONFIG_PM_SLEEP`; it tests only
  `LED_CORE_SUSPENDRESUME`, so when `.poweroff` runs
  (`hibernation_platform_enter()`) an LED with that flag is turned off
  whatever `LED_RETAIN_AT_SHUTDOWN` says.

## Device tree bindings

**Common binding**

- `deprecated:` keyword: `Documentation/devicetree/bindings/leds/common.yaml`
  does not use it on any property.
- `label`: deprecated in its description text only ("use 'function' and
  'color' properties instead").
- `nand-disk` value of `linux,default-trigger`: marked deprecated in a YAML
  comment only, which points to `mtd`.
- `retain-state-suspended`: not in `common.yaml`; `leds-gpio.yaml` and
  `leds-lgm.yaml` declare it in their own child-node schema, and any other
  binding that wants it and closes its LED node with
  `unevaluatedProperties: false` or `additionalProperties: false` must do
  the same.
- `power-supply`: not in `common.yaml`.
- linux,default-trigger-delay-ms and flash-led-max-microamp: defined nowhere
  in this tree.
- Easy to miss in `common.yaml`: `default-intensity`, `max-brightness`,
  `default-brightness`, `active-high`, `inactive-high-impedance`.
- `allOf` in `common.yaml`: a node with `active-low` may not also have
  `active-high`.
- `additionalProperties: false` beside `$ref: common.yaml#`: used in-tree as
  a whitelist; only common properties re-listed as `name: true` are accepted.
  See `regulator-led.yaml` and the sub-LED nodes of
  `leds-pwm-multicolor.yaml`.
- `unevaluatedProperties: false` beside the `$ref`: accepts every property
  of `common.yaml`; see `leds-gpio.yaml`.
- `Documentation/devicetree/bindings/leds/backlight/common.yaml`: a separate
  schema for backlights; a relative `$ref: common.yaml#` in a file under
  `backlight/` names that one, not the LED one.

**Function and color constants**

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

**Color identifiers**

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

**Multicolor binding**

- `$nodename` pattern in `leds-class-multicolor.yaml`:
  `^multi-led(@[0-9a-f]|-[0-9]+)?$`. That is `multi-led`, `multi-led@` plus
  one hex digit, or `multi-led-` plus decimal digits.
- `LED_COLOR_ID_RGB`: the comment in `include/dt-bindings/leds/common.h`
  defines it as an LED "that can do arbitrary color", including RGBW and
  similar; it is not limited to three-channel red/green/blue.
- Some drivers accept only `LED_COLOR_ID_RGB` on the multi-led node and fail
  probe otherwise, for example `drivers/leds/leds-sun50i-a100.c`; the class
  schema alone does not show this.
- Sub-LED nodes: `leds-class-multicolor.yaml` defines none. Each controller
  binding adds its own `patternProperties` under the multi-led node, for
  example `^led@[0-9a-f]+$` with `reg` in `leds-lp50xx.yaml` and
  `^led-[0-9a-z]+$` with `pwms` in `leds-pwm-multicolor.yaml`.
- Sub-LEDs by reference: `leds-group-multicolor.yaml` has no child nodes;
  the multi-led node lists ordinary monochrome LEDs in a `leds` phandle
  property.
- `leds_gmc_probe()` in `drivers/leds/rgb/leds-group-multicolor.c`: takes
  each sub-LED color from the referenced LED's `led_cdev->color`.

**Trigger sources and consumers**

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

## User-space LEDs

**User-space LED driver**

- `uleds_misc`: minor is `MISC_DYNAMIC_MINOR`; there is no ULEDS_MINOR in this
  tree.
- `uleds_open()`: allocates `struct uleds_device` and sets `led_cdev.name` and
  `led_cdev.brightness_set`; `uleds_write()` does not allocate the structure.
- Registration: `uleds_write()` calls `devm_led_classdev_register()` with
  parent `uleds_misc.this_device`, not `led_classdev_register()`.
- Removal: `uleds_release()` calls `devm_led_classdev_unregister()` on the same
  parent, only if the state is `ULEDS_STATE_REGISTERED`.
- Hook: the driver sets `brightness_set`, not `brightness_set_blocking`, and
  writes no `flags` (no `LED_CORE_SUSPENDRESUME`).
- Name checks in `uleds_write()`, each failing with `-EINVAL`: empty, `"."`,
  `".."`, contains `/`, or no `'\0'` within `LED_MAX_NAME_SIZE` bytes.
- Unterminated name: rejected, never truncated or terminated by the driver.
- `max_brightness <= 0`: `-EINVAL`, so negative values are rejected too.
- Order of checks in `uleds_write()`: `-EBUSY` is tested before the size, so
  any non-empty write to a registered fd gives `-EBUSY`.
- Failed write: leaves the state at `ULEDS_STATE_UNKNOWN`, so the same fd can
  write again.
- Name clash: `led_classdev_next_name()` in `drivers/leds/led-class.c` appends
  `_<n>`; uleds does not set `LED_REJECT_NAME_CONFLICT`.
- Renamed LED: `led_cdev.name` keeps the name as written, and nothing on the fd
  reports the final name.
- Name clash where the suffixed name does not fit in `LED_MAX_NAME_SIZE`:
  the write fails with `-ENOMEM`.
- Value read: one `int` (`sizeof(udev->brightness)`), not one byte.
- `uleds_read()` with `count` below `sizeof(int)`: returns 0, not `-EINVAL`.
- `Documentation/leds/uleds.rst`: says a single byte is read and shows
  `struct uleds_user_dev` without `max_brightness`; the code does neither.
- `uleds_read()` before registration: `-ENODEV`.
- First read after a successful write: does not block, because
  `uleds_write()` sets `new_data`; it returns the stored `brightness`, which
  is 0 unless something has set the LED since.
- `uleds_brightness_set()`: sets `new_data` and wakes `waitq` only when the
  value differs from the stored `brightness`.
- `struct uleds_device`: keeps only the latest value, in `brightness`; changes
  between two reads collapse into one.
- `mutex` of `struct uleds_device`: taken by `uleds_write()` and
  `uleds_read()` only; `uleds_brightness_set()` writes `brightness` and
  `new_data`, and `uleds_poll()` reads `new_data`, without it.

## Conventions

**Conventions for new code**

These are conventions that the maintainers of the LED subsystem ask of new
code. Existing code may differ. A kernel tree cannot supply all of them, so
they are kept by hand and inserted as they are.

- The subject of a commit has the form "leds: <driver>: <Capitalized
  description>", for example "leds: qwerty: Add support for Qwerty LED".
- Always capitalize the description after the subsystem prefix. The MFD and
  Backlight subsystems ask for the same.
- Choose clear names for data structures. Name the structure that holds a
  driver's private data after the device, for example struct qwerty_led, and
  name the variable that holds an instance `ddata`. Avoid generic names such
  as `info` or `priv`.
- Prefer `devm_led_classdev_register()` or `devm_led_classdev_register_ext()`
  to the unmanaged `led_classdev_register()`.
- Prefer `devm_led_trigger_register()` to `led_trigger_register()` where
  possible.
- In a new device tree binding, prefer the `color` and `function` properties
  to `label`. Use `label` only in a legacy driver or for backwards
  compatibility.
- Do not print a message when an operation succeeds, such as "LED registered
  successfully" or "Probe success". Log only errors and warnings.
- Always use `dev_err_probe()` to report a probe failure, such as a missing
  regulator or GPIO.

## Model gaps

### Other mistakes models make

- Models name ledtrig-audio.c and ledtrig_audio_set(). `sound/core/control_led.c`
  does that job and reads the trigger state back with
  `led_trigger_get_brightness()`.
- Models take the usbport trigger to be the only reader of `trigger-sources`.
  `gpio_trig_activate()` returns `-EINVAL` when `gpiod_get_optional()` finds
  no GPIO under that name; `desired_brightness` is the gpio trigger's only
  sysfs file.
- Models do not know that `gpio` and `active_low` of `struct gpio_led` exist
  only under `CONFIG_GPIOLIB_LEGACY`; see `include/linux/leds.h`.
