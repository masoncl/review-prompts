- `gic_cpu_sys_reg_init()` and `gic_cpu_init()`: do not call
  `gic_cpu_sys_reg_enable()`.
  - Its callers are `gic_init_bases()`, `gic_starting_cpu()` and
    `gic_cpu_pm_notifier()` (exit path only), each before the other `ICC_*`
    accesses of that path.
  - `CPU_PM_ENTER` writes `gic_write_grpen1(0)` without calling it.
- `gic_enable_sre()`: defined in `include/linux/irqchip/arm-gic-v3.h`, not in
  the arch headers.
  - It touches only the EL1 register, through `gic_read_sre()` and
    `gic_write_sre()`; it writes nothing at EL2.
  - The `isb()` is inside `gic_write_sre()` in
    `arch/arm64/include/asm/arch_gicv3.h`.
  - It returns `true` without writing when `ICC_SRE_EL1_SRE` is already set.
- `gic_cpu_sys_reg_enable()` when the bit does not stick: `pr_err()` only.
  - It is void, and all three callers go on to the next step; there is no
    explicit panic or error return.
- Arch code calls `gic_enable_sre()` directly as well, so the driver is not
  the only place it happens:
  - `has_useable_gicv3_cpuif()` in `arch/arm64/kernel/cpufeature.c`:
    `pr_warn_once()` and the capability is reported absent.
  - `init_gic_priority_masking()` in `arch/arm64/kernel/smp.c`: `WARN_ON()`
    and returns without setting PMR.
- `gic_cpu_pm_notifier()`: saves nothing; no register is read into memory.
- `CPU_PM_ENTER_FAILED`: handled exactly as `CPU_PM_EXIT`.
- `gic_enable_redist()` in the notifier: called only when
  `gic_dist_security_disabled()` is true, on entry and on exit.
  - With security enabled, `CPU_PM_ENTER` does nothing at all, including no
    `gic_write_grpen1(0)`.
- On exit, besides that conditional `gic_enable_redist()`, the notifier redoes
  only `gic_cpu_sys_reg_enable()` and `gic_cpu_sys_reg_init()`.
  - It does not call `gic_populate_rdist()` or `gic_cpu_config()`; SGI/PPI
    group, priority and enable state in the redistributor is not rewritten.
