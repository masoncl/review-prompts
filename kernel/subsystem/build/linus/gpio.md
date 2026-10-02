# GPIO Subsystem

## Main structures

### Objects and how they relate

- `struct gpio_device` holds its own copies of what the core needs after
  the chip is gone: `base`, `ngpio`, `label`, `can_sleep`, filled in by
  `gpiochip_add_data_with_key()`. `gpiod_cansleep()` and `desc_to_gpio()`
  read the device, not the chip.
- `gc->base` still exists; with a negative value the allocated base is
  written back into it, and `gpio_to_desc()` reads `gdev->base`.
- `struct gpio_chip` has no `valid_mask` field: the line-validity bitmap is
  `gdev->valid_mask`, read through `gpiochip_line_is_valid()`. The interrupt
  mask `gc->irq.valid_mask` is separate.
- Three SRCU domains, not interchangeable: `gpio_devices_srcu` for the global
  list, `gdev->srcu` for `gdev->chip`, `gdev->desc_srcu` for `desc->label`
  (a `struct gpio_desc_label`).
- `struct gpio_chip_guard` with `CLASS(gpio_chip_guard, ...)` is defined in
  `drivers/gpio/gpiolib.h` and is built from a `const struct gpio_desc *`
  only; for code that has just a `struct gpio_device` see "Chip, device and
  descriptor".
- A hog is claimed by `gpiochip_hog_lines()` in `drivers/gpio/gpiolib.c`
  through `gpiod_hog()` and marked `GPIOD_FLAG_IS_HOGGED` on the descriptor;
  see "Registering a chip".
- `struct gpiod_lookup`: `key` is a chip label, or a line name when
  `chip_hwnum` is `U16_MAX`; see `gpio_desc_table_match()`.
- Software-node references find the chip by firmware node
  (`gpio_device_find_by_fwnode()` in `swnode_get_gpio_device()`), not by
  label.
- `struct gpio_generic_chip` (`include/linux/gpio/generic.h`) is the MMIO
  helper: it embeds the `struct gpio_chip` and is set up by
  `gpio_generic_chip_init()`. There is no bgpio_init() and `struct gpio_chip`
  has no bgpio fields.
- Shared lines (`CONFIG_GPIO_SHARED`, `drivers/gpio/gpiolib-shared.c`), four
  objects:

  | Structure | Represents |
  |---|---|
  | `struct gpio_shared_entry` | one physical pin: controller fwnode and offset |
  | `struct gpio_shared_ref` | one consumer reference to that pin; embeds a `struct auxiliary_device` |
  | `struct gpio_shared_desc` | the real descriptor plus vote and use counts; one per entry; defined in `drivers/gpio/gpiolib-shared.h` |
  | `struct gpio_shared_proxy_data` | a one-line sleeping `struct gpio_chip` per ref, in `drivers/gpio/gpio-shared-proxy.c` |

- A consumer of a shared line never holds the real descriptor:
  `gpiod_find_and_request()` sees `GPIOD_FLAG_SHARED`, calls
  `gpio_shared_add_proxy_lookup()` to add a `struct gpiod_lookup_table`, and
  resolves through it to offset 0 of that consumer's proxy chip.

## Where to look

**Core files**

| Job | File under `drivers/gpio/` | Easy to miss |
|---|---|---|
| Lines with several consumers | `gpiolib-shared.c` (core side, `CONFIG_GPIO_SHARED`); `gpio-shared-proxy.c` (the proxy chip, `CONFIG_GPIO_SHARED_PROXY`) | private header `gpiolib-shared.h` is shared by both; `gpio-aggregator.c` is a different job |
| Integer-based legacy calls | `gpiolib-legacy.c` | `devm_gpio_request_one()` is defined here, not in `gpiolib-devres.c`; `CONFIG_GPIOLIB_LEGACY` is `def_bool y` with no dependency, so the file is built whenever `CONFIG_GPIOLIB` is |
| Generic MMIO helper | `gpio-mmio.c` | no gpio-generic.c source: `gpio-generic.o` is only the composite object name in `drivers/gpio/Makefile`; the one exported entry point is `gpio_generic_chip_init()`, there is no bgpio_init() |
| KUnit tests | `gpiolib-kunit.c` | built by `CONFIG_GPIO_KUNIT`; there is no gpiolib-test.c |

**Headers by role**

- `include/linux/gpio.h`: declares nothing of its own; it only includes
  `include/linux/gpio/consumer.h` under `CONFIG_GPIOLIB` and
  `include/linux/gpio/legacy.h` under `CONFIG_GPIOLIB_LEGACY`.
- `include/linux/gpio/legacy.h`: holds the integer-API declarations
  (`gpio_request()`, `gpio_is_valid()`, `devm_gpio_request_one()`) and the
  flags `GPIOF_IN`, `GPIOF_OUT_INIT_LOW`, `GPIOF_OUT_INIT_HIGH`;
  `gpio_to_desc()` and `desc_to_gpio()` are in
  `include/linux/gpio/consumer.h`.
- Code that still uses the integer calls: the opening comment of
  `include/linux/gpio.h` tells it to include `<linux/gpio/legacy.h>`, not
  `<linux/gpio.h>`, and names all three replacements; a few files still
  include `<linux/gpio.h>`, for example `drivers/gpio/gpiolib-legacy.c`.
- `include/linux/gpio/legacy.h` in new code: its own opening comment says no
  new code should use it.
- include/linux/gpio/legacy-of-mm-gpiochip.h: does not exist; neither do
  struct of_mm_gpio_chip nor of_mm_gpiochip_add_data().
- `drivers/gpio/gpiolib-of.c`: has no `EXPORT_SYMBOL`; every OF entry point is
  declared in the private `drivers/gpio/gpiolib-of.h` for gpiolib itself.
- Controller-side OF hooks: members of `struct gpio_chip` in
  `include/linux/gpio/driver.h` under `CONFIG_OF_GPIO`: `of_gpio_n_cells`,
  `of_xlate` and `of_node_instance_match`.
- `include/linux/gpio/property.h`: the board-file header for software-node
  descriptions; it defines `PROPERTY_ENTRY_GPIO()` and no flag values.
- Flags passed to `PROPERTY_ENTRY_GPIO()`: `GPIO_ACTIVE_LOW` and the rest are
  `enum gpio_lookup_flags` in `include/linux/gpio/machine.h`, so a
  software-node board file includes both headers, as
  `drivers/gpio/gpiolib-kunit.c` does.
- `include/linux/gpio/machine.h`: lookup flags and lookup tables only; there
  is no struct gpiod_hog and no gpiod_add_hogs().
- `include/linux/gpio/generic.h` and `include/linux/gpio/regmap.h`: the
  headers for users of `drivers/gpio/gpio-mmio.c` and
  `drivers/gpio/gpio-regmap.c`; `generic.h` includes `driver.h` itself,
  `regmap.h` does not.
- `include/linux/gpio/defs.h`: defines `GPIO_LINE_DIRECTION_IN` and
  `GPIO_LINE_DIRECTION_OUT`; both `consumer.h` and `driver.h` include it, so a
  consumer does not need `driver.h` for them.

## Polarity and the integer interface

**Integer-based interface**

- `include/linux/gpio.h`: its opening comment says "This header *must not*
  be included"; for what it includes and what the comment names instead, see
  "Headers by role".
- `drivers/gpio/gpiolib-legacy.c`: defines `gpio_request()`,
  `gpio_request_one()`, `gpio_free()` and `devm_gpio_request_one()`;
  `drivers/gpio/gpiolib-devres.c` holds no integer call.
- `CONFIG_GPIOLIB_LEGACY`: `def_bool y` with no prompt and no dependency in
  `drivers/gpio/Kconfig`, so a `select` or `depends on` naming it gates
  nothing, and the `#ifdef CONFIG_GPIOLIB_LEGACY` guard in both
  `include/linux/gpio.h` and `include/linux/gpio/legacy.h` is always true.
- `CONFIG_GPIOLIB` off: `drivers/Makefile` does not enter `drivers/gpio/`, so
  `drivers/gpio/gpiolib-legacy.c` is not built; `include/linux/gpio/legacy.h`
  then supplies inline stubs.

| Call a reader reaches for | In this tree |
|---|---|
| gpio_request_array(), gpio_free_array() | absent |
| devm_gpio_request(), without flags | absent; `devm_gpio_request_one()` takes flags and is present |
| gpio_set_debounce() | absent; `gpiod_set_debounce()` on a descriptor |
| of_get_named_gpio(), of_get_gpio() | absent, as is the header include/linux/of_gpio.h |

- Device tree lookup: no call returns a GPIO number; consumers use the
  `gpiod_get()` family, or `fwnode_gpiod_get_index()` for another node.
- `of_gpio_count()`: exists only as an internal function of
  `drivers/gpio/gpiolib-of.c` taking a fwnode and a `con_id`; consumers call
  `gpiod_count()`.

**Logical and raw values**

- Descriptor flag names: `GPIOD_FLAG_ACTIVE_LOW`, `GPIOD_FLAG_OPEN_DRAIN` and
  `GPIOD_FLAG_OPEN_SOURCE` in `drivers/gpio/gpiolib.h`; there is no
  FLAG_ACTIVE_LOW.
- Open drain in `gpiod_set_value_nocheck()`: acts on the value after
  inversion; physical 1 switches the line to input, physical 0 drives it low.
- Open source in `gpiod_set_value_nocheck()`: the mirror image; physical 0
  switches the line to input, physical 1 drives it high.
- `gpiod_set_value_nocheck()`: tests only the flag bit, so it emulates by
  switching direction even where `gpiod_direction_output_nonotify()` had set
  open drain in hardware with `gpio_set_config()`.
- `gpio_direction_input()`: calls `gpiod_direction_input()`; there is no raw
  input call, and input direction carries no polarity.

**Device tree quirks**

- `of_find_gpio_rename()` entry: keyed by the `con_id` the driver asks for,
  plus `compatible` when not NULL; `legacy_id` is the property then parsed.
- `legacy_id` NULL in an `of_find_gpio_rename()` entry: the property is named
  exactly `con_id`, with no suffix.
- `of_gpio_try_fixup_polarity()` entry: `propname` is compared with
  `strcmp()` against the property name actually parsed.
- Renamed property: the polarity entry carries the legacy name, for example
  `"gpios-reset"` for `"himax,hx8357"`; a tree that uses `reset-gpios` gets no
  override from that entry.
- Suffix in a polarity entry: `reset-gpio` and `reset-gpios` are different
  keys; an entry covers only the one it spells.
- `of_gpio_set_polarity_by_property()`: when the boolean property is absent
  it forces `OF_GPIO_ACTIVE_LOW`, whatever the specifier says; it fits only a
  binding where that property is the sole source of polarity.
- `enable-active-high`: handled by entries of
  `of_gpio_set_polarity_by_property()`, not inline.
- Inline in `of_gpio_flags_quirks()`: `gpio-open-drain` for
  `"reg-fixed-voltage"`, `spi-cs-high` for `cs-gpios`, and
  `snps,reset-active-low`; each is guarded by `IS_ENABLED()` in a C `if`, not
  by `#if`.
- `of_find_gpio_quirks`: holds `of_find_gpio_rename()`,
  `of_find_trigger_gpio()` and, only under
  `IS_ENABLED(CONFIG_SND_SOC_MT2701_CS42448)`, `of_find_mt2701_gpio()`; there
  is no of_find_usb_gpio().
- `of_find_trigger_gpio()`: always in the array; it returns `-ENOENT` itself
  without `CONFIG_LEDS_TRIGGER_GPIO`.

**Initial state at request**

- `gpiod_configure_flags()`: calls `gpiod_direction_output_nonotify()`, not
  `gpiod_direction_output()`; the inversion is the first step there, before
  that function calls the chip.
- Kerneldoc of `enum gpiod_flags` in `include/linux/gpio/consumer.h`: says
  "drive them low" and "drive them high"; the value is logical all the same.
- First level driven: follows polarity only when polarity arrives in `lflags`,
  from the firmware or board-table lookup or a quirk of
  `drivers/gpio/gpiolib-of.c`.
- `GPIOD_FLAGS_BIT_NONEXCLUSIVE` with `-EBUSY` from `gpiod_request()`:
  `gpiod_find_and_request()` returns the descriptor without calling
  `gpiod_configure_flags()`, so this request's value and polarity are not
  applied.
- **Unsafe usage**: choosing `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH` by the
  voltage wanted on the pin, for a line whose lookup can carry
  `GPIO_ACTIVE_LOW`.
  - Safe: choose by state, `GPIOD_OUT_HIGH` for asserted, and keep that sense
    in later set calls, as `tsc200x_probe()` and `tsc200x_reset()` in
    `drivers/input/touchscreen/tsc200x-core.c` do;
    `gpiod_direction_output_nonotify()` applies `GPIOD_FLAG_ACTIVE_LOW` to
    the request value.
  - Safe: `GPIOD_OUT_LOW` for a reset line that must start released, as
    `ca8210_reset_init()` in `drivers/net/ieee802154/ca8210.c` does.
- **Potentially unsafe usage**: calling `gpiod_toggle_active_low()` after
  the request.
  - Unsafe: when the request passed `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH`; the
    line was already driven with the polarity from the lookup.
  - Safe: request with `GPIOD_ASIS`, toggle, then `gpiod_direction_output()`,
    as `matrix_keypad_init_gpio()` does for the column lines;
    `gpiod_toggle_active_low()` only flips `GPIOD_FLAG_ACTIVE_LOW` and does
    not drive the line.
  - Safe: on a line requested with `GPIOD_IN`, as `mmc_gpiod_request_cd()`
    does; nothing is driven.

**Working around wrong polarity**

- `of_gpio_try_fixup_polarity()` entry: `active_high` is the polarity that is
  enforced; the driver writes logical values in that sense.
- In-tree example: the `"cascoda,ca8210"` entry forces active low;
  `ca8210_reset_init()` requests with `GPIOD_OUT_LOW` and
  `ca8210_reset_send()` writes 1 then 0.
- `of_gpio_quirk_polarity()` logging: `pr_warn()` when it clears an
  active-low flag, `pr_info()` when it adds one, nothing when the tree agrees.
- Property name of the `of_gpio_try_fixup_polarity()` entry: see "Device tree
  quirks"; it must be the name the existing trees use.
- `Documentation/driver-api/gpio/consumer.rst`: names no case in which the raw
  accessors or `gpiod_toggle_active_low()` are permitted, and none in which
  they are forbidden.
- `Documentation/driver-api/gpio/consumer.rst` on raw accessors: "should be
  avoided as much as possible, especially by system-agnostic drivers".
- `Documentation/driver-api/gpio/consumer.rst` on the raw calls,
  `gpiod_is_active_low()` and `gpiod_toggle_active_low()` together: "should
  only be used with great moderation; a driver should not have to care about
  the physical line level or open drain semantics".
- `Documentation/driver-api/gpio/consumer.rst` does not mention bit-banging,
  MMC, or the quirks of `drivers/gpio/gpiolib-of.c`.
- In-tree callers of `gpiod_toggle_active_low()`: take polarity from a source
  the lookup does not carry, so a call to it is not in itself a defect.
  - Platform data on a descriptor made from a number: for example
    `gpio_led_get_legacy_gpiod()` and `gpio_keys_setup_key()`.
  - A separate property or host capability: for example
    `matrix_keypad_init_gpio()` reads `gpio-activelow`, and
    `mmc_gpiod_request_cd()` tests `MMC_CAP2_CD_ACTIVE_HIGH`.

## Requesting and using a line

**Finding a line**

- Board tables: `gpiod_find_and_request()` searches them only when its
  `platform_lookup_allowed` argument is true. `gpiod_get_index()` passes true.
- `fwnode_gpiod_get_index()` and `devm_fwnode_gpiod_get_index()`: pass false,
  so `-ENOENT` from the primary and secondary nodes is the final result.
- Firmware hit on a descriptor with `GPIOD_FLAG_SHARED`: the result is
  replaced by `-ENOENT` and the board tables are searched, for the fwnode-only
  getters too; see "Lines with several consumers".
- OF legacy names: `of_find_gpio_quirks[]` in `drivers/gpio/gpiolib-of.c`, run
  only after both suffixes gave `-ENOENT`.
  - The rename table is inside `of_find_gpio_rename()`; each entry is compiled
    in only under `IS_ENABLED()` of the consumer driver's symbol.
  - No quirk matches a NULL `con_id`.
- ACPI fallback to _CRS by index: only what `acpi_can_fallback_to_crs()`
  allows, which is a NULL `con_id` on an ACPI device with no properties and no
  `driver_gpios`. No quirk widens it.
- ACPI and `-ENOENT`: the property loop in `__acpi_find_gpio()` passes on only
  success and `-EPROBE_DEFER`; any other failure ends as `-ENOENT` when the
  _CRS fallback is not allowed.
- `acpi_find_gpio()`: returns `-ENOENT` for a GpioInt resource when the request
  flags equal `GPIOD_OUT_LOW` or `GPIOD_OUT_HIGH`.
  - With ACPI, `-ENOENT` (NULL from the optional getters) therefore does not
    prove that firmware has no entry.
- `-EPROBE_DEFER` has more sources than a missing controller:

  | Source | Also returned when |
  |---|---|
  | `of_get_named_gpiod_flags()` | a registered chip's `of_xlate` rejects the specifier; see `of_gpiochip_match_node_and_xlate()` |
  | `swnode_find_gpio()` | the referenced software node is not registered yet (`-ENOTCONN`) |
  | `gpio_desc_table_match()` | no chip has a label equal to `key`, or, with `chip_hwnum` equal to `U16_MAX`, no line is named `key` |
  | `gpiod_request()` | `try_module_get()` on the chip's owner fails |

- Property name buffer: `char propname[32]` in the OF, ACPI and swnode
  lookups. `for_each_gpio_property_name()` fills it with `snprintf()`, so a
  `con_id` longer than 25 characters is truncated silently.

**Lines with several consumers**

- `GPIOD_FLAGS_BIT_NONEXCLUSIVE`: still honoured, and still passed by many
  in-tree drivers, mostly under `drivers/regulator/`.
  - The only message is a `dev_info()` in `gpiod_find_and_request()` on each
    second request. Nothing rejects or warns about a new user.
  - On a line marked `GPIOD_FLAG_SHARED` the flag has no effect: each consumer
    gets its own proxy descriptor, so `gpiod_request()` does not return
    `-EBUSY`.
  - `drivers/regulator/fixed.c` passes the flag unconditionally and is correct
    in both configurations; `regulator_ena_gpio_request()` skips its search of
    `regulator_ena_gpio_list` for an entry with the same descriptor when
    `gpiod_is_shared()` is true.
- Configuration: `GPIO_SHARED` in `drivers/gpio/Kconfig` is `def_bool y` and
  `depends on HAVE_SHARED_GPIOS || COMPILE_TEST`. It has no prompt.
  - Only `ARCH_QCOM` in `arch/arm64/Kconfig.platforms` selects
    `HAVE_SHARED_GPIOS`.
  - `GPIO_SHARED_PROXY` is a separate tristate with `default m`.
- Scan: `gpio_shared_init()` is a `postcore_initcall()` and scans devicetree
  only. `gpio_shared_of_traverse()` takes only:
  - properties named by suffix (`-gpios`, `-gpio`, `gpios`, `gpio`); a legacy
    name of `of_find_gpio_rename()` without such a suffix is not scanned
  - specifiers with exactly two cells, whose target node has
    `gpio-controller`
  - nodes that are available, are not a `gpio-hog` and are not named
    `__symbols__`
- `gpiochip_setup_shared()`, at chip registration, for each line with more
  than one reference:
  - sets `GPIOD_FLAG_SHARED` on the real descriptor
  - requests the real line itself with label "shared", so any direct request
    of that line gets `-EBUSY`
  - creates one auxiliary device per reference, not one per line
- Lookup: `gpio_shared_add_proxy_lookup()` adds a board table whose `key` is
  the proxy chip's label. Until `drivers/gpio/gpio-shared-proxy.c` has bound
  and registered that chip, the consumer gets `-EPROBE_DEFER`.
- `gpio_shared_add_proxy_lookup()`: matches the consumer by fwnode pointer and
  by `con_id`. With no match it does `WARN_ON(1)` and returns `-ENOENT`.
- Proxy chip: `gpio_shared_proxy_probe()` sets `can_sleep` to true whatever the
  real chip is.
  - `gpiod_cansleep()` is true for every shared line.
  - A consumer must use the `_cansleep` value calls, from process context.
- Output value: a vote against `def_val`, not "high wins". See
  `gpio_shared_proxy_set_unlocked()`.
  - `def_val` is the value of the last `direction_output` made while the line
    had one user.
  - The real line is at the other value while at least one consumer asks for
    it, and returns to `def_val` when the last such vote is withdrawn.
  - `gpio_shared_proxy_free()` withdraws the vote of a consumer that releases
    the line.
- Direction with more than one user: `-EPERM` if the request differs from the
  real line's direction. With one user it is applied.
- Configuration with more than one user: `gpio_shared_proxy_set_config()`
  applies a differing value and logs a `dev_dbg()`. It does not refuse.
- `gpiod_get_value_cansleep()` on a proxy: reads the real line, not the
  consumer's own vote.
- `gpiod_is_shared()`: tests `GPIOD_FLAG_SHARED_PROXY`, which is set on the
  proxy's descriptor. `GPIOD_FLAG_SHARED` is on the real line, which consumers
  never hold.
- reset-gpio: the first `reset-gpios` reference to a line adds one placeholder
  reference in `gpio_shared_setup_reset_proxy()`; later ones add none.
  - `gpio_shared_dev_is_reset_gpio()` matches it to the reset-gpio device
    later, and is a stub that returns false without `CONFIG_RESET_GPIO`.
  - `gpio_shared_entry_is_really_shared()`: a line with two references, one of
    them the placeholder, is not shared.
- **Unsafe usage**: requesting a line marked `GPIOD_FLAG_SHARED` with no
  consumer device.
  - Unsafe: when the getter has no `struct device`, as with
    `fwnode_gpiod_get_index()`, which passes a NULL consumer;
    `gpio_shared_add_proxy_lookup()` passes it to `dev_name()`.
  - Safe: `devm_fwnode_gpiod_get_index()`, or `gpiod_get_index()` with a
    non-NULL `dev`; both pass the device as the consumer.

**Sleeping and atomic access**

- Plain value calls on one descriptor: the check is a bare
  `WARN_ON(desc->gdev->can_sleep)`, placed after `VALIDATE_DESC()`. They do
  not call `might_sleep()` or `might_sleep_if()`.
  - The warning fires on every call, not once; it needs `CONFIG_BUG` and no
    debug option.
- `_cansleep` value calls: call `might_sleep()` unconditionally, before
  `VALIDATE_DESC()`, so the context rule applies to a NULL descriptor too.
  - There is no extra_checks in this tree.
  - `might_sleep()` reports only under `CONFIG_DEBUG_ATOMIC_SLEEP`; without it
    `might_sleep()` reports nothing for a `_cansleep` call from atomic
    context.
- `gpiod_cansleep()`: returns `desc->gdev->can_sleep` after `VALIDATE_DESC()`.
  It does not call `gpiod_to_chip()`.
- Choosing per line: `create_gpio_led()` and `gpio_led_set()` in
  `drivers/leds/leds-gpio.c` store `gpiod_cansleep()` at probe and pick the
  call from it.
- Rejecting sleeping lines: `pwm_gpio_probe()` in `drivers/pwm/pwm-gpio.c`
  fails probe when `gpiod_cansleep()` is true.

**NULL and error descriptors**

- `validate_desc()`: has three results and never looks at the chip.
  - NULL: 0, no message.
  - Error pointer: `pr_warn()` with no stack trace, then `PTR_ERR(desc)`.
  - Anything else: 1.
- Removed chip, configuration calls: `gpio_do_set_config()` finds a NULL chip
  in `gpio_chip_guard` and returns `-ENODEV`; `validate_desc()` prints
  nothing for it. For the value calls see "Removing a chip in use".
- `gpiod_to_irq()` and `gpiod_get_direction()`: return `-EINVAL` for both NULL
  and an error pointer.
- `gpiod_cansleep()` and `gpiod_is_active_low()` on an error pointer: return
  the negative errno, which is true in a boolean test.
- `gpiod_to_chip()` and `gpiod_to_gpio_device()`: return NULL for NULL, and
  dereference an error pointer.
- Array value calls: return `-EINVAL` for a NULL `desc_array`, and test no
  element for NULL or an error pointer before dereferencing it.
- `devm_gpiod_put()` with NULL: no action was registered, so
  `devm_release_action()` hits its `WARN_ON()`. `devm_gpiod_unhinge()` accepts
  NULL and error pointers.
- `!CONFIG_GPIOLIB` stubs in `include/linux/gpio/consumer.h`: the direction
  and config stubs return `-ENOSYS` for any argument, NULL included; the value
  stubs return 0.
  - A driver that checks the return of `gpiod_direction_output()` on an
    optional line therefore fails when `CONFIG_GPIOLIB` is off.
- **Potentially unsafe usage**: passing the kept result of an optional request
  to a call that does not go through `validate_desc()`.
  - Unsafe: when the line may be absent and no NULL test precedes the call;
    `desc_to_gpio()`, `gpiod_hwgpio()` and `gpiod_is_shared()` dereference
    NULL, and `gpiod_put_array()` dereferences the NULL that
    `gpiod_get_array_optional()` returns.
  - Safe: after a NULL test, as `regulator_register()` tests
    `config->ena_gpiod` before `regulator_ena_gpio_request()` calls
    `gpiod_is_shared()`.

## Writing a chip driver

**Chip, device and descriptor**

- `gpiod_to_chip()` and `gpio_device_get_chip()`: take no SRCU lock; they
  return `rcu_dereference_check(gdev->chip, 1)`. The pointer is good only
  while the caller itself keeps `gpiochip_remove()` from running.
- SRCU-protected routes to the chip: `CLASS(gpio_chip_guard, guard)(desc)`
  from a descriptor; `guard(srcu)(&gdev->srcu)` plus `srcu_dereference()`
  from a `struct gpio_device`, as `gpio_device_find()` does.
- `gpio_devices_lock`: a mutex, taken by writers of `gpio_devices` only.
- Line label: `desc->label` is protected by `gdev->desc_srcu`, one SRCU
  domain per `struct gpio_device`, separate from `gdev->srcu`.
- `desc_set_label()`: frees the old label with `call_srcu()` and takes no
  lock of its own.
- `gpiod_get_label()`: the caller holds `gdev->desc_srcu`; chip drivers use
  `gpiochip_dup_line_label()`, which takes it and returns a copy.
- `desc->flags`: not only atomic bitops. `gpiod_get_direction()` and
  `gpiod_free_commit()` read the word with `READ_ONCE()`, change a local
  copy and store it with `WRITE_ONCE()`.
- `struct gpio_device` also holds `can_sleep`, copied from the chip at
  registration, and `data`, the driver pointer behind `gpiochip_get_data()`.

**Chip callbacks**

- `set` and `set_multiple` in `struct gpio_chip`: return `int`; the tree has
  no void setter and no set_rv member.

| Callback | Wrapper | Value outside the permitted set |
|---|---|---|
| `get` | `gpiochip_get()` | above 1: `gpiochip_warn()`, then becomes 1 |
| `get_multiple` | `gpio_chip_get_multiple()` | above 0: `-EBADE` |
| `set` | `gpiochip_set()` | above 0: `-EBADE` |
| `set_multiple` | `gpiochip_set_multiple()` | above 0: `-EBADE` |
| `direction_input` | `gpiochip_direction_input()` | above 0: `-EBADE` |
| `direction_output` | `gpiochip_direction_output()` | above 0: `-EBADE` |
| `get_direction` | `gpiochip_get_direction()` | above 1: `-EBADE` |

- `gpiochip_get()`: the only wrapper that keeps a bad value as success, and
  the only one that logs it.
- `-EBADE` conversions: silent in the wrapper, no `WARN_ON()` and no message.
- `WARN_ON()` in the wrappers: fires only when the callback pointer is NULL,
  and the wrapper returns `-EOPNOTSUPP`; `gpiochip_get()` has no such test,
  its caller `gpio_chip_get_value()` returns `-EIO`.
- `gpio_chip_get_multiple()` and `gpiochip_set_multiple()` without the
  multiple callback: loop over `gpiochip_get()` or `gpiochip_set()`, so the
  per-line handling above applies.
- Registration in `gpiochip_add_data_with_key()`: calls `gc->get_direction()`
  directly and stores `!ret`, so a negative errno or any other non-zero
  value marks the line as input; no `-EBADE`.

**Registering a chip**

- `gc->parent` NULL: accepted without a warning.
- `gc->label` NULL: `gdev->label` becomes `"unknown"`.
- `gdev->owner`: `gc->parent->driver->owner` when the parent is bound, else
  `gc->owner`, else `THIS_MODULE` of gpiolib; `gc->owner` is ignored when the
  parent has a driver.
- `gpiochip_get_ngpios()`: when `gc->ngpio` is 0, reads `"ngpios"` with
  `fwnode_property_read_u32()` from `gpiochip_choose_fwnode()`, so
  `gc->fwnode` wins over the parent's node, and writes the result to
  `gc->ngpio`.
- `gpiochip_get_ngpios()` read error other than `-ENODATA`: returned as it
  is, without the zero-lines message.
- `gc->names` and `"gpio-line-names"`: both are applied; each non-empty
  property string overrides the `gc->names` entry.
- `gpiochip_set_desc_names()`: stores the `gc->names[i]` pointers without
  copying, and warns only about a name already used on another chip.
- Hogs: `of_gpiochip_add()` applies none and the tree has no
  machine_gpiochip_add(); `gpiochip_hog_lines()` runs after
  `acpi_gpiochip_add()` for each child fwnode with `"gpio-hog"`, except an
  OF node already marked `OF_POPULATED`.
- Failing hog: `gpiochip_hog_lines()` returns the error and registration
  fails; a hog node with no state property only warns.
- `of_gpiochip_add()`: there is no of_gpio_simple_xlate(); the default is
  `of_gpio_twocell_xlate()`, or `of_gpio_threecell_xlate()` when
  `of_gpio_n_cells` is 3, which needs `of_node_instance_match` or fails with
  `-EINVAL`.
- First driver callback called: `init_valid_mask()`; the `get_direction()`
  loop comes after it and skips lines the mask excludes.
- `gpio_device_find()`: skips a device until `device_is_registered()` is
  true, so fwnode, OF, ACPI and label lookups cannot find the chip before
  `gpiochip_setup_dev()`, the last step.
- Reachable before `gpiochip_setup_dev()`, from list insertion on:
  `gpio_to_desc()` by number, `gpio_name_to_desc()` by line name, and
  `gc->dbg_show()` through debugfs in `gpiolib_seq_show()`; none of them
  tests `device_is_registered()`.
- Hogs and ACPI event interrupts (`acpi_gpiochip_request_interrupts()`):
  request lines and call the chip before a lookup through
  `gpio_device_find()` can.

**Removing a chip in use**

- `gpiochip_remove()`: has no test for requested lines and prints nothing
  about them; it returns `void`. Its kerneldoc says such a chip "may not be
  removed", but no code enforces that.
- Released by removal itself, while the chip is still set: lines requested
  through sysfs, flagged `GPIOD_FLAG_SYSFS` (`gpiochip_sysfs_unregister()`),
  hogs, and every interrupt requested on a line flagged
  `GPIOD_FLAG_USED_AS_IRQ`.
- `gpiochip_free_remaining_irqs()`: calls `free_irq()` on the consumers'
  behalf for each action on such a line.
- Order: `gdev->chip` is cleared and `synchronize_srcu(&gdev->srcu)` runs
  before `gpiochip_irqchip_remove()`, `acpi_gpiochip_remove()` and
  `of_gpiochip_remove()`; the character device goes last.
- `gpiod_get_value()` on a removed chip: returns `-ENODEV`; nothing is
  logged about the missing chip.
- `gpiod_set_value()` and the other setters: return `int`;
  `gpiod_set_raw_value_commit()` tests `GPIOD_FLAG_IS_OUT` before the chip,
  so a line not flagged output gives `-EPERM`, otherwise `-ENODEV`.
- Calls that never look at the chip still succeed, for example
  `gpiod_cansleep()`, `gpiod_is_active_low()` and
  `gpiod_set_consumer_name()`.
- `gpiod_free()` after removal: `gpiod_free_commit()` does nothing when
  `guard.gc` is NULL, so `gc->free()` is never called for a line still
  requested once `gdev->chip` is cleared; only the module and device
  references drop.
- `gpiochip_get_data()` after removal: `gpiochip_remove()` sets
  `gdev->data` to NULL after the SRCU wait, never clears `gc->gpiodev`, and
  then drops its reference, which may free the `struct gpio_device`.
- Driver code that runs after removal, such as its own IRQ handler or work
  item, therefore cannot use `gpiochip_get_data()` or `gc->gpiodev`.
- `irq_chip` callbacks: reached through the IRQ core, not through
  `gdev->srcu`; they can still run inside `gpiochip_remove()` after the
  `gpio_chip` callbacks have stopped.
- Domain added with `gpiochip_irqchip_add_domain()`:
  `gpiochip_irqchip_remove()` neither disposes its mappings nor removes it;
  whoever created the domain does, for example `regmap_del_irq_chip()`.

**Interrupt chip helpers**

- `IRQCHIP_IMMUTABLE` chip: `gpiochip_set_irq_hooks()` returns at once and
  gpiolib validates nothing in it; `const` is not required;
  `gpio_irq_chip_set_chip()` casts it away.
- `GPIOCHIP_IRQ_RESOURCE_HELPERS`: installs `gpiochip_irq_reqres()` and
  `gpiochip_irq_relres()`, the `struct irq_data` forms of
  `gpiochip_reqres_irq()` and `gpiochip_relres_irq()`.
- Flag names: `GPIOD_FLAG_USED_AS_IRQ` and `GPIOD_FLAG_IRQ_IS_ENABLED` in
  `drivers/gpio/gpiolib.h`; there is no FLAG_USED_AS_IRQ or
  FLAG_IRQ_IS_ENABLED.
- `gpiochip_enable_irq()` and `gpiochip_disable_irq()`: `WARN_ON()` and do
  nothing when the line lacks `GPIOD_FLAG_USED_AS_IRQ`, which
  `gpiochip_lock_as_irq()` sets, for example from the resource helpers or
  from `gpiochip_irq_domain_activate()`.
- Immutable chip that omits the resource helpers and the enable/disable
  calls, when nothing else calls `gpiochip_lock_as_irq()` for the line (a
  hierarchical domain does, in `gpiochip_irq_domain_activate()`):
  `GPIOD_FLAG_USED_AS_IRQ` is never set, so
  `gpiod_direction_output_nonotify()` does not refuse the line and
  `gpiochip_free_remaining_irqs()` skips it.
- Driver with `irq_enable` or `irq_disable`: `irq_enable()` and
  `__irq_disable()` in `kernel/irq/chip.c` call those instead of
  `irq_unmask` and `irq_mask`, so the gpiolib calls go there.
- Mutable chip, resource callbacks: filled in only when both are NULL; when
  the driver set either, nothing is logged about that and hooking continues.
- Mutable chip, hooks: two independent choices, never all four.
  `irq_disable` is wrapped if set, else `irq_mask`; `irq_enable` is wrapped
  if set, else `irq_unmask`.
- `gc->irq.irq_enable` already set by the driver: `WARN_ON()` and no enable,
  disable, mask or unmask hook is installed.
- Chained `parent_handler` with `gc->can_sleep`: refused only in
  `gpiochip_add_irqchip()`, which tests it only when `gc->irq.chip` is set.
- `gpiochip_irqchip_add_domain()`: has no `can_sleep` test; under
  `CONFIG_GPIOLIB_IRQCHIP` it returns `-EINVAL` only for a NULL domain.

## Helper libraries

**Generic MMIO helper**

- Older names: bgpio_init(), the BGPIOF_ flags and the bgpio_ fields of
  `struct gpio_chip` are defined nowhere in this tree, and there are no
  compatibility wrappers.
- `CONFIG_GPIO_GENERIC`: has no prompt, so drivers `select` it; there is no
  GPIO_MMIO symbol.
- `CONFIG_GPIO_GENERIC_PLATFORM`: guards the `basic-mmio-gpio` platform driver
  inside `drivers/gpio/gpio-mmio.c`; the library part of the file is built
  without it.
- Lock argument: the lock macros and both guard classes in
  `include/linux/gpio/generic.h` take the `struct gpio_generic_chip *`, not
  the address of its `lock` member.
- `gpio_generic_lock` and `gpio_generic_lock_irqsave`: guard class names for
  `guard()` and `scoped_guard()`, not functions.
- `gpio_generic_chip_lock()`, `gpio_generic_chip_unlock()`,
  `gpio_generic_chip_lock_irqsave()`, `gpio_generic_chip_unlock_irqrestore()`:
  macros; the irqsave pair takes `flags` as a second argument.
- Examples: `drivers/gpio/gpio-dwapb.c` uses the guards and
  `drivers/gpio/gpio-grgpio.c` also uses the macro pairs.

**Generic MMIO initialisation**

- `cfg->dat`: required in every configuration, also for an output-only chip
  that gives `set`; `gpio_mmio_setup_io()` returns `-EINVAL` without it.
- `cfg->sz`: the register width in bytes, given by the caller; only
  `gpio_mmio_pdev_probe()` derives it from the size of the `dat` resource.
- Byte order: the one refusal is 64-bit registers with
  `GPIO_GENERIC_BIG_ENDIAN_BYTE_ORDER`; 8-bit registers ignore the flag.
- `gc.ngpio`: a nonzero value set before the call is kept; otherwise the
  `ngpios` property is read, and only if that fails is it `sz * 8`. See
  `gpiochip_get_ngpios()` in `drivers/gpio/gpiolib.c`.
- `gc.parent`, `gc.label`, `gc.base`, `gc.request`: assigned unconditionally,
  so a value set before the call is lost; override after the call, as
  `spacemit_gpio_add_bank()` does.
- `gc.get_direction`: set only when `dirout` or `dirin` is given.
- `sdata`: read from `dat`, then re-read from `set` when `set` is given
  without `clr` and `GPIO_GENERIC_UNREADABLE_REG_SET` is clear.
- `GPIO_GENERIC_READ_OUTPUT_REG_SET`: selects the `get` callback and plays no
  part in the initial `sdata`.
- `struct gpio_generic_chip` must be zeroed before the call: `reg_dir_out`,
  `reg_dir_in`, `pinctrl`, `dir_unreadable` and `sdir` are written only when
  the matching register or flag is given, and read later.

**Controllers with several banks**

- `of_gpio_threecell_xlate()`: `static` in `drivers/gpio/gpiolib-of.c`, so a
  driver cannot install it by name.
- `of_node_instance_match`: a callback in `struct gpio_chip`, not a number;
  there is no of_node_instance_id field.
- Cells: cell 0 is passed to `of_node_instance_match`, cell 1 is the line and
  is the one compared with `ngpio`, cell 2 is the flags.

| Arrangement | What the driver sets after `gpio_generic_chip_init()` | Example |
|---|---|---|
| one node, three cells | `of_gpio_n_cells = 3`, `of_node_instance_match`, no `of_xlate` | `spacemit_gpio_add_bank()` in `drivers/gpio/gpio-spacemit-k1.c` |
| one node, two cells, lines numbered across banks | own `of_xlate` that fails for other banks' lines, and `gc.offset` | `brcmstb_gpio_of_xlate()`, `mt7621_gpio_xlate()` |
| one child node per bank | `gc.fwnode` to the child node, and `gc.ngpio` | `dwapb_gpio_add_port()` in `drivers/gpio/gpio-dwapb.c` |

- `spacemit_of_node_instance_match()`: the only implementation of the callback
  in this tree.
- Other chips with `of_gpio_n_cells = 3` install their own `of_xlate`, for
  example `drivers/pinctrl/sunxi/pinctrl-sunxi.c`.
- Child node per bank: the helper reads `ngpios` before the driver has set
  `gc.fwnode`, so from the parent's node; the driver sets `gc.ngpio` itself.
- `gpio-ranges` on a three-cell chip: parsed with four cells, the first being
  the instance; see `of_gpiochip_add_pin_range()`.
- Interrupts: the domain from `gpiochip_simple_create_domain()` picks the bank
  with the same callback, in `gpiochip_irq_select()` in
  `drivers/gpio/gpiolib.c`; the hierarchical domain has no `select`.
- Three-cell interrupt specifier: `irq_domain_translate_twothreecell()` takes
  cell 1 as the hwirq.

**Regmap helper**

- Refused with `-EINVAL`: `reg_dir_in_base` or `reg_dir_out_base` set while
  either `reg_dat_base` or `reg_set_base` is 0.
- Refused with `-EINVAL`: `reg_dir_in_base` and `reg_dir_out_base` both set.
- `reg_clr_base`: no refusal in `gpio_regmap_register()` involves it; without
  `reg_set_base` it is ignored.
- `config->regmap`: never tested and never looked up from the parent; a NULL
  one is dereferenced by `regmap_might_sleep()`.
- `ngpio` of 0: not refused as such; `gpiochip_get_ngpios()` reads `ngpios`,
  and its error code is what registration returns.
- `ngpio_per_reg` left 0: becomes `config->ngpio`, not the count read from the
  `ngpios` property.
- **Unsafe usage**: leaving `ngpio` and `ngpio_per_reg` both 0 with the default
  translation; `gpio_regmap_simple_xlate()` divides by `ngpio_per_reg`.
  - Safe: set `ngpio` in the config, as `sl28cpld_gpio_probe()` does;
    `ngpio_per_reg` then takes that value.

**Regmap translation callback**

- `reg_mask_xlate`: takes six parameters; the second is an
  `enum gpio_regmap_operation`, before `base`. A five-parameter callback does
  not match the type in `struct gpio_regmap_config`.
- Operation passed: `GPIO_REGMAP_GET_OP` from `gpio_regmap_get()`,
  `GPIO_REGMAP_SET_OP` from both set paths, `GPIO_REGMAP_GET_DIR_OP` and
  `GPIO_REGMAP_SET_DIR_OP` from the direction paths.
- Use of the operation: it tells the cases apart when several bases are the
  same register; see `rtd1625_reg_mask_xlate()` in
  `drivers/gpio/gpio-rtd1625.c`.
- `value_xlate`: a second, optional callback in `struct gpio_regmap_config`;
  it runs after `reg_mask_xlate` on the set and set-direction paths and may
  change the mask and the value to be written;
  `gpio_regmap_set_with_clear()` writes only the mask.

## Model gaps

### Other mistakes models make

- Models take a set on any requested line to reach the chip. A set on a line
  whose `GPIOD_FLAG_IS_OUT` is clear returns `-EPERM`, on a live chip too; see
  `gpiod_set_raw_value_commit()`. `gpiod_set_value()` and
  `gpiod_set_value_cansleep()` on an open-drain or open-source line skip that
  test; the array calls do not.
- Models limit the range check to value and direction callbacks. A positive
  return from `request()` or `set_config()` also becomes `-EBADE`; `to_irq()`
  returning 0 becomes `-ENXIO`.
- Models take the `enum gpiod_flags` a consumer passes to be what is applied.
  On ACPI, when `acpi_gpio_to_gpiod_flags()` returns other than `GPIOD_ASIS`
  for the resource, `acpi_gpio_update_gpiod_flags()` replaces direction and
  value from the resource unless `ACPI_GPIO_QUIRK_NO_IO_RESTRICTION` is set.
- Models take `gpiod_set_value()`, `gpiod_set_value_cansleep()`,
  `gpiod_set_raw_value()` and `gpiod_set_raw_value_cansleep()` to be void, as
  `Documentation/driver-api/gpio/consumer.rst` still prints. All four return
  `int` in `include/linux/gpio/consumer.h`.
- Models take a requested line to make `gpiochip_remove()` fail, as the
  comment above `gpiod_get_raw_value_commit()` in `drivers/gpio/gpiolib.c`
  still says. `gpiochip_remove()` returns `void` and has no early return.
- Models let a driver assign `of_gpio_twocell_xlate()` to `of_xlate`. It is
  `static` in `drivers/gpio/gpiolib-of.c`; `of_gpiochip_add()` installs it
  on a chip with an OF node when `of_xlate` is NULL and `of_gpio_n_cells` is
  not 3.
