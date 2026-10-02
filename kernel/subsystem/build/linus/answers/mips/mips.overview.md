- Cache line-size macros such as `cpu_dcache_line_size()`, as
  `arch/mips/include/asm/cpu-features.h` defines them: read `cpu_data[0]`, not
  the running CPU's entry.
- `cpu_has_fpu` and `raw_cpu_has_fpu`: the constant 0 when
  `CONFIG_MIPS_FP_SUPPORT` is off or a platform override defines
  `cpu_has_fpu`.
- Page table to refill handler: the handler does not look at `current`; it
  reads the pgd that `tlbmiss_handler_setup_pgd()` installed, from
  `pgd_current[]`, or from a CP0 register when `pgd_reg` is not -1 or under
  `CONFIG_MIPS_PGD_C0_CONTEXT`.
- `tlbmiss_handler_setup_pgd()`: is itself uasm-generated, by
  `build_setup_pgd()`; `check_switch_mmu_context()` calls it through
  `TLBMISS_HANDLER_SETUP_PGD()`.
- `mm_context_t`: a typedef of an anonymous struct in
  `arch/mips/include/asm/mmu.h`; there is no struct tag of that name.
- `asid_cache` in `struct cpuinfo_mips`: without MMID it is that CPU's
  ASID allocator (last ASID plus version); with `cpu_has_mmid` it holds the
  context value (MMID plus version) active on that CPU, and the allocator's
  version lives in `mmid_version` in `arch/mips/mm/context.c`.
- CPU topology: `struct cpuinfo_mips` has no core or VPE field; cluster, core
  and VP are packed in `globalnumber` and read with `cpu_cluster()`,
  `cpu_core()`, `cpu_vpe_id()`; `cpus_are_siblings()` compares `package` and
  `globalnumber` with the VP bits masked off.
- `$28`: holds the `struct thread_info` pointer, not a stack pointer;
  `SAVE_SOME` recomputes it from `sp` only on entry from user mode.
- `kernelsp[]` in `arch/mips/kernel/setup.c`: the kernel stack pointer loaded
  on entry from user mode; `resume()` writes it for the incoming task.
- Status CU0 bit: `SAVE_SOME` in `arch/mips/include/asm/stackframe.h` uses it
  as the "already on a kernel stack" flag; `CLI`, `STI` and `KMODE` set it.
- `struct pt_regs` instances: `task_pt_regs()` is the user-entry frame near
  the top of the task stack; `thread_info.regs` points at the frame of the
  interrupt in progress and is what `get_irq_regs()` returns.
- `thread.fpu` and the `bd_emu_frame`, `bd_emu_branch_pc`, `bd_emu_cont_pc`
  fields of `struct thread_struct`: exist only under
  `CONFIG_MIPS_FP_SUPPORT`.
- DSP state: not lazy; `switch_to()` in `arch/mips/include/asm/switch_to.h`
  runs `__save_dsp()` and `__restore_dsp()` on every switch when
  `cpu_has_dsp`, so `thread.dsp` of `current` is stale until saved.
- Watch registers: under `CONFIG_HARDWARE_WATCHPOINTS`, `__restore_watch()`
  loads them from `thread.watch` on every switch to a task with
  `TIF_LOAD_WATCH`; otherwise it is an empty macro.
- CPU interrupt controller: there is no arch/mips/kernel/irq_cpu.c;
  `mips_cpu_irq_init()` and the weak `plat_irq_dispatch()` are in
  `drivers/irqchip/irq-mips-cpu.c`.
- GIC below a CPU line: holds only when `cpu_has_veic` is false; in EIC mode
  `drivers/irqchip/irq-mips-gic.c` installs its dispatcher with
  `set_vi_handler()` and bypasses the CPU irq domain.
- CPS boot config: `struct cluster_boot_config` (array
  `mips_cps_cluster_bootcfg`) points to an array of
  `struct core_boot_config`, each of which points to an array of
  `struct vpe_boot_config`; `mips_cps_get_bootcfg()` in
  `arch/mips/kernel/cps-vec.S` walks all three by the constants from
  `arch/mips/kernel/asm-offsets.c`.
- Boot memory map: there is no boot_mem_map here; platforms and
  `arch/mips/kernel/setup.c` call `memblock_add()` directly, platforms from
  `prom_init()` or `plat_mem_setup()`.
