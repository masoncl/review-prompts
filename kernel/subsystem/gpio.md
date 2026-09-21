# GPIO Subsystem Details

## Deprecate legacy APIs

Never accept new code referencing `<linux/gpio.h>`. This is a legacy header
and is gradually replaced with `<linux/gpio/driver.h>` for driver
implementations and `<linux/gpio/consumer.h>` for consumers.

## Add Device Tree quirks rather than using raw accessors

When replacing legacy APIs such as `gpio_get_value()` or
`gpio_get_value_cansleep()` to `gpiod_get_value()` or
`gpiod_get_value_cansleep()` the library will provide line polarity inversion
semantics such as when device tree phandles to GPIO lines are tagged with
`GPIO_ACTIVE_HIGH` from `<dt-bindings/gpio/gpio.h>`.

In these cases, recommend that a polarity quirk be added to
`drivers/gpio/gpiolib-of.h` enforcing a certain polarity for a certain binding,
thereby preserving the polarity semantics.

Do not recommend developers to use raw accessors such as
`gpiod_get_raw_value()` or `gpiod_get_raw_value_cansleep()` to work around
this problem as these are for especially peculiar fringe use cases.

## Use Generic MMIO GPIO helper library

If a new GPIO driver using `<linux/gpio/driver.h>` has hardware exposing
registers with regular fields of bits that are 8, 16, 32 or 64 bits wide,
where each bit is mapped directly to a GPIO line, where GPIO 0 is at bit 0,
GPIO 1 is at bit 1 etc, recommend to handle this with the generic MMIO GPIO
helper library enabled by `select GPIO_GENERIC` in `Kconfig` and using the
header `<linux/gpio/generic.h>`.

This works especially well when the number of GPIOs are equal to the number of
bits in a register, but can often be used also when the GPIO lines are accessed
in several similarly shaped registers so that after GPIO 31 in bit 31 a second
register starting with GPIO 32 at bit 0 in the new register and GPIO 33 at bit
1 in the new registet etc, in this case GPIOs can often be grouped into banks
with 8/16/32/64 GPIOs each, where each bank correpsonds to one GPIO chip.

During device tree review it should be pointed out that a structure where a
single node exposing e.g 128 GPIOs could possibly be broken into 4 nodes
corresponding to 4 banks of 32 GPIOs each. This mapping of the hardware makes
it easier to write a driver using `GPIO_GENERIC` later on.

## Use Generic Regmap GPIO library

If a new GPIO driver using `<linux/gpio/driver.h>` is also using the regmap
abstraction from `<linux/regmap.h>` it may be adivisable to use the GPIO regmap
helper library enabled by `select GPIO_REGMAP` in `Kconfig` and including the
header `<linux/gpio/regmap.h>`

The regmap library has a function to translate a GPIO line offset to a register
and bitmask, so that registers with bitfields for different settings
and values can easily be used accessed if these registers and bitmasks have
a repeating pattern.

