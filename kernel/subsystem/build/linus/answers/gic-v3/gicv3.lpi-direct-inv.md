- Physical LPI: `irq_to_cpuid_lock()` takes no lock; it reads
  `its_dev->event_map.col_map` and relies on the caller holding the
  `irq_desc` lock, under which `its_set_affinity()` writes `col_map`.
- Doorbell detection: `irq_to_cpuid_lock()` tests only
  `d->chip == &its_vpe_irq_chip`. Doorbells of `its_vpe_4_1_irq_chip` never
  reach it; `its_vpe_4_1_send_inv()` invalidates them with
  `its_send_invdb()`.
- Lock order: `vpe->vpe_lock`, then `rd_lock`.
- `rd_lock`: taken with plain `raw_spin_lock()`. Interrupts are already off,
  through `raw_spin_lock_irqsave()` in `vpe_to_cpuid_lock()` or through the
  caller's `irq_desc` lock.
- All of a vPE's LPIs: `its_vpe_4_1_invall_locked()` writes `GICR_INVALLR`
  and takes only `rd_lock`. Both callers hold `vpe->vpe_lock`:
  `its_vpe_4_1_invall()` and `its_vpe_set_affinity()`, which passes the new
  CPU.
- `wait_for_syncr()`: spins on bit 0 of `GICR_SYNCR` with `cpu_relax()`; no
  timeout and no fallback to another register.
