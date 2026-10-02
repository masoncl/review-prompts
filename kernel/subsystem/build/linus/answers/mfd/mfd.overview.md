- One cell yields at most one child: `struct mfd_cell` has no num_devices
  member; several children of one kind need several cells or several calls.
- Child id: `id + cell->id` (the cell's `id` member, not its array index);
  with `PLATFORM_DEVID_AUTO` the cell's `id` is ignored. See
  `mfd_add_device()`.
- `struct resource` in a cell, as translated by `mfd_add_device()`:

  | Cell resource | Child resource |
  |---|---|
  | `flags` has the `IORESOURCE_MEM` bit (`IORESOURCE_REG` has it too), `mem_base` non-NULL | offset by `mem_base->start`, parented to `mem_base` |
  | `IORESOURCE_IRQ`, `domain` non-NULL | `irq_create_mapping()` of `start`; a range triggers `WARN_ON()` |
  | `IORESOURCE_IRQ`, `domain` NULL | offset by `irq_base` |
  | anything else, including `IORESOURCE_IO` and `IORESOURCE_MEM` with NULL `mem_base` | copied unchanged, with the cell's `parent` |

- `mfd_dev_type`: the private `struct device_type` stamped on every child
  (there is no mfd_devtype).
- OF node lookup in `mfd_add_device()`: runs only for a cell with
  `of_compatible` under a parent that has an `of_node`; for a parent without
  an `of_node` the core gives the child no DT node and prints no
  "Failed to locate of_node" warning.
- `struct mfd_of_node_entry`: one entry per DT node handed to a child, on
  `mfd_of_node_list`, which is global rather than per parent; without
  `use_of_reg`, cells with the same compatible take the nodes in DT order.
- `swnode` is the only software-node member of the cell; there is no
  property-entry member.
- `drivers/mfd/mfd-core.c` sets no driver data and no regmap on a child;
  reaching the regmap or driver data through `dev.parent` is a convention
  between the two drivers, which the core neither sets up nor enforces.
- DMA: the child's `dev.dma_mask` and `dev.dma_parms` point at the parent's
  objects (not copies); `coherent_dma_mask` is copied by value.
- `parent_supplies`: regulator supply names that the child requests are
  aliased to the parent device, so the lookup happens on the parent.
- `drivers/mfd/simple-mfd-i2c.c`: `simple_mfd_i2c_probe()` uses
  `devm_mfd_add_devices()` when the match data carries cells, and
  `devm_of_platform_populate()` only when it carries none.
- Children created from DT nodes rather than cells: `mfd_get_cell()` returns
  NULL and `dev.type` is not `mfd_dev_type`, so `mfd_remove_devices()` skips
  them.
- `keyboard_led_is_mfd_device()` in
  `drivers/platform/chrome/cros_kbd_led_backlight.c`: uses
  `IS_ENABLED(CONFIG_MFD_CROS_EC_DEV)` and a non-NULL `mfd_get_cell()` to tell
  an MFD child from a device that firmware enumerated.
- `struct syscon` in `drivers/mfd/syscon.c`: unrelated to cells; it has no
  `struct device`, is keyed by `struct device_node` on the global
  `syscon_list`, and nothing in that file removes an entry.
