- `translation_cache` in `struct vgic_its`: an xarray whose entries are the
  `struct vgic_irq` pointers themselves, keyed by `vgic_its_cache_key()`. There
  is no vgic_translation_cache_entry structure, no list and no lock besides
  the xarray's own.
- **Unsafe usage**: dropping the cache's reference on the pointer the walk
  yielded.
  - Safe: put only the non-NULL value `xa_erase()` returned, as
    `vgic_its_invalidate_cache()` does; two walkers can race, and only the one
    whose erase succeeds owns the reference.
- `vgic_its_invalidate_cache()` must not sleep:
  `vgic_its_invalidate_all_caches()` calls it inside `rcu_read_lock()`.
- Invalidating paths hold different locks. ITS command handlers hold
  `its_lock`; `vgic_mmio_write_its_ctlr()` holds `cmd_lock` but not
  `its_lock`; `vgic_its_invalidate_all_caches()` holds neither.
- `vgic_its_invalidate_all_caches()` has one caller,
  `vgic_mmio_write_v3r_ctlr()`.
- Order against `its_free_ite()` is free: `vgic_its_cmd_handle_discard()`
  invalidates first, `vgic_its_free_device()` frees the ITEs first. The cache's
  own reference keeps the object alive either way.
