- There is no marking scheme here: no iter_mark_lpis(), no
  LPI_XA_MARK_DEBUG_ITER, and no reference held across the iteration.
- Next LPI: `iter_next()` calls `xa_find_after()` on `lpi_xa` with
  `XA_PRESENT`, under `rcu_read_lock()`, and keeps only the ID in `intid`.
- End of the LPIs: `intid` is set to `VGIC_LPI_MAX_INTID + 1`.
- `struct vgic_state_iter` has no LPI index or count field.
- Interrupt gone: `vgic_debug_show()` returns 0 and prints nothing when
  `vgic_get_irq()` returns NULL; no warning and no error.
