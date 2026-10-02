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
