- `its_vpe_schedule()`: sets `GICR_VPENDBASER_PendingLast` to 1 on every
  call, whatever `vpe->pending_last` holds.
- `its_vpe_4_1_schedule()`: writes the whole register with PendingLast 0.
- `pending_last` is not cleared when the vPE becomes resident; a true value
  stays until the next deschedule that stores the read-back, in
  `its_vpe_deschedule()` or in `its_vpe_4_1_deschedule()` with `req_db`.
- Writers of `pending_last`: `its_vpe_deschedule()` and
  `its_vpe_4_1_deschedule()` with `req_db` (both store the read-back),
  `its_vpe_4_1_deschedule()` without `req_db` (always true), and
  `vgic_v4_doorbell_handler()` (always true).
- `kvm_vgic_vcpu_pending_irq()`: reads `pending_last` without
  `vpe->vpe_lock`, after the `vgic.enabled` test and before the priority
  test; a true value is ignored while the distributor is disabled.
