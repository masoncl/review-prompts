- `its_clear_vpend_valid()`: returns the `u64` value of `GICR_VPENDBASER`
  last read, never a boolean or an error code.
- Not settled in time: the returned value has `GICR_VPENDBASER_Dirty` still
  set and `GICR_VPENDBASER_PendingLast` forced to 1 by the helper itself.
- `read_vpend_dirty_clear()`: called twice by the helper, before the write
  and after it; each call polls for up to about one second.
- `its_vpe_deschedule()` and `its_vpe_4_1_deschedule()`: neither tests
  Dirty in the result; both are void, so `DESCHEDULE_VPE` returns 0 and
  `its_make_vpe_non_resident()` clears `vpe->resident` after a timeout too.
- GICv4.1 with `info->req_db` false: the helper is called with
  `set = GICR_VPENDBASER_PendingLast`, the result is discarded, and
  `vpe->pending_last` is set to true.
- `info->req_db`: the `db` argument of `its_make_vpe_non_resident()`, which
  KVM takes from `vgic_v4_want_doorbell()`; WFI is not the only case, see
  "vPE residency from KVM".
