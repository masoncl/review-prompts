- `vgic_mmio_write_v3r_ctlr()`: does nothing without an ITS, and flushes only
  if `atomic_cmpxchg_acquire()` moves `ctlr` from `GICR_CTLR_ENABLE_LPIS` to
  `GICR_CTLR_RWP`.
- `vgic_flush_pending_lpis()` clears `pending_latch` on each LPI it removes, in
  addition to `list_del()` and `vcpu = NULL`.
- Only LPIs on this vCPU's `ap_list` are touched; an LPI that is latched
  pending but not queued keeps its `pending_latch`.
- After releasing `ap_list_lock` the function itself calls
  `vgic_release_deleted_lpis()` if any put returned true.
