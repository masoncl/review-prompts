# Questions: GPIO (measurement set)

- guide: gpio.md
- title: GPIO Subsystem

A wide set of questions about gpiolib under `drivers/gpio/` and the headers in
`include/linux/gpio/`: the chip, device and descriptor objects, the consumer
calls and what they return, how a line is looked up from device tree, ACPI,
software nodes and board tables, the polarity quirks, what is left of the
integer-based interface, registering and removing a chip, the generic MMIO and
regmap helper libraries, the interrupt chip helpers, the userspace interfaces
and the tests. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written
guide it will replace is 435 words, so most of what is asked here cannot be in
the built guide; the point is to find which few things must be. Pin control
and the device tree binding documents are not covered. The trimmed set a guide
is built from is `../gpio.md`. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## gpio.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold the gpiolib core, the device tree, ACPI and software node
lookups, the character device, the sysfs interface, the integer-based legacy
calls, the managed (devres) wrappers, support for lines with several
consumers, the generic MMIO and regmap helper libraries, and the in-kernel
tests? A table. Start from `drivers/gpio/` and `drivers/gpio/gpiolib.h`.

## gpio.headers: Headers by role

- section: Finding your way
- relevance: 5 - the first thing checked in any patch that touches GPIOs
- words: 90

Which header should a GPIO controller driver include, which a consumer, which
a board file that describes lines, and which the two helper libraries? What
does `include/linux/gpio.h` itself say about being included, what does it pull
in, and is there a separate header for the device tree GPIO calls in this
tree? Start from `include/linux/gpio/`.

## gpio.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - a change has to keep the tests passing
- words: 80

Which files under `Documentation/` describe the driver interface, the consumer
interface, board mappings and the userspace interfaces, where is the
subsystem's list of ongoing work kept, and what exercises a change to gpiolib:
which simulator or mock-up drivers, selftests and KUnit suites, and which
configuration options build them? Start from `drivers/gpio/Kconfig` and
`tools/testing/selftests/gpio/`.

# What this tree calls things

## gpio.objects: Chip, device and descriptor

- section: Objects and names
- relevance: 5 - which object outlives which decides what a pointer may be used for
- words: 100

What are `struct gpio_chip`, `struct gpio_device` and `struct gpio_desc`, who
allocates each, which of them can outlive the driver that registered the chip,
and how does gpiolib code get from a descriptor to the chip safely while the
chip may be going away? Start from `drivers/gpio/gpiolib.h` and
`gpiochip_remove()`.

## gpio.flag-namespaces: Flag namespaces

- section: Objects and names
- relevance: 4 - three sets of constants with similar names and different values
- words: 90

Which sets of flag constants describe a GPIO line: the ones in a device tree
specifier, the ones in a board lookup table, the ones a consumer passes when it
requests a line, and the state bits kept in the descriptor? Give the header
each lives in and the prefix its names carry. Start from
`include/linux/gpio/machine.h`, `include/linux/gpio/consumer.h` and
`struct gpio_desc`.

## gpio.legacy-api: Integer-based interface

- section: Objects and names
- relevance: 5 - new uses of it are refused and readers misremember what is left
- words: 100

Which functions of the integer-based GPIO interface exist in this tree, under
which configuration symbol and in which header and source file? Say for each
of these whether it is still there: requesting an array of GPIOs, the managed
request that takes no flags, setting debounce by number, and the device tree
calls that return a GPIO number. What does each remaining value and direction
call turn into in terms of the descriptor interface? Start from
`include/linux/gpio/legacy.h`.

## gpio.chip-callbacks: Chip callbacks

- section: Objects and names
- relevance: 4 - the prototypes have changed and gpiolib now polices the return values
- words: 110

List the callbacks of `struct gpio_chip` a driver fills in to read, write and
set the direction of lines, with the return type and the permitted return
values of each. What does gpiolib do when a callback returns a value outside
that set? Start from `gpiochip_get()`, `gpiochip_set()` and
`gpiochip_get_direction()` in `drivers/gpio/gpiolib.c`.

# Facts that are easy to get wrong

## gpio.logical-and-raw: Logical and raw values

- section: Consumers
- relevance: 5 - converting a driver from one interface to the other silently inverts lines
- words: 100

Which consumer calls act on the logical value of a line and which on the
physical level, and which line properties besides polarity does the logical
set-value path apply? When a driver is converted from the integer-based calls
to descriptors, which of the two did the old calls use, and what therefore
changes for a line whose firmware description marks it active low? Start from
`gpiod_set_value_nocheck()`.

## gpio.request-flags: Initial state at request

- section: Consumers
- relevance: 4 - the wrong constant asserts a reset line during probe
- words: 70

What do the values of `enum gpiod_flags` passed to `gpiod_get()` ask for, and
is the initial output value they name a logical or a physical level? Which
lookup flags are folded into the descriptor at the same time? Start from
`gpiod_configure_flags()`.

## gpio.null-and-error-descs: NULL and error descriptors

- section: Consumers
- relevance: 4 - decides whether an optional line needs a NULL check at every use
- words: 80

What do the optional request calls return when no line is described, and what
do the value, direction and configuration calls do when handed a NULL
descriptor or an error pointer? What usage of an optional GPIO is unsafe, and
what that looks similar is correct? Start from `validate_desc()` in
`drivers/gpio/gpiolib.c`.

## gpio.sleeping-access: Sleeping and atomic access

- section: Consumers
- relevance: 4 - the wrong variant warns at run time, not at build time
- words: 80

How does a chip declare that its accessors may sleep, what happens when the
plain value calls are used on a line of such a chip, what do the calls with
cansleep in their name check, and how does a consumer that can run in either
context choose? Start from `gpiod_get_value()` and `gpiod_cansleep()`.

## gpio.set-value-errors: Errors from setting a value

- section: Consumers
- relevance: 3 - the return type is not what older code assumes
- words: 60

What do `gpiod_set_value()` and its variants return in this tree, and which
errors come back when the line is not an output, when the chip has been
removed, and when the driver's callback fails? Start from
`gpiod_set_raw_value_commit()`.

## gpio.lookup-order: Finding a line

- section: Lookups
- relevance: 4 - the error code decides between probe deferral and a missing line
- words: 100

When a consumer asks for a line by function name, in what order are device
tree, ACPI, software nodes, a secondary firmware node and the board lookup
tables consulted, which property names are tried for a given function name,
and which error comes back when nothing describes the line as opposed to when
the controller is not registered yet? Start from `gpiod_find_and_request()`
and `gpio_suffixes`.

## gpio.of-quirks: Device tree quirks

- section: Lookups
- relevance: 5 - where a binding that got polarity or naming wrong is fixed up
- words: 110

Which tables and functions in `drivers/gpio/gpiolib-of.c` adjust what a device
tree says about a line: forcing a polarity for a given compatible and
property, taking polarity from a separate boolean property, and accepting an
old property name? How is an entry in each keyed, how are entries kept out of
kernels that do not build the driver concerned, and what is logged when a quirk
overrides the device tree? Start from `of_gpio_flags_quirks()` and
`of_find_gpio_quirks`.

## gpio.polarity-workarounds: Working around wrong polarity

- section: Lookups
- relevance: 5 - the usual mistake when a legacy driver is converted
- words: 90

A driver is being converted to descriptors and existing device trees carry a
polarity flag that disagrees with how the driver has always driven the line.
Which of these does the tree treat as acceptable and which not: negating the
value in the driver, switching to the raw accessors, flipping the descriptor's
polarity after the request, a quirk inside gpiolib? Say what the documentation
says the raw accessors are for and what kind of caller uses
`gpiod_toggle_active_low()`. Start from
`Documentation/driver-api/gpio/consumer.rst` and
`of_gpio_try_fixup_polarity()`.

## gpio.shared-lines: Lines with several consumers

- section: Lookups
- relevance: 4 - the old flag is deprecated and the replacement is new
- words: 100

How does this tree let two devices use one GPIO line: what is the status of the
request flag that allowed a second request of a busy line, what does gpiolib
do on its own when firmware shows a line referenced by several consumers, which
configuration symbols turn that on, and what does a consumer driver have to do
differently? Start from `drivers/gpio/gpiolib-shared.c` and
`GPIOD_FLAGS_BIT_NONEXCLUSIVE`.

## gpio.board-descriptions: Describing lines without firmware

- section: Lookups
- relevance: 3 - board files are still converted and the preferred form has changed
- words: 80

How does a board file with no device tree or ACPI describe which line a device
uses: what are the two mechanisms in this tree, which does the documentation
prefer for new conversions, how is the controller identified in each, and what
comes back when the controller named has not been registered yet? Start from
`include/linux/gpio/machine.h`, `include/linux/gpio/property.h` and
`swnode_find_gpio()`.

# Using it safely

## gpio.chip-registration: Registering a chip

- section: Writing a chip driver
- relevance: 4 - what a new driver's probe function is checked against
- words: 100

What must a driver fill in before it registers a `struct gpio_chip`, which
fields have a preferred value that the core warns about otherwise, where can
the number of lines come from when the driver leaves it zero, and in what order
does registration set up the descriptors, device tree and ACPI data, pin
ranges, hogs, the interrupt chip and the character device? Start from
`gpiochip_add_data_with_key()`.

## gpio.chip-removal: Removing a chip in use

- section: Writing a chip driver
- relevance: 4 - decides what a driver may free in its remove path
- words: 80

What happens when a chip is removed while consumers still hold descriptors or
userspace has the character device open: what do later consumer calls return,
what keeps memory alive, and what may the driver's callbacks assume after
removal returns? Start from `gpiochip_remove()` and `gpio_chip_guard`.

## gpio.generic-mmio: Generic MMIO helper

- section: Helper libraries
- relevance: 5 - the interface reviewers ask new drivers to use has been renamed
- words: 120

How does a driver for memory-mapped registers with one bit per line use the
generic MMIO helper: which configuration symbol and header, which structures
and which initialisation function, which register widths and register roles it
supports, and what the driver still has to do itself afterwards? Which flags
cover reversed bit order, unreadable registers and input-only or output-only
hardware, and how does a driver take the helper's lock? Start from
`include/linux/gpio/generic.h` and `drivers/gpio/gpio-mmio.c`.

## gpio.banked-controllers: Controllers with several banks

- section: Helper libraries
- relevance: 4 - how more lines than one register holds are fitted to the helper
- words: 90

When a controller has more lines than fit in one register, how do in-tree
drivers that use the generic MMIO helper arrange it, and what are the ways the
device tree can refer to a line of such a controller: one node per bank, or
one node with an extra specifier cell? Which `struct gpio_chip` members does
the second form need? Name a driver that does each. Start from
`of_gpio_threecell_xlate()`.

## gpio.regmap-helper: Regmap helper

- section: Helper libraries
- relevance: 5 - the second helper reviewers ask for, with rules about its register bases
- words: 110

How does a driver whose registers are reached through regmap use the GPIO
regmap helper: which configuration symbol, header, configuration structure and
registration call, what the rules are for which register bases must be given
together, how a register base of zero is expressed, and what the translation
callback receives and returns? What does the default translation assume about
the register layout, and can a driver call it directly? Start from
`include/linux/gpio/regmap.h`.

## gpio.irqchip: Interrupt chip helpers

- section: Helper libraries
- relevance: 4 - the immutable form is required of new drivers
- words: 110

How does a GPIO driver that also delivers interrupts set that up through
`struct gpio_irq_chip`: what is filled in before the chip is registered, what
must an immutable `struct irq_chip` contain and call from its mask and unmask
callbacks, what does the core do and print when the irq_chip is not marked
immutable, and which combination of a chained handler and a sleeping chip is
refused? Start from `gpiochip_add_irqchip()` and `gpiochip_set_irq_hooks()`.

# Changing the implementation

## gpio.userspace-abi: Userspace interfaces

- section: What a change must preserve
- relevance: 3 - two of the three are deprecated but still ABI
- words: 90

Which userspace interfaces to GPIO lines does this tree build, which
configuration symbol enables each and which are marked deprecated, where is
the ioctl ABI defined, and what does the second sysfs option control? Start
from `include/uapi/linux/gpio.h`, `drivers/gpio/gpiolib-cdev.c` and
`drivers/gpio/gpiolib-sysfs.c`.

## gpio.core-locking: Locks in the core

- section: What a change must preserve
- relevance: 3 - which calls may be made from atomic context follows from these
- words: 90

Which locks and SRCU domains does the gpiolib core use, and what does each
protect: the list of devices, the pointer from a device to its chip, a
descriptor's consumer label, the board lookup tables, the line state
notifier? Which consumer calls can therefore be made from atomic context? Start
from the top of `drivers/gpio/gpiolib.c` and `struct gpio_device`.

## gpio.change-checklist: Changing gpiolib

- section: What a change must preserve
- relevance: 3 - the code is built in more configurations than a developer tests
- words: 80

What must a change to the gpiolib core or to `include/linux/gpio/consumer.h`
keep working besides the default build: the stubs for kernels without GPIO
support, builds without the character device, without device tree or ACPI, the
global number space and the sysfs interface that depends on it, the uAPI
structure layouts, and the tests? Say where each lives.
