- Order of choice: with a `vpe_table_mask` for the old CPU, keep the old CPU
  if it is in both `mask_val` and that mask; else any CPU in both; with no
  CPU in both, or with no `vpe_table_mask`, `cpumask_first(mask_val)`.
- `its_vpe_set_affinity()` makes no `cpu_online_mask` test of its own;
  `irq_do_set_affinity()` in `kernel/irq/manage.c` passes a mask already
  restricted to online CPUs unless `force` is set.
- `vpe->col_idx` is written before `its_send_vmovp()`, which reads it to pick
  the collection.
- Residency: the function does not deschedule or reschedule the vPE;
  `vgic_v4_load()` calls `irq_set_affinity()` first and
  `its_make_vpe_resident()` after.
- After VMOVP no VINVALL command is sent; the only invalidate is
  `its_vpe_4_1_invall_locked()` on the new CPU, when `find_4_1_its()` returns
  an ITS with `ITS_FLAGS_WORKAROUND_HISILICON_162100801`.
- `its_vpe_db_proxy_move()` then runs one of three cases:
  - `has_rvpeid`: nothing.
  - `has_direct_lpi`: clears the doorbell on the old redistributor through
    `GICR_CLRLPIR` and waits in `wait_for_syncr()`.
  - otherwise: under `vpe_proxy.lock`, maps the vPE in the proxy device and
    calls `its_send_movi()`.
