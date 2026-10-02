- `vgic_v5_set_ppi_dvi()`: only asserts `irq->irq_lock` with
  `lockdep_assert_held()`. `kvm_vgic_map_phys_irq()` and
  `kvm_vgic_unmap_phys_irq()` take it.
- **Potentially unsafe usage**: `__set_bit()`, `__clear_bit()` or
  `__assign_bit()` on a bitmap indexed by interrupt while holding
  `irq->irq_lock`.
  - Unsafe: when the bitmap is shared and the writers of its other bits hold
    only their own `irq_lock`, as for `vgic_ppi_dvir`. Two non-atomic updates
    of one word lose a bit.
  - Safe: the atomic `assign_bit()`, as `vgic_v5_set_ppi_dvi()` does.
  - Safe: when one lock covers the whole walk. `vgic_v5_finalize_ppi_state()`
    writes `vgic_ppi_mask` and `vgic_ppi_hmr` with `__set_bit()` and
    `__assign_bit()` under `kvm->arch.config_lock`.
  - Safe: on an on-stack bitmap. `vgic_v5_flush_ppi_state()` builds its
    pending bitmap with `__assign_bit()` and publishes it with one
    `bitmap_copy()` after the loop.
