- Ordinary failure: `-ENOMEM`, the value `bitmap_find_free_region()`
  returns, passed through unchanged by `gicv5_its_alloc_eventid()` and
  `gicv5_its_irq_domain_alloc()`; neither uses `-ENOSPC`.
- Fixed message data failures: all three return `-EINVAL`: `nr_irqs != 1`
  (with `WARN_ON_ONCE()`), `info->hwirq >= its_dev->num_events`, and bit
  already set. Neither `-EBUSY` nor `-EEXIST` is returned.
- `MSI_ALLOC_FLAGS_FIXED_MSG_DATA`: set by `iwb_msi_template` in
  `drivers/irqchip/irq-gic-v5-iwb.c`; `gicv5_iwb_domain_set_desc()` puts the
  wire number in `info->hwirq`, so the event ID equals the IWB wire.
- `gicv5_its_free_eventid()`: called only from the error path of
  `gicv5_its_irq_domain_alloc()`. `gicv5_its_irq_domain_free()` calls
  `bitmap_release_region()` directly.
- `gicv5_its_irq_domain_free()`: entered once per interrupt with
  `nr_irqs == 1`, because `irq_domain_free_irqs_hierarchy()` in
  `kernel/irq/irqdomain.c` calls `.free` that way; each call clears one bit.
- Fixed IDs are freed the same way; `clear_bit()` is not used.
- **Unsafe usage**: an ordinary allocation whose `nr_irqs` is not a power of
  two.
  - Unsafe: `bitmap_find_free_region()` sets `1 << get_count_order(nr_irqs)`
    bits and the per-interrupt free clears `nr_irqs` of them; with a bit
    left, `gicv5_its_msi_teardown()` hits `WARN_ON_ONCE()` and returns
    without unregistering the device.
  - Safe: `nr_irqs == 1`, as for an MSI-X descriptor
    (`msix_prepare_msi_desc()` sets `nvec_used` to 1) and for the fixed
    path, which rejects any other count.
  - Safe: the alloc error path, where `gicv5_its_free_eventid()` releases
    the whole region with the same order.
