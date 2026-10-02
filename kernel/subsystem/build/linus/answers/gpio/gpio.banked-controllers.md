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
