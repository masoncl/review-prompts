- `regmap_add_irq_chip_fwnode()` has five `-EINVAL` tests of the chip, all
  before any allocation:
  - `num_regs <= 0`
  - `clear_on_unmask` with `ack_base` or `use_ack`
  - `mask_base` and `unmask_base` both set without `mask_unmask_non_inverted`
  - an `irqs[i].reg_offset` that is not a multiple of `map->reg_stride`
  - an `irqs[i].reg_offset / map->reg_stride` that is `>= num_regs`
- Not tested at registration: `type_in_mask` layouts, a zero `status_base`,
  `clear_on_unmask` with `status_invert`, `clear_ack` without `ack_base`.
- `mask_unmask_non_inverted`: read only by the registration test. It changes
  no written value; the kerneldoc in `include/linux/regmap.h` that describes
  an inverted mode does not match the code.
- `mask_base` and `unmask_base` both set (with the flag): to mask, the bit is
  set in the `mask_base` register and cleared in the `unmask_base` register,
  on every sync. Examples: `drivers/mfd/stpmic1.c`,
  `drivers/mfd/qcom-pm8008.c`.
- There is no mask_invert member in `struct regmap_irq_chip`; a register where
  0 means masked is described with `unmask_base` alone.
- `handle_mask_sync` set: neither `mask_base` nor `unmask_base` is written, at
  registration or in `regmap_irq_sync_unlock()`.
