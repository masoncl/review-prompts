- `gic_check_rdist()` (`CPUHP_BP_PREPARE_DYN`): returns `-EINVAL` when the
  CPU is in `broken_rdists`, and tests nothing else.
  - Only `gic_acpi_parse_madt_gicc()` sets bits in `broken_rdists`, for a GICC
    entry with `ACPI_MADT_GICC_ONLINE_CAPABLE` and without
    `ACPI_MADT_ENABLED`.
  - It does not look for the redistributor; a CPU for which
    `gic_populate_rdist()` later finds none passes this check.
- `gic_starting_cpu()`: always returns 0 and drops the return value of
  `its_cpu_init()`, which can be an error from `redist_disable_lpis()`.
- A STARTING callback that returns non-zero: `notify_cpu_starting()` uses
  `cpuhp_invoke_callback_range_nofail()`, which only does `pr_warn()` and
  continues.
- `its_cpu_memreserve_lpi()`: allocates no pending table.
  - Its only error is `-ENOMEM`, when `pend_page` is NULL.
  - A `gic_reserve_range()` failure is a `WARN_ON()` and is not returned.
  - `RD_LOCAL_MEMRESERVE_DONE` is set on the failing path too, so a second
    run on that CPU returns 0.
- First run of `its_cpu_memreserve_lpi()`: on the boot CPU, as a direct call
  from `cpuhp_setup_state()` in `its_lpi_memreserve_init()`.
  - That is inside `init_IRQ()`, before `start_kernel()` enables interrupts.
  - Later CPUs run it in the `CPUHP_AP_ONLINE_DYN` state.
- **Potentially unsafe usage**: allocating memory in code reached from
  `gic_starting_cpu()`.
  - Unsafe: with a gfp mask that allows blocking, such as `GFP_KERNEL`;
    `secondary_start_kernel()` has not yet unmasked interrupts, and
    `might_alloc()` does `might_sleep_if()` on such a mask.
  - Unsafe: under `CONFIG_PREEMPT_RT` with any mask, when the allocation can
    reach the page allocator; `zone->lock` is a `spinlock_t`, which sleeps
    there.
  - Unsafe: when the only report of failure is the callback's return value;
    nothing acts on it.
  - Safe: without `CONFIG_PREEMPT_RT`, `GFP_ATOMIC` with the failure handled
    in place, as `allocate_vpe_l1_table()` does; its caller
    `its_cpu_init_lpis()` clears `has_rvpeid` and `has_vlpis` on failure.
  - Safe: allocating for every possible CPU on the boot CPU, as
    `allocate_lpi_tables()` does from `its_init()` with `GFP_NOWAIT`;
    `its_cpu_init_lpis()` then only programs `pend_page`.
  - Safe: deferring to the `CPUHP_AP_ONLINE_DYN` callback, which a secondary
    CPU runs in `cpuhp_thread_fun()` with interrupts on, as
    `its_cpu_memreserve_lpi()` does for `gic_reserve_range()`, which reaches
    `memremap()` through `efi_mem_reserve_persistent()`.
