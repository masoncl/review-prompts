- **Unsafe usage**: taking the reference on a pointer just loaded from `lpi_xa`
  with `vgic_get_irq_ref()`.
  - Unsafe: at count zero `vgic_get_irq_ref()` warns once and takes nothing, so
    the caller's later put underflows a freed or dying object.
  - Safe: `vgic_try_get_irq_ref()` and return NULL on false, as
    `vgic_get_lpi()` does.
- **Potentially unsafe usage**: reading fields of an entry of `lpi_xa` before
  holding a reference.
  - Unsafe: outside both `rcu_read_lock()` and `lpi_xa.xa_lock`; the object is
    freed by `kfree_rcu()` in `vgic_release_lpi_locked()`.
  - Safe: inside the RCU section, before the try-get, as
    `__vgic_host_irq_get_vlpi()` in `arch/arm64/kvm/vgic/vgic-v4.c` does with
    `hw` and `host_irq`.
  - Safe: under `lpi_xa.xa_lock`, as `vgic_release_deleted_lpis()` does.
- Walkers of `lpi_xa` outside RCU, for example `vgic_its_invall()` and
  `vgic_v3_save_pending_tables()`, discard the pointer `xa_for_each()` yields
  and call `vgic_get_irq()` on the index.
- Lookups that take a reference from `lpi_xa`: `vgic_get_lpi()`,
  `vgic_add_lpi()` and `__vgic_host_irq_get_vlpi()`; `vgic_its_check_cache()`
  does the same on `translation_cache`.
- The debugfs iterator is not one of them; it takes no reference from `lpi_xa`.
