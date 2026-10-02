# What the gpio measurement found

Three models were asked the 26 questions in `gpio-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C said they were
describing kernels 6.12 to 6.19, reader B 6.9 to 6.12. The hand-written guide
was never checked against current sources, so differences between it and the
built guide are expected and are noted below.

## What all three readers got wrong

- **`include/linux/gpio.h` is not where the integer-based calls live.** All
  three called it the legacy header that declares them. Its comment says it
  "must not be included", and it declares nothing: it pulls in `consumer.h`
  under `CONFIG_GPIOLIB` and `include/linux/gpio/legacy.h` under
  `CONFIG_GPIOLIB_LEGACY`. The declarations and the stubs are in `legacy.h`.
  Readers B and C said they did not recognise `legacy.h`; readers A and C said
  include/linux/of_gpio.h and of_get_named_gpio() still exist. Neither does.
- **There is a KUnit suite**, `drivers/gpio/gpiolib-kunit.c` under
  `CONFIG_GPIO_KUNIT`. Every reader said there was none or left it out.
- **Registration order and hogs.** All three named machine_gpiochip_add(),
  which is not in the tree, and had `of_gpiochip_add()` adding device tree
  hogs. Hogs of every firmware kind are added by `gpiochip_hog_lines()` after
  `acpi_gpiochip_add()`; `gpiochip_setup_shared()` runs before the character
  device is set up, and nobody listed it. Only `ngpio` is checked at
  registration; a missing label becomes "unknown".
- **Regmap helper.** The `reg_mask_xlate` callback takes an
  `enum gpio_regmap_operation` after the first argument; nobody gave it.
  `gpio_regmap_register()` enforces three rules: at least one of
  `reg_dat_base` and `reg_set_base` is given, a direction base needs both of
  them, and the two direction bases may not be given together. The rest are
  only in the header comment.
  `gpio_regmap_simple_xlate()` is static, so a driver cannot call it.
- **Generic MMIO helper.** `gpio_generic_chip_init()` already sets the parent,
  the label, a base of -1 and the line count (from "ngpios", else the register
  width); readers A and C had the driver doing that, reader B had fields that
  do not exist. `dat` is required and doubles as the output register when no
  `set` is given. 64-bit registers work only on 64-bit kernels and not with
  big-endian byte order.
- **Who calls `gpiod_toggle_active_low()`.** Reader A named the SPI core,
  which never calls it; reader B called it the documented fix for a backwards
  binding; reader C said only subsystem cores use it. The callers are a handful
  of drivers that honour a separately supplied inversion (gpio_keys,
  leds-gpio, matrix_keypad, the MMC slot helpers, pcmcia soc_common), and the
  documentation says "with great moderation".
- The initial value in `enum gpiod_flags` reaches the chip through
  `gpiod_direction_output_nonotify()`, which is where the active-low inversion
  is applied. The stubs for kernels without the character device are in
  `drivers/gpio/gpiolib.c`, not in `gpiolib-cdev.h`.

## What readers A and B got wrong as well

- **Callback return values.** Reader B had `set` returning void beside a
  set_rv member; there is no set_rv, and `set` returns int. Reader A had every
  wrapper warn and return `-EBADE`. In the code `gpiochip_get()` warns and
  clamps a value above 1 to 1, the set, multiple and direction wrappers turn a
  positive return into `-EBADE` silently, and `gpiochip_get_direction()` does
  the same for anything but the two direction constants.
- **Descriptor state bits** are `GPIOD_FLAG_*` in `drivers/gpio/gpiolib.h`;
  both wrote FLAG_*.
- **Lines with several consumers.** Reader A was unsure of every name, reader
  B denied the mechanism exists. `drivers/gpio/gpiolib-shared.c` scans the
  device tree, `gpiochip_setup_shared()` creates a proxy per consumer when the
  chip registers, `GPIO_SHARED` follows `HAVE_SHARED_GPIOS` (one platform
  selects it), and `GPIOD_FLAGS_BIT_NONEXCLUSIVE` is marked deprecated.
- **Device tree quirks.** Reader B described `of_find_gpio_quirks` as a table
  of polarity entries; it is an array of lookup functions for old property
  names. Reader A had the flag quirks run on every lookup and misquoted the
  log lines.
- Reader A said `gpiochip_remove()` warns when lines are still requested. Only
  its comment says so; the code has no such check.
- Reader A said the board lookup flags have the same values as the device tree
  ones. `GPIO_OPEN_DRAIN` and `GPIO_OPEN_SOURCE` differ, and
  `of_convert_gpio_flags()` translates.

## What reader B got wrong alone

Reader B is a few releases behind and it shows in whole mechanisms:

- `gpiod_set_value()` returns void and only logs. It returns int: `-EPERM`
  when the line is not an output, `-ENODEV` when the chip is gone.
- To keep old behaviour when converting a driver, use the raw accessors. The
  opposite of what the documentation says, and the one answer here that would
  turn a review verdict round.
- A gpio_lock spinlock protects the device list, the flags and the labels, and
  the device is counted by a kref. There is no gpio_lock: the list is
  `gpio_devices_lock` with `gpio_devices_srcu`, the chip pointer is
  `gdev->srcu` through `gpio_chip_guard`, labels are `desc_srcu`, and the
  count is the embedded `struct device`.
- BGPIOF_ flag names for the MMIO helper (now `GPIO_GENERIC_*`),
  gpiolib-acpi.c (now `gpiolib-acpi-core.c` and `gpiolib-acpi-quirks.c`),
  devm_gpio_request() and gpio_set_debounce() still present, and
  `gpio_direction_output()` mapping to the logical call (it maps to
  `gpiod_direction_output_raw()`).
- The cansleep calls "skip the check". They call `might_sleep()`; the plain
  ones only `WARN_ON()` and carry on.

## What the readers already knew

Readers A and C answered these with little or nothing to correct: the three
objects and which outlives which, logical against raw values and what a
conversion from the integer calls changes, sleeping and atomic access, what a
NULL descriptor does, removal of a chip that is in use, the order of lookups,
the names in the generic MMIO helper, and the immutable irq_chip rules. Reader
C also had the shared-line mechanism and the device tree quirk tables nearly
right.

## Where the hand-written guide is stale

- It calls `<linux/gpio.h>` the legacy header that is being replaced. In this
  tree that file is a shim that says it must not be included, and the legacy
  interface has its own header, `<linux/gpio/legacy.h>`, behind
  `CONFIG_GPIOLIB_LEGACY`. More files include `legacy.h` than `gpio.h` now.
- It says the library applies polarity inversion when a device tree handle is
  tagged `GPIO_ACTIVE_HIGH`. Active high is zero and inverts nothing; the flag
  that matters is `GPIO_ACTIVE_LOW`. It also never says why a conversion
  changes behaviour: the integer calls map to the raw descriptor calls.
- `of_gpio_try_fixup_polarity()` is there, but it is one of three mechanisms
  in `drivers/gpio/gpiolib-of.c` (a polarity taken from a separate boolean
  property, and old property names, are the others), it is static, and every
  entry sits inside `#if IS_ENABLED()` for its driver.
- For the two helper libraries it gives the configuration symbol and the
  header and nothing a reader could search for. It says the regmap library
  "has a function to translate" an offset; that is a callback the driver may
  supply, and the default is not callable from a driver.
- It is written as advice to give ("recommend that", "do not recommend"). A
  built guide says how the code is used and leaves the verdict to the reader.

## What was left out of the build set and why

The build set has 10 of the 26 questions and 515 words of budget. The
hand-written guide is 435 words, under the 600-word floor for a built guide, so
the set is sized to 600 words (480 to 720) with no question budgeted under 40.
The first cut, nine questions and 335 words held to the 435, left 20 to 50
words an answer for questions that each ask for half a dozen things, and the
answers came out as fragments that needed the question beside them. Kept from
the first cut: the four things the old guide was about (the headers and the
legacy interface, wrong polarity and the quirk tables, the MMIO helper with
its banks, the regmap helper), because those are what the guide is loaded for
and every reader got part of each wrong, with the callback return values and a
pointer to the files nobody guessed. Most of the larger size went to those
nine, so that each thing a question asks for gets a sentence of its own. Added
with what was left:

- `gpio.shared-lines`: reader A was unsure of every name and reader B denied
  the mechanism exists, and a reader who does not know it has only the
  deprecated request flag to offer a driver that shares a line.

Left out:

- `gpio.chip-registration`, `gpio.irqchip`: real gaps, the first for two
  readers, but each needs sixty words or more to say anything, and what the
  readers got wrong about registration is the order of the steps inside
  gpiolib, which a driver patch does not depend on. They are the first to
  bring back if the guide is allowed to grow again.
- `gpio.objects`, `gpio.logical-and-raw`, `gpio.sleeping-access`,
  `gpio.null-and-error-descs`, `gpio.chip-removal`, `gpio.lookup-order`:
  two of three readers already answer them. What reader B lacks there would
  need most of the guide.
- `gpio.flag-namespaces`, `gpio.request-flags`, `gpio.set-value-errors`,
  `gpio.board-descriptions`: one or two corrections each, of detail.
- `gpio.docs-and-tests`, `gpio.userspace-abi`, `gpio.core-locking`,
  `gpio.change-checklist`: about changing gpiolib itself, which few patches
  do. The KUnit file is in the pointer.

They stay in the measurement set.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A           61        33%      6     10   6.12 to 6.18
reader-B           82        77%      0     25   6.9 to 6.12
reader-C           59        21%      8      3   6.12 to 6.19

question                       reader-A      reader-B      reader-C   verdict
gpio.core-files                 7% ( 4)      28% ( 7)       6% ( 2)   middling
gpio.headers                   40% ( 4)      75% ( 2)      36% ( 4)   weak: reader-A, reader-B
gpio.docs-and-tests            37% ( 2)      63% ( 2)      32% ( 3)   weak: reader-B
gpio.objects                    0% ( 0)      75% ( 5)       6% ( 2)   weak: reader-B
gpio.flag-namespaces           11% ( 1)      48% ( 2)      19% ( 1)   weak: reader-B
gpio.legacy-api                33% ( 3)      91% ( 5)      37% ( 2)   weak: reader-B
gpio.chip-callbacks            33% ( 2)      82% ( 4)      42% ( 2)   weak: reader-B, reader-C
gpio.logical-and-raw            6% ( 1)      81% ( 5)       8% ( 2)   weak: reader-B
gpio.request-flags             26% ( 3)      75% ( 2)      20% ( 2)   weak: reader-B
gpio.null-and-error-descs      17% ( 2)      76% ( 1)      21% ( 3)   weak: reader-B
gpio.sleeping-access            0% ( 0)      86% ( 1)       0% ( 0)   weak: reader-B
gpio.set-value-errors          59% ( 3)      83% ( 1)      22% ( 2)   weak: reader-A, reader-B
gpio.lookup-order              41% ( 2)      84% ( 5)      20% ( 1)   weak: reader-A, reader-B
gpio.of-quirks                 53% ( 2)      83% ( 2)       0% ( 0)   weak: reader-A, reader-B
gpio.polarity-workarounds      43% ( 1)      79% ( 1)      35% ( 3)   weak: reader-A, reader-B
gpio.shared-lines              88% ( 3)      91% ( 1)      32% ( 5)   weak: reader-A, reader-B
gpio.board-descriptions        38% ( 1)      84% ( 1)      21% ( 2)   weak: reader-B
gpio.chip-registration         72% ( 4)      89% ( 5)      16% ( 4)   weak: reader-A, reader-B
gpio.chip-removal              21% ( 1)      87% ( 5)       6% ( 0)   weak: reader-B
gpio.generic-mmio              46% ( 4)      83% ( 7)      22% ( 3)   weak: reader-A, reader-B
gpio.banked-controllers        39% ( 3)      79% ( 2)       6% ( 1)   weak: reader-B
gpio.regmap-helper             38% ( 3)      69% ( 4)      48% ( 2)   weak: reader-B, reader-C
gpio.irqchip                   29% ( 2)      87% ( 3)      17% ( 1)   weak: reader-B
gpio.userspace-abi             42% ( 2)      74% ( 2)       3% ( 1)   weak: reader-A, reader-B
gpio.core-locking              10% ( 2)      88% ( 4)      34% ( 5)   weak: reader-B
gpio.change-checklist          53% ( 6)      77% ( 3)      60% ( 6)   all weak
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `gpio.chip-registration`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `gpio.objects`, `gpio.logical-and-raw`, `gpio.request-flags`, `gpio.null-and-error-descs`, `gpio.sleeping-access`, `gpio.lookup-order`, `gpio.chip-removal`, `gpio.irqchip`.

## Questions reorganised

- Subjects now: polarity and the integer interface; requesting and using a line; writing a chip
  driver; helper libraries. Every question names its subject as its section. 21 questions became 23.
- Split, being checklists: `gpio.generic-mmio` into itself (names) and `gpio.generic-mmio-init`;
  `gpio.regmap-helper` into itself and `gpio.regmap-xlate`.
- Asked twice, now once: what the integer calls map to (`gpio.logical-and-raw`, out of
  `gpio.legacy-api`); what keeps memory alive (`gpio.objects`, out of `gpio.chip-removal`).
- Dropped as inventory: the order of steps inside registration, the lookup flags folded in at
  request, how a chip declares that it may sleep. No whole question was dropped.
