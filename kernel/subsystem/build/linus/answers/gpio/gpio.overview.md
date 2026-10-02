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
