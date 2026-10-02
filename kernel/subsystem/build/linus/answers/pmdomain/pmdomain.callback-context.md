- Lock kinds: three. `genpd_lock_init()` tests `GENPD_FLAG_CPU_DOMAIN` first.

| Selected by | Lock | `lock_ops` |
|---|---|---|
| `GENPD_FLAG_CPU_DOMAIN`, with or without `GENPD_FLAG_IRQ_SAFE` | `raw_slock` | `genpd_raw_spin_ops` |
| `GENPD_FLAG_IRQ_SAFE` alone | `slock` | `genpd_spin_ops` |
| neither | `mlock` | `genpd_mtx_ops` |

- There is no genpd_lock_ops_spin in this tree.
- `raw_slock` domain: `power_on`, `power_off` and the notifiers run with IRQs
  off; for `slock` that holds only without `CONFIG_PREEMPT_RT`.
- `GENPD_FLAG_CPU_DOMAIN` without `GENPD_FLAG_IRQ_SAFE`: the lock is a raw
  spinlock but `genpd_is_irq_safe()` is false, so `genpd_switch_state()`,
  `genpd_add_subdomain()` and `irq_safe_dev_in_sleep_domain()` treat the domain
  as one that may sleep. The two providers that set the CPU flag,
  `drivers/cpuidle/cpuidle-psci-domain.c` and
  `drivers/cpuidle/cpuidle-riscv-sbi.c`, set both flags.
- Noirq system sleep: `genpd_finish_suspend()` and `genpd_finish_resume()` take
  the domain lock and pass `use_lock` true.
- Lockless path: `genpd_switch_state()`, behind `dev_pm_genpd_suspend()` and
  `dev_pm_genpd_resume()`. It sets `use_lock = genpd_is_irq_safe(genpd)`.
- Domain with `GENPD_FLAG_IRQ_SAFE` on that path: locked as usual.
- Domain without `GENPD_FLAG_IRQ_SAFE` on that path: no lock on the domain, nor
  on any parent reached from it, whatever the parent's own flags; `use_lock` is
  passed up unchanged.
- Context of the lockless path: a mutex domain's callbacks and notifiers can run
  with IRQs off there; for example `sh_cmt_clocksource_suspend()` in
  `drivers/clocksource/sh_cmt.c` is reached from
  `timekeeping_syscore_suspend()`.
