- First test: `!atomic_read(&vpe->vmapp_count)`, made before the function
  takes any lock; it is not a test of the old CPU against the new one.
- `vmapp_count` zero under eager mapping: returns `-EINVAL` and changes
  nothing.
- `vmapp_count` zero under lazy mapping: only the effective affinity is set to
  `cpumask_first(mask_val)`; `col_idx` is left as it was and no command is
  sent.
- `its_vpe_set_affinity()` sends no VMAPP in any outcome; a move does not map
  the vPE on a destination ITS or unmap it from a source ITS.
- `vmapp_lock`: taken only `if (its_list_map)`, with plain `raw_spin_lock()`,
  before `vpe_lock`.
- `vpe_lock`: held from `vpe_to_cpuid_lock()` until after
  `irq_data_update_effective_affinity()`, also when the CPU does not change.
- `vmovp_lock`, `rd_lock` and `vpe_proxy.lock`: taken and dropped inside
  `its_send_vmovp()`, `its_vpe_4_1_invall_locked()` and
  `its_vpe_db_proxy_move()`, under `vpe_lock`, and under `vmapp_lock` when it
  was taken.
