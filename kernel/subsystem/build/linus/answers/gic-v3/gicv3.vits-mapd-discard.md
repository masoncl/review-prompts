- `its_unmap_vlpi()`: returns `void` in this tree
  (`drivers/irqchip/irq-gic-v4.c`); `its_free_ite()` does not wrap it in
  `WARN_ON()`.
- Hardware-forwarded interrupt in `its_free_ite()`: under `irq->irq_lock`,
  `its_unmap_vlpi(irq->host_irq)` if `irq->hw`, then `irq->hw = false`, all
  before `vgic_put_irq()`.
- `its_free_ite()`: does not touch `pending_latch` or `enabled` of the
  `struct vgic_irq`.
- `its_free_ite()` with `ite->irq` NULL: allowed, the unmap and put are
  skipped; `vgic_its_cmd_handle_mapi()` relies on it in its unwind.
- `vgic_its_cmd_handle_discard()`: needs `find_ite()` to succeed and
  `its_is_collection_mapped(ite->collection)`.
- DISCARD of an event whose collection is unmapped in either form: returns
  `E_ITS_DISCARD_UNMAPPED_INTERRUPT` and the ITE stays.
- DISCARD besides freeing: `vgic_its_invalidate_cache()`, then a zero ITE is
  written to the guest's ITT with `vgic_its_write_entry_lock()`.
- MAPD with V=0: writes a zero DTE to guest memory even when no device was
  mapped.
- `E_ITS_MAPD_ITTSIZE_OOR`: tested only when V=1.
- `vgic_its_free_device()`: calls `vgic_its_invalidate_cache()` after freeing
  the ITEs.
