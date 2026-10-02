# Questions: GPIO Subsystem

- guide: gpio.md
- title: GPIO Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/gpio-measurement.md` is the
wider set the readers were measured on and `catalogue/gpio-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## gpio.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## gpio.core-files: Core files

- section: Finding your way
- relevance: 4 - the files nobody guesses

A table and nothing else, job to file under `drivers/gpio/`: the ACPI lookup and its quirks;
lines with several consumers; the integer-based legacy calls; the generic MMIO helper; the regmap
helper; the KUnit tests. Where a reader is likely to look for a file that does not exist in this
tree, say so in the row.

## gpio.headers: Headers by role

- section: Finding your way
- relevance: 5 - the first thing checked in any patch that touches GPIOs

Which header does a GPIO controller driver, a consumer and a board file that describes lines
each include? What is `include/linux/gpio.h` in this tree and may new code include it, and
where a reader expects a separate header for the device tree GPIO calls, what is there instead?
Start from `include/linux/gpio/`.

# Polarity and the integer interface

## gpio.legacy-api: Integer-based interface

- section: Polarity and the integer interface
- relevance: 5 - new uses of it are refused and readers misremember what is left

Where does the integer-based GPIO interface live in this tree: header, source file and
configuration symbol? Of the calls a reader is likely to reach for (requesting an array of
GPIOs, the managed request that takes no flags, setting debounce by number, the device tree
calls that return a GPIO number), which are gone? Start from `include/linux/gpio/legacy.h`.

## gpio.logical-and-raw: Logical and raw values

- section: Polarity and the integer interface
- relevance: 5 - converting a driver from one interface to the other silently inverts lines

Which consumer calls act on the logical value of a line and which on the physical level, and
what besides polarity does the logical set-value path apply? Which of the two do the
integer-based value and direction calls turn into, and what therefore changes, when a driver is
converted to descriptors, for a line whose firmware description marks it active low? Start from
`gpiod_set_value_nocheck()`.

## gpio.of-quirks: Device tree quirks

- section: Polarity and the integer interface
- relevance: 5 - where a binding that got polarity or naming wrong is fixed up

For correcting the polarity of a line and for accepting an old property name, which mechanism of
`drivers/gpio/gpiolib-of.c` is used when, and what is each one's entry keyed by? How is an entry
kept out of kernels that do not build the driver concerned? Start from `of_gpio_flags_quirks()`
and `of_find_gpio_quirks`.

## gpio.request-flags: Initial state at request

- section: Polarity and the integer interface
- relevance: 4 - the wrong constant asserts a reset line during probe

Is the initial output value named by the `enum gpiod_flags` constants passed to `gpiod_get()` a
logical or a physical level, and at which point on the way to the chip is polarity applied to it?
What are the requirements for choosing between `GPIOD_OUT_LOW` and `GPIOD_OUT_HIGH` for a reset or
enable line in order to assure safe usage? Start from `gpiod_configure_flags()`.

## gpio.polarity-workarounds: Working around wrong polarity

- section: Polarity and the integer interface
- relevance: 5 - the usual mistake when a legacy driver is converted

A driver is being converted to descriptors and existing device trees carry a polarity flag that
disagrees with how the driver has always driven the line. Where does the tree correct such a
polarity, and what does that require of the driver? What does
`Documentation/driver-api/gpio/consumer.rst` say about when a driver may use the raw accessors and
`gpiod_toggle_active_low()`? Start from `Documentation/driver-api/gpio/consumer.rst` and
`of_gpio_try_fixup_polarity()`.

# Requesting and using a line

## gpio.lookup-order: Finding a line

- section: Requesting and using a line
- relevance: 4 - the error code decides between probe deferral and a missing line

When a consumer asks for a line by function name, in what order are the device's firmware node,
its secondary node and the board lookup tables consulted, and which property names are tried for
a given function name? Which error comes back when nothing describes the line, as opposed to
when the controller is not registered yet? Start from `gpiod_find_and_request()` and
`gpio_suffixes`.

## gpio.shared-lines: Lines with several consumers

- section: Requesting and using a line
- relevance: 4 - the old flag is deprecated and the replacement is new

How does this tree let two devices use one GPIO line: what is the status of the request flag
that allowed a second request of a busy line, what does gpiolib do on its own, and under which
configuration, when firmware shows a line referenced by several consumers, and what does a
consumer driver have to do differently? Start from `drivers/gpio/gpiolib-shared.c` and
`GPIOD_FLAGS_BIT_NONEXCLUSIVE`.

## gpio.sleeping-access: Sleeping and atomic access

- section: Requesting and using a line
- relevance: 4 - the wrong variant warns at run time, not at build time

What happens when the plain value calls are used on a line of a chip whose accessors may sleep,
what do the calls with cansleep in their name check, and how does a consumer that can run in
either context choose? Start from `gpiod_get_value()` and `gpiod_cansleep()`.

## gpio.null-and-error-descs: NULL and error descriptors

- section: Requesting and using a line
- relevance: 4 - decides whether an optional line needs a NULL check at every use

What do the optional request calls return when no line is described, and what do the value,
direction and configuration calls do when handed a NULL descriptor or an error pointer? What are
the requirements for a driver that keeps the result of `gpiod_get_optional()` in order to assure
safe usage? Start from `validate_desc()` in `drivers/gpio/gpiolib.c`.

# Writing a chip driver

## gpio.objects: Chip, device and descriptor

- section: Writing a chip driver
- relevance: 5 - which object outlives which decides what a pointer may be used for

What do `struct gpio_chip`, `struct gpio_device` and `struct gpio_desc` each represent, and
which of them outlives the driver that registered the chip? How does gpiolib code get from a
descriptor to the chip safely while the chip may be going away, and what protects the list of
devices and a line's label? Start from `drivers/gpio/gpiolib.h` and `gpiochip_remove()`.

## gpio.chip-callbacks: Chip callbacks

- section: Writing a chip driver
- relevance: 4 - the prototypes have changed and gpiolib now polices the return values

What do the `struct gpio_chip` callbacks that read, write and set the direction of lines return
in this tree, and which values is each permitted to return? What does gpiolib do with a value
outside that set, and is that the same in every wrapper? Start from `gpiochip_get()`,
`gpiochip_set()` and `gpiochip_get_direction()` in `drivers/gpio/gpiolib.c`.

## gpio.chip-registration: Registering a chip

- section: Writing a chip driver
- relevance: 4 - what a new driver's probe function is checked against

What does registering a `struct gpio_chip` refuse, default or warn about in what the driver
filled in, and where can the number of lines come from when the driver leaves it zero? By which
point in registration can consumers, hogs and userspace reach the chip's callbacks, and what
must the driver therefore have ready before the call? Start from
`gpiochip_add_data_with_key()`.

## gpio.chip-removal: Removing a chip in use

- section: Writing a chip driver
- relevance: 4 - decides what a driver may free in its remove path

When a chip is removed while consumers still hold descriptors or userspace has the character
device open, what do later consumer calls return, and what may the driver's callbacks and its
remove path assume once removal returns? Does removal check or warn that lines are still
requested? Start from `gpiochip_remove()` and `gpio_chip_guard`.

## gpio.irqchip: Interrupt chip helpers

- section: Writing a chip driver
- relevance: 4 - the immutable form is required of new drivers

For a GPIO driver that delivers interrupts through `struct gpio_irq_chip`, what must an
immutable `struct irq_chip` contain and call from its mask and unmask callbacks, what does the
core do when the irq_chip is not marked immutable, and which combination of a chained handler
and a sleeping chip is refused? Start from `gpiochip_add_irqchip()` and
`gpiochip_set_irq_hooks()`.

# Helper libraries

## gpio.generic-mmio: Generic MMIO helper

- section: Helper libraries
- relevance: 5 - the interface reviewers ask new drivers to use has been renamed

What does this tree call the interface of the generic MMIO helper for memory-mapped registers
with one bit per line: configuration symbol, header, chip structure, initialisation function and
the prefix of its flags, where a reader's memory offers older names? How does a driver take the
helper's lock? Start from `include/linux/gpio/generic.h` and `drivers/gpio/gpio-mmio.c`.

## gpio.generic-mmio-init: Generic MMIO initialisation

- section: Helper libraries
- relevance: 5 - drivers repeat what the helper already sets, or leave out what it needs

Which register must a driver give the generic MMIO initialisation, and which register widths and
byte orders does it refuse? What does it fill in on its own that a driver need not repeat, and
what is left for the driver to do afterwards? Start from `gpio_generic_chip_init()`.

## gpio.banked-controllers: Controllers with several banks

- section: Helper libraries
- relevance: 4 - how more lines than one register holds are fitted to the helper

When a controller has more lines than fit in one register, how can a driver that uses the generic
MMIO helper describe the banks to gpiolib and to the device tree? What does
`of_gpio_threecell_xlate()` require to be set in `struct gpio_chip`, and can a driver install that
function itself? Name an in-tree driver for each arrangement. Start from
`of_gpio_threecell_xlate()`.

## gpio.regmap-helper: Regmap helper

- section: Helper libraries
- relevance: 5 - the second helper reviewers ask for, with rules about its register bases

Which combinations of register bases does the GPIO regmap helper's registration code itself
refuse, as opposed to those only a comment forbids, and how is a register base of zero
expressed? Start from `include/linux/gpio/regmap.h` and `gpio_regmap_register()`.

## gpio.regmap-xlate: Regmap translation callback

- section: Helper libraries
- relevance: 4 - nobody gave the callback's arguments, and the default is not callable

What does the GPIO regmap helper's translation callback receive and return, and can a driver
call the default translation function directly? Start from `gpio_regmap_register()`.

# Model gaps

## gpio.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
