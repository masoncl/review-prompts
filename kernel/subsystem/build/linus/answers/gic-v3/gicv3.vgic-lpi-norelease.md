- `vgic_put_irq_norelease()` and `vgic_release_deleted_lpis()`: both `static`
  in `arch/arm64/kvm/vgic/vgic.c`, so only code in that file can use them.
- `vgic_put_irq_norelease()`: for an LPI returns the result of
  `refcount_dec_and_test()`, for any other interrupt false; it records nothing
  else; there is no pending_release field and no xarray mark.
- `vgic_release_deleted_lpis()`: walks all of `lpi_xa` under
  `xa_lock_irqsave()` and releases every entry whose `refcount_read()` is zero,
  including entries another vCPU's put left behind.
- Between the put and the sweep `vgic_add_lpi()` may already have evicted and
  freed the object, so the sweep can release nothing for that ID.
