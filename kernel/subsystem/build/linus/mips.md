# MIPS Subsystem Details

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| TLB maintenance, R3000 class | `arch/mips/mm/tlb-r3k.c` | built under `CONFIG_CPU_R3K_TLB` |
| TLB maintenance, every other CPU | `arch/mips/mm/tlb-r4k.c` | no R8000 file and no per-vendor file; built by three `Makefile` lines, and `CONFIG_CPU_R4K_CACHE_TLB` is off for `CONFIG_CPU_SB1` and `CONFIG_CPU_CAVIUM_OCTEON`; has entry points `tlb-r3k.c` lacks, for example `add_temporary_entry()`, `has_transparent_hugepage()` |
| Cross-CPU TLB flush | `arch/mips/kernel/smp.c` | without `CONFIG_SMP`, `arch/mips/include/asm/tlbflush.h` maps the calls to the local ones, and `flush_tlb_mm()` to `drop_mmu_context()` |
| TLB exception handler generator | `arch/mips/mm/tlbex.c` | one file for R3000, R4000 and Loongson-3; the load, store and modify handlers and `tlbmiss_handler_setup_pgd` land in the placeholders in `arch/mips/mm/tlb-funcs.S`, the refill handler is copied to `ebase`; slow path is `arch/mips/mm/tlbex-fault.S`; the non-static builders, for example `build_get_pmde64()`, are declared in `arch/mips/include/asm/tlbex.h` |
| Assembler for the generator | `arch/mips/mm/uasm.c` | never compiled alone: included by `uasm-mips.c` or `uasm-micromips.c`, of which `CONFIG_CPU_MICROMIPS` selects one; the only header is `arch/mips/include/asm/uasm.h` |
| Address space id allocation | `arch/mips/mm/context.c` | holds both the ASID path, `get_new_mmu_context()`, and the MMID allocator; `arch/mips/include/asm/mmu_context.h` has no allocator, only the inline callers, for example `switch_mm()`, `drop_mmu_context()` |
| TLB instruction wrappers | `arch/mips/include/asm/mipsregs.h` | no file of their own, they sit with the CP0 accessors; the `ginvt` wrappers are apart, in `arch/mips/include/asm/ginvt.h` |
| Hazard barriers | `arch/mips/include/asm/hazards.h` | for C and `.S` sources, not for generated code; the after-write barrier is `tlbw_use_hazard()`; generated handlers get theirs from `tlbex.c`, see `build_tlb_write_entry()` |
| Invalid entry values and wired count | `arch/mips/include/asm/tlb.h` | one file does both: `UNIQUE_ENTRYHI()`, `UNIQUE_GUEST_ENTRYHI()`, `num_wired_entries()`; `arch/mips/include/asm/tlbmisc.h` only declares `add_wired_entry()` |
| TLB dump helpers | `arch/mips/lib/dump_tlb.c`, `arch/mips/lib/r3k_dump_tlb.c` | not under `arch/mips/mm/`; chosen by `CONFIG_CPU_GENERIC_DUMP_TLB` and `CONFIG_CPU_R3000`; both define `dump_tlb_all()` and `dump_tlb_regs()` |
| CPU probing that sizes the TLB | `arch/mips/kernel/cpu-probe.c`, or `arch/mips/kernel/cpu-r3k-probe.c` under `CONFIG_CPU_R3K_TLB` | exactly one is built; the size is field `tlbsize` of `struct cpuinfo_mips`; `kvm_vz_enable_virtualization_cpu()` and `kvm_vz_disable_virtualization_cpu()` in `arch/mips/kvm/vz.c` rewrite `tlbsize` and `tlbsizevtlb` on Octeon III and are the only setters of `guest.tlbsize` |
| KVM TLB routines | `arch/mips/kvm/tlb.c` | `obj-y`: built into the kernel under `CONFIG_KVM`, not into the kvm module; defines `kvm_vz_save_guesttlb()` and `kvm_vz_load_guesttlb()`; guest VTLB resizing is in `arch/mips/kvm/vz.c`; KVM's refill handler is generated in `arch/mips/kvm/entry.c`, with the `tlbex.c` builders except under `CONFIG_CPU_LOONGSON64`; root TLB fault handling is in `arch/mips/kvm/mmu.c` |

## TLB entries and primitives

**Hazard barriers and instruction wrappers**

| Barrier | After | Before |
|---|---|---|
| `mtc0_tlbw_hazard()` | write of EntryHi, EntryLo0/1, Index, PageMask, MemoryMapID or GuestCtl1 | `tlb_write_indexed()`, `tlb_write_random()`, `tlbinvf()`, `tlb_probe()`, `ginvt_mmid()` |
| `mtc0_tlbr_hazard()` | `write_c0_index()` | `tlb_read()` |
| `tlb_probe_hazard()` | `tlb_probe()` | `read_c0_index()` |
| `tlb_read_hazard()` | `tlb_read()` | read of EntryHi, EntryLo0/1, PageMask, GuestCtl1 |
| `tlbw_use_hazard()` | the last TLB write of a routine or loop | return to code that may use the mapping |
| `back_to_back_c0_hazard()` | `mtc0` | `mfc0` of the same register |

- `mtc0_tlbw_hazard()` and `mtc0_tlbr_hazard()`: identical expansion in every
  branch of `arch/mips/include/asm/hazards.h`.
- `tlbw_use_hazard()`, `tlb_read_hazard()` and `tlb_probe_hazard()`: identical
  to each other in every branch.
- Guest wrappers such as `guest_tlb_probe()` and `guest_tlb_write_indexed()`:
  take the same barriers; `hazards.h` has no guest variants. See
  `arch/mips/kvm/tlb.c`.
- `tlbw_use_hazard()` relative to the EntryHi/PageMask restore: not uniform.
  `local_flush_tlb_page()` restores after it;
  `kvm_vz_local_flush_roottlb_all_guests()` restores before it.
- Empty TLB, irq and `back_to_back_c0_hazard()` barriers: under
  `CONFIG_MIPS_ALCHEMY`, `CONFIG_CPU_CAVIUM_OCTEON`, `CONFIG_CPU_LOONGSON2EF`,
  `CONFIG_CPU_LOONGSON64`, `CONFIG_CPU_R10000`, `CONFIG_CPU_R5500`.
- `CONFIG_CPU_CAVIUM_OCTEON` and `CONFIG_CPU_LOONGSON64`: both set
  `CONFIG_CPU_MIPSR2`, but the first `#if` excludes them from the `ehb` branch.
- `CONFIG_CPU_SB1`: every barrier of that group is empty except
  `irq_disable_hazard()`; `irq_enable_hazard()` is empty.
- Final `#else` branch (R4000 class): no barrier is empty.
- `enable_fpu_hazard()` and `disable_fpu_hazard()`: chosen by a separate `#if`;
  the only empty one is `disable_fpu_hazard()` under `CONFIG_CPU_SB1`.
- `CONFIG_WAR_MIPS34K_MISSED_ITLB`: a promptless `bool` in `arch/mips/Kconfig`
  that nothing in this tree selects, so `tlb_read()` builds as a bare `tlbr`.
- `tlb_read()` erratum block, if the symbol were set: `dvpe`, `ehb`, then
  `instruction_hazard()`; it does not call `mips_ihb()`.
- `arch/mips/mm/tlb-r3k.c`: uses no `hazards.h` barrier; it has its own
  one-`nop` `BARRIER` macro.
- Generated handlers in `arch/mips/mm/tlbex.c`: the padding does not come from
  `hazards.h`. `build_tlb_write_entry()` with `cpu_has_mips_r2_r6` emits only
  an `ehb`, and only if `cpu_has_mips_r2_exec_hazard`; on other CPUs the
  padding is chosen by `current_cpu_type()`. `build_tlb_probe_entry()` chooses
  by `current_cpu_type()`.

**Invalidated entry values**

- `UNIQUE_GUEST_ENTRYHI()`: base is `CKSEG1`; `UNIQUE_ENTRYHI()` uses `CKSEG0`.
  Both come from `_UNIQUE_ENTRYHI()` in `arch/mips/include/asm/tlb.h`.
- `MIPS_ENTRYHI_EHINV`: ORed in by `_UNIQUE_ENTRYHI()` itself when
  `cpu_has_tlbinv`; callers add nothing. `cpu_has_xpa` plays no part.
- Distinctness: holds only among entries written through the macro with
  different indexes; it says nothing about values firmware left in the TLB.
- `local_flush_tlb_all()` with `cpu_has_tlbinv` and a wired count of 0: writes
  no `UNIQUE_ENTRYHI()` value; it uses `tlbinvf()` instead.
- `build_huge_handler_tail()` in `arch/mips/mm/tlbex.c`, when `cpu_has_ftlb`
  and its `flush` argument is non-zero: ORs `MIPS_ENTRYHI_EHINV` into the live
  EntryHi, writes the entry, then clears the bit. The VPN2 is not made unique
  there.
- `arch/mips/mm/tlb-r3k.c`: uses neither macro. Only `local_flush_tlb_from()`
  writes a per-index value; the probe-based flushes write plain `KSEG0` for
  every entry.

**PageMask invariants**

- `PM_DEFAULT_MASK`: one of five values, `PM_4K`, `PM_8K`, `PM_16K`, `PM_32K`
  or `PM_64K`, chosen in `arch/mips/include/asm/mipsregs.h` by
  `CONFIG_PAGE_SIZE_4KB`, `CONFIG_PAGE_SIZE_8KB`, `CONFIG_PAGE_SIZE_16KB`,
  `CONFIG_PAGE_SIZE_32KB` or `CONFIG_PAGE_SIZE_64KB`.
- Flush routines in `arch/mips/mm/tlb-r4k.c`, `__kmap_pgprot()` and
  `kunmap_coherent()`: never write PageMask; the entry they write takes its
  size from whatever the register holds.
- Restore from a saved `read_c0_pagemask()` value: for example
  `add_wired_entry()`, `add_temporary_entry()`, `dump_tlb()`,
  `kvm_vz_local_flush_roottlb_all_guests()`.
- Restore by writing the constant `PM_DEFAULT_MASK`: for example the huge path
  of `__update_tlb()`, `has_transparent_hugepage()`, `r4k_tlb_uniquify()`,
  `build_restore_pagemask()`.
- `tlb_read()`: loads PageMask from the entry read, so a routine that only
  reads the TLB must also restore it.
- `r4k_tlb_uniquify_write()`: writes `PM_4K`, not `PM_DEFAULT_MASK`;
  `r4k_tlb_uniquify()` writes `PM_DEFAULT_MASK` back after it returns.
- `build_loongson3_tlb_refill_handler()`: emits a write of `PM_DEFAULT_MASK`
  after the `tlbwr` of every refill, huge page or not.
- Restore relative to `tlbw_use_hazard()`: not uniform. `__update_tlb()`
  restores after it; `build_huge_tlb_write_entry()` emits the restore straight
  after `build_tlb_write_entry()`.
- CPU that cannot hold `PM_DEFAULT_MASK`: `r4k_tlb_configure()` writes it,
  calls `back_to_back_c0_hazard()`, reads it back and calls `panic()` on a
  mismatch.

**Wired entries**

- `__kmap_pgprot()` in `arch/mips/mm/init.c`: the body of both
  `kmap_coherent()` and `kmap_noncoherent()`.
- `__kmap_pgprot()` and `kunmap_coherent()`: do not call `htw_stop()` or
  `htw_start()`; `add_wired_entry()` does.
- `__kmap_pgprot()` compared with `add_wired_entry()`: writes no PageMask and
  does not call `local_flush_tlb_all()` afterwards.
- `cpu_has_mmid`: `__kmap_pgprot()` and `add_wired_entry()` write the entry
  under `MMID_KERNEL_WIRED` and restore the old MemoryMapID;
  `kunmap_coherent()` does not touch MemoryMapID.
- **Unsafe usage**: adding or removing a wired entry (changing the wired count
  and writing the slot) with interrupts enabled.
  - Unsafe: `__kmap_pgprot()` has a second set of fixmap colours for
    `in_interrupt()`, so an interrupt can add its own entry between the read
    of the count and the `tlb_write_indexed()`; its `kunmap_coherent()` leaves
    Index, EntryLo0 and EntryLo1 overwritten.
  - Safe: `local_irq_save()` from the EntryHi save to the EntryHi restore, as
    `__kmap_pgprot()`, `kunmap_coherent()` and `add_wired_entry()` do.
- **Unsafe usage**: an open-coded remove that is not the exact inverse of the
  latest add on the same CPU.
  - Unsafe: `kunmap_coherent()` invalidates index `num_wired_entries() - 1`
    whatever it holds, so an `add_wired_entry()` between map and unmap makes
    the unmap drop the wrong entry.
  - Safe: strictly nested pairs with no migration, as in
    `copy_to_user_page()`; `__kmap_pgprot()` calls `preempt_disable()` and
    `pagefault_disable()`, and `kunmap_coherent()` undoes both.
- **Potentially unsafe usage**: taking the count or index from
  `read_c0_wired()`.
  - Unsafe: when `cpu_has_mips_r6` can be true; the upper 16 bits are
    `MIPSR6_WIRED_LIMIT`.
  - Safe: `num_wired_entries()` in `arch/mips/include/asm/tlb.h`, as
    `__kmap_pgprot()` uses.
  - Safe: where the platform override defines `cpu_has_mips32r6` and
    `cpu_has_mips64r6` as 0, as `alchemy_pci_wired_entry()` in
    `arch/mips/pci/pci-alchemy.c` with
    `arch/mips/include/asm/mach-au1x00/cpu-feature-overrides.h`.
- Reset: `r4k_tlb_configure()` writes 0 to Wired. It runs from `tlb_init()` and
  from `r4k_tlb_pm_notifier()` on `CPU_PM_EXIT` and `CPU_PM_ENTER_FAILED`.
- Entries added by `add_wired_entry()`: not permanent across that reset. The
  `local_flush_tlb_all()` that follows starts at index 0, and nothing in
  `arch/mips/mm/tlb-r4k.c` re-adds them.
- `tlb_init()` with the `ntlb=` boot option: sets Wired to
  `current_cpu_data.tlbsize - ntlb` after the reset, so the count can be
  non-zero with no entry added.
- Other writers of 0: `early_tlb_init()` in `arch/mips/bcm47xx/prom.c` and some
  platform setup and reboot code; search for `write_c0_wired`.
- `add_wired_entry()` in `arch/mips/mm/tlb-r3k.c`: never touches Wired. It
  keeps a static counter capped at 8, and `local_flush_tlb_all()` there starts
  at index 8.

## TLB initialisation

**TLB initialisation order**

- Boot CPU: `trap_init()` calls `per_cpu_trap_init(true)`, which calls
  `tlb_init()`, before its first `set_handler()` or `set_except_vector()`;
  the TLB is set up before `trap_init()` installs any vector.
- Boot CPU, during `r4k_tlb_configure()`: `configure_status()` has already
  cleared `ST0_BEV` and, when `cpu_has_mips_r2_r6`,
  `configure_exception_vector()` has written EBase, but `trap_init()` has
  copied no handler to `ebase` yet; the refill handler is copied there by
  `build_tlb_refill_handler()`, at the end of `tlb_init()`.
- `per_cpu_trap_init()`: calls `tlb_init()` unconditionally; no test of
  `tlbsize` or `is_boot_cpu` guards it.
- `tlb_init()` in `arch/mips/mm/tlb-r4k.c`: does not call `setup_pw()`
  itself; `build_tlb_refill_handler()` does, under `cpu_has_ldpte`.
- Secondary CPU: `tlb_init()` still calls `build_tlb_refill_handler()`; only
  the code generation inside it is behind `run_once`, the per-CPU register
  setup in it runs again.
- Return from a power state: `per_cpu_trap_init()` is not called; its only
  callers are `trap_init()` and `start_secondary()`.
- Return from a power state: `cpu_pm_exit()` (for example from
  `cps_nc_enter()` in `drivers/cpuidle/cpuidle-cps.c`) runs
  `r4k_tlb_pm_notifier()`, which calls `r4k_tlb_configure()` and nothing
  else of `tlb_init()`.
- Status and EBase on that path: restored by a separate notifier,
  `trap_pm_notifier()` in `arch/mips/kernel/traps.c`.
- `CONFIG_CPU_R3K_TLB`: `tlb_init()` comes from `arch/mips/mm/tlb-r3k.c` and
  is `local_flush_tlb_from(0)` then `build_tlb_refill_handler()`, with no
  uniquification.

**Uniquifying inherited entries**

- Entries rewritten: every index from `num_wired_entries()` up, duplicated
  or not; `r4k_tlb_configure()`, the only caller, writes Wired to 0 first,
  so that is the whole TLB.
- Helpers: `r4k_tlb_uniquify_read()` only reads; `r4k_tlb_uniquify_write()`
  does every write.
- Values written: `(vpn << VPN2_SHIFT) | asid`, counted up from VPN 0,
  ASID 0; the ASID is incremented first, the VPN when `cpu_asid_mask()` is
  used up.
- Against `UNIQUE_ENTRYHI()`: the VPN is kept below
  `1 << (vmbits - VPN2_SHIFT)`, a user-segment address, while
  `UNIQUE_ENTRYHI()` is `CKSEG0`-based, so no index gives the same value.
- Against entries in the TLB: candidates are compared with the copy made by
  `r4k_tlb_uniquify_read()`, not with `tlb_probe()`.
- Recorded per entry in `struct tlbent`: VPN masked by that entry's own
  PageMask, page size, global bit, ASID (0 when global), wired, index.
- Wired or global entry reached by the candidate: the VPN is moved past the
  entry's whole span, whatever the ASID.
- Non-global entry with the same VPN and ASID: the ASID is incremented.
- User VPN space used up: `WARN_ON()`, `dump_tlb_all()`, and the write pass
  returns with the remaining entries not rewritten.
- EntryHi width: `read_c0_entryhi_native()` and `write_c0_entryhi_native()`
  use the 64-bit register when `cpu_has_64bits`, also with `CONFIG_32BIT`.
- Memory: an array of `tlbsize` `struct tlbent`, allocated and freed on
  each run.
  - `slab_is_available()` true: `kmalloc()` with `GFP_ATOMIC`, `kfree()`.
  - Otherwise: `memblock_alloc_raw()`, `memblock_free()`.
  - It uses neither `kmalloc_array()` nor `memblock_alloc()`.

**Order of uniquification**

- Comparison function: `r4k_entry_cmp()`; there is no r4k_vpn_cmp here.
- Sort key, in order: wired first, global first, ascending VPN, ascending
  ASID, descending page size.
- Candidate: a (VPN, ASID) pair whose VPN never decreases; it is not
  `UNIQUE_ENTRYHI(n)`.
- Cursors: `widx` (wired), `gidx` (global) and `idx` only move forward, and
  the candidate is compared with the entry at each cursor only.
- Relied on: within each group the entries are in ascending VPN order, so
  an entry the cursor has passed is never looked at again.
- Slot written: `tlb_vpns[i].index`; after `sort()` the array position `i`
  is not a TLB index.
- Order of overwriting: sorted order, starting at the first non-wired
  entry, so global entries are replaced before the others.
- After each write: `tlb_vpns[i]` gets the new VPN, ASID and page size, so a
  cursor that reaches it later sees the value now in the TLB.

**Skipping uniquification**

- `r4k_tlb_configure()`: the only test on the call is `!cpu_has_tlbinv`;
  there is no second condition for a TLB that reset leaves clean.
- `r4k_tlb_configure()` tests none of `cpu_has_ftlb`, `cpu_has_mmid` or
  `cpu_has_mips_r6` before the call; the `MIPS_CPU_TLBINV` bit or a platform
  override alone decides.
- Not handled by `r4k_tlb_uniquify()`:
  - FTLB: it writes any VPN to any index and never reads `tlbsizevtlb`.
  - MMID: it takes the ASID from EntryHi with `cpu_asid_mask()` and never
    touches `read_c0_memorymapid()`.
  - R6 without a 4KiB page size: it writes `PM_4K` entries.
- Inherited large pages: handled; the read pass records each entry's
  PageMask and the write pass moves the VPN past the span of an entry it
  steps over.
- Hardware page-table walker: handled; `r4k_tlb_uniquify()` calls
  `htw_stop()` before its read pass and `htw_start()` after its write pass.

**Hardware invalidate support**

- `decode_config4()` in `arch/mips/kernel/cpu-probe.c`: sets
  `MIPS_CPU_TLBINV` only when the `MIPS_CONF4_IE` field equals 2; values 1
  and 3 do not set it.
- IE values: compared as the literal 2; `decode_config4()` does not use
  `MIPS_CONF4_TLBINV` from `arch/mips/include/asm/mipsregs.h`.
- `cpu_probe_loongson()`: sets `MIPS_CPU_TLBINV` for `PRID_IMP_LOONGSON_64C`
  whatever Config4 says.
- `cpu_has_tlbinv`: tests `cpu_data[0].options`, so the boot CPU's probe
  result is used on every CPU.
- Forcing off: only a platform `cpu-feature-overrides.h` that defines
  `cpu_has_tlbinv` as 0; search for the name under
  `arch/mips/include/asm`.
- Command line: no parameter clears it; `noftlb` leaves `MIPS_CPU_TLBINV`
  set.
- `local_flush_tlb_all()` with `cpu_has_tlbinv` and wired entries: no
  `tlbinvf()`; it loops from `num_wired_entries()` with
  `tlb_write_indexed()` of `UNIQUE_ENTRYHI(entry)`, which then carries
  `MIPS_ENTRYHI_EHINV`.

**Duplicate entry machine check**

- `MIPS_CPU_MCHECK`: set in one place, `decode_configs()`; legacy R4000-class
  probe code does not set it.
- `cpu_has_mcheck`: `__isa_ge_or_opt(1, MIPS_CPU_MCHECK)` in
  `arch/mips/include/asm/cpu-features.h`, so it is constant true when
  `MIPS_ISA_REV` is at least 1.
- Platform overrides: `cpu-feature-overrides.h` files force `cpu_has_mcheck`
  to 0 or 1; for example
  `arch/mips/include/asm/mach-loongson64/cpu-feature-overrides.h` forces 0,
  so no handler is installed there although `decode_configs()` sets the bit.
- Without the handler: ExcCode 24 keeps `handle_reserved`, and
  `do_reserved()` panics.
- `do_mcheck()`: calls `dump_tlb_regs()` and `dump_tlb_all()` only when
  `ST0_TS` was set in `regs->cp0_status`; it ends in `panic()`, not `die()`.
- `ST0_TS`: cleared by `configure_status()`, which runs before `tlb_init()`
  in `per_cpu_trap_init()` and again from `trap_pm_notifier()`.

**TLB operations before initialisation**

- **Potentially unsafe usage**: `tlb_write_indexed()` of
  `UNIQUE_ENTRYHI(idx)` into a TLB that holds entries the kernel did not
  write.
  - Unsafe: when `cpu_has_tlbinv` is false and the inherited entries have
    not been rewritten first; an entry at another index can already hold
    the same `CKSEG0`-based value, and the duplicate raises a machine check.
  - Safe: after `r4k_tlb_uniquify()` has moved every entry to a user-segment
    value; `r4k_tlb_configure()` calls it before `local_flush_tlb_all()`.
    It rewrites nothing if its allocation fails, and stops early if the
    user VPNs run out.
  - Safe: when `cpu_has_tlbinv` is true; `UNIQUE_ENTRYHI()` then sets
    `MIPS_ENTRYHI_EHINV`, or `local_flush_tlb_all()` uses `tlbinvf()`, and
    `r4k_tlb_configure()` relies on that when it skips
    `r4k_tlb_uniquify()`.
- Writing back an inherited value: not done; `r4k_tlb_uniquify_read()`
  writes nothing, and `r4k_tlb_uniquify_write()` writes only an EntryHi it
  computed, with EntryLo0/1 of 0.
- Other callers of `tlb_read()` under `arch/mips`: none writes back the
  EntryHi it read; `dump_tlb()` only reads, and
  `kvm_vz_local_flush_roottlb_all_guests()` writes `UNIQUE_ENTRYHI(entry)`.
- `tlb_probe()`: `r4k_tlb_uniquify()` and `local_flush_tlb_all()` never
  call it; `r4k_tlb_uniquify_read()` learns the contents by index with
  `tlb_read()`, between `mtc0_tlbr_hazard()` and `tlb_read_hazard()`.
- `tlb_write_random()`: its only callers under `arch/mips` are the two
  `__update_tlb()` functions, in `arch/mips/mm/tlb-r4k.c` and
  `arch/mips/mm/tlb-r3k.c`; no initialisation code uses it.
- Interrupts: `r4k_tlb_uniquify()` and `r4k_tlb_configure()` do not disable
  them around their TLB accesses; `local_flush_tlb_all()` does, with
  `local_irq_save()`.

## TLB maintenance

**Flushing one entry**

- Saved and restored: EntryHi only, plus MemoryMapID in
  `local_flush_tlb_page()` when `cpu_has_mmid`.
- EntryLo0, EntryLo1 and Index: overwritten and left that way by both
  routines, `local_flush_tlb_page()` and `local_flush_tlb_one()`.
- PageMask: neither routine reads, writes or restores it.
- `cpu_has_mmid` in `local_flush_tlb_page()`: EntryHi gets the bare pair
  address, `write_c0_entryhi(page)`; the identifier goes only to
  `write_c0_memorymapid(cpu_asid(cpu, vma->vm_mm))`. There is no
  mmid_asid_mask in this tree.
- `local_flush_tlb_one()`: has no `cpu_has_mmid` branch and never touches
  MemoryMapID; it loads no ASID or MMID for the probe, so it is only for
  entries with the global bit.
- Micro TLB: both routines flush it after `htw_start()` and before
  `local_irq_restore()`. `flush_micro_tlb_vm()` acts only if the VMA has
  `VM_EXEC`; `flush_micro_tlb()` acts only on `CPU_LOONGSON2EF` and
  `CPU_LOONGSON64`.
- `CONFIG_SMP` with `cpu_has_mmid`: `flush_tlb_page()` and
  `flush_tlb_range()` in `arch/mips/kernel/smp.c` do not call the local
  routines. They load the mm's MMID, run `ginvt_va_mmid()` and `sync_ginv()`,
  and restore MemoryMapID, inside `htw_stop()` and under `preempt_disable()`
  with no `local_irq_save()` of their own; EntryHi is not touched.

**Overwriting a flushed entry**

- EntryLo0 and EntryLo1: zeroed before the `idx < 0` test, so the registers
  are clobbered on a probe miss too; a miss skips only the
  `UNIQUE_ENTRYHI()` write, `tlb_write_indexed()` and their barriers.
- `cpu_has_tlbinv`: the single-entry routines never execute `tlbinvf()`;
  only `local_flush_tlb_all()` does, and only with no wired entries. Here
  the invalid mark comes from `MIPS_ENTRYHI_EHINV`, which `UNIQUE_ENTRYHI()`
  in `arch/mips/include/asm/tlb.h` ORs in.
- PageMask of the overwritten entry: whatever the register holds, since the
  routines do not set it. `r4k_tlb_configure()` sets `PM_DEFAULT_MASK`, and
  code that changes the register puts it back, for example the huge-page
  branch of `__update_tlb()` and `add_wired_entry()`.

**Address space identifiers**

- `cpu_has_mmid` storage: `mm->context.mmid`, an `atomic64_t` that shares a
  union with `asid[NR_CPUS]` in `mm_context_t`
  (`arch/mips/include/asm/mmu.h`). `cpu_context()` then ignores its `cpu`
  argument; MMID-only callers, for example `get_new_mmid()`, pass 0.
- Active MMID per CPU: kept in `cpu_data[cpu].asid_cache`, where 0 means
  none; there is no mmid_cache. `flush_context()` exchanges it for 0 and
  parks the old value in `reserved_mmids`.
- MMID rollover: `flush_context()` executes no ginvt and flushes nothing
  itself; it sets every CPU in `tlb_flush_pending`, and each CPU then runs
  `flush_icache_all()` (if `cpu_has_vtag_icache`) and
  `local_flush_tlb_all()` in its next `check_switch_mmu_context()`.
- `ginvt_mmid()` in `check_switch_mmu_context()`: only under `CONFIG_SMP`
  with `cpu_has_shared_ftlb_entries` and a sibling still pending.
  `ginvt_full()` is used by `flush_tlb_all()` in `arch/mips/kernel/smp.c`,
  not by rollover.
- `get_new_mmu_context()` and `check_mmu_context()` on an MMID system: warn
  and return only with `CONFIG_DEBUG_VM`; without it they run the per-CPU
  ASID code.
- Non-zero context without MMID: not always a live ASID. When the mm has one
  user and is `current->mm`, `flush_tlb_page()` and `flush_tlb_range()` in
  `arch/mips/kernel/smp.c` store 1 (or `!exec`) for other CPUs; the version
  bits are 0, so the next switch allocates a new ASID, while
  `has_valid_asid()` in `arch/mips/mm/c-r4k.c` still sees the mm as used.

**Dropping a context**

- Locking: the body of `drop_mmu_context()` runs under `local_irq_save()` and
  reads `smp_processor_id()` inside; it does not use `get_cpu()`.
- Context 0: no-op, tested before anything else, with or without
  `cpu_has_mmid`.
- `cpu_has_mmid`: the mm keeps its MMID and its context value. The MMID is
  loaded into MemoryMapID, `ginvt_mmid()` and `sync_ginv()` run, and the old
  MemoryMapID is restored; it does not call `local_flush_tlb_all()`.
- `flush_tlb_mm()` in `arch/mips/kernel/smp.c` relies on that invalidate
  reaching other CPUs: with `cpu_has_mmid` it sends no IPI.
- No MMID, "active": decided by `cpumask_test_cpu(cpu, mm_cpumask(mm))`,
  not by `current->mm`.
- No MMID, guarantee: covers the calling CPU only, and the old entries are
  not invalidated; they stay in the TLB under the old ASID, at the latest
  until `local_flush_tlb_all()` runs.
- Callers: `arch/mips` defines no `local_flush_tlb_mm()`. Without
  `CONFIG_SMP`, `flush_tlb_mm()` is a macro for `drop_mmu_context()` in
  `arch/mips/include/asm/tlbflush.h`.
- `local_r4k_flush_cache_page()` in `arch/mips/mm/c-r4k.c` also calls it, in
  place of the icache flush, when the VMA is executable, the flush went
  through a kernel mapping, `cpu_has_vtag_icache` is true and the mm is
  `current->active_mm`.

**Hardware page table walker**

- `htw_stop()` and `htw_start()`: macros in
  `arch/mips/include/asm/pgtable.h`.
- Nesting: counted in `htw_seq` of `struct cpuinfo_mips`, reached through
  `raw_current_cpu_data`. Only the outermost stop clears the
  `MIPS_PWCTL_PWEN_SHIFT` bit and only the matching start sets it.
- Interrupts: each macro wraps its counter update and PWCtl write in its own
  `local_irq_save()`, so the caller need not have interrupts off to call
  them.
- **Unsafe usage**: a `htw_stop()` and `htw_start()` pair across which the
  task can move to another CPU; each CPU's `htw_seq` is then left
  unbalanced.
  - Safe: under `preempt_disable()`, as the `cpu_has_mmid` branch of
    `flush_tlb_page()` in `arch/mips/kernel/smp.c` does.
  - Safe: under `local_irq_save()`, as `local_flush_tlb_page()` does.
- `pte_clear()` in `arch/mips/include/asm/pgtable.h`: brackets its page
  table write with the pair, though it touches no TLB register.
- Generated load, store and modify handlers: do not stop the walker. With
  `cpu_has_htw`, `cpu_has_tlbex_tlbp_race()` in `arch/mips/mm/tlbex.c` makes
  them test Index after the probe and leave if it missed.
- PWBase: written by `htw_set_pwbase()` inside
  `TLBMISS_HANDLER_SETUP_PGD()` in `arch/mips/include/asm/mmu_context.h`,
  not by the generated `tlbmiss_handler_setup_pgd`, which writes
  `C0_PWBASE` only for `cpu_has_ldpte`.
- `arch/mips/kvm/entry.c`: repeats `TLBMISS_HANDLER_SETUP_PGD()` in uasm,
  including the PWBase write.

**Generated exception handlers**

- Load, store and modify handlers: generated in place in `handle_tlbl`,
  `handle_tlbs` and `handle_tlbm`, fixed areas of `FASTPATH_SIZE`
  instructions in `arch/mips/mm/tlb-funcs.S`; no memory is allocated.
- In-place overflow check: runs after generation (`p >= handle_tlbl_end`
  and the like), so the following area is already overwritten when the
  panic fires, and code that fills the area exactly also panics.
- Refill handler: generated in the `tlb_handler` buffer and then copied to
  `ebase`; `build_r3000_tlb_refill_handler()` and
  `build_r4000_tlb_refill_handler()` check the size before the copy.
- `build_r4000_tlb_refill_handler()` on 32-bit kernels and
  `CPU_LOONGSON2EF`: the refill handler starts at `ebase` and may use 64
  instructions, running on through the 0x80 slot.
- `build_r4000_tlb_refill_handler()` on other 64-bit kernels: the refill
  handler starts at `ebase + 0x80`; code past `MIPS64_REFILL_INSNS` is
  folded into the slot before it, at `ebase`.
- `build_loongson3_tlb_refill_handler()`: copies 0x80 bytes to
  `ebase + 0x80` and has no size check.
- Refill handler, how often: built once. All three refill builders are
  inside a `run_once` block of `build_tlb_refill_handler()`, whatever its
  comment says.
- Every call of `build_tlb_refill_handler()`: the XPA/RIXI panic test,
  `output_pgtable_bits_defines()`, `check_pabits()`, the
  `check_for_high_segbits` computation (`CONFIG_64BIT`), then `setup_pw()`,
  `config_xpa_params()` and `config_htw_params()`, each under its feature
  test.
- `cpu_has_3kex`: returns before `setup_pw()`, `config_xpa_params()` and
  `config_htw_params()`.

**Changing TLB code**

- Selection: at build time only, in `arch/mips/mm/Makefile`. `tlb-r4k.o` is
  built for `CONFIG_CPU_R4K_CACHE_TLB`, `CONFIG_CPU_SB1` and
  `CONFIG_CPU_CAVIUM_OCTEON`; `tlb-r3k.o` for `CONFIG_CPU_R3K_TLB`, which
  `CPU_R3000` selects. There is no CPU_TX39XX in this tree.
- `arch/mips/mm/tlb-r3k.c`: not a routine-for-routine twin. It defines no
  `local_flush_tlb_one()`, flushes single pages with one EntryLo, and uses
  neither `htw_stop()` nor `UNIQUE_ENTRYHI()`.
- Copies of the TLB write sequence outside `tlb-r4k.c`: search `arch/mips`
  for `tlb_write_indexed()`. For example `_kvm_mips_host_tlb_inv()` in
  `arch/mips/kvm/tlb.c` and `kunmap_coherent()` in `arch/mips/mm/init.c`.
- `arch/mips/kernel/smp.c` with `cpu_has_mmid`: `flush_tlb_all()`,
  `flush_tlb_range()` and `flush_tlb_page()` use ginvt and never reach
  `tlb-r4k.c`, so a fix to a local routine does not cover them.
- `dump_tlb()` in `arch/mips/lib/dump_tlb.c`: depends on what a flushed
  entry looks like; it skips entries with `MIPS_ENTRYHI_EHINV` (when
  `cpu_has_tlbinv`) and entries whose EntryHi equals `CKSEG0` once the low
  17 bits are masked.
- Dump code, which file: `dump_tlb.o` is built for
  `CONFIG_CPU_GENERIC_DUMP_TLB` (default y unless `CPU_R3000`),
  `r3k_dump_tlb.o` for `CONFIG_CPU_R3000`.
- Dump callers: search for `dump_tlb_all()`. No debugfs, procfs or sysfs
  file in `arch/mips` calls it.
- SysRq `x`: registered in `arch/mips/kernel/sysrq.c`, with enable mask
  `SYSRQ_ENABLE_DUMP`; dumps on every CPU.
- `DEBUG_TLB` in `arch/mips/mm/tlb-r3k.c`: compile-time `printk()` tracing,
  `#undef` by default; `tlb-r4k.c` has no equivalent.

## CPU features and caches

**cpu_has feature macros**

- `cpu_has_` macros: read `cpu_data[0]`, the boot CPU's `struct cpuinfo_mips`,
  through `__opt()`, `__ase()` and `__isa()`; the cache macros such as
  `cpu_has_dc_aliases` read `cpu_data[0].dcache.flags` or
  `cpu_data[0].icache.flags`.
- `cpu_has_fpu`: the one macro that reads `current_cpu_data`, under
  `CONFIG_MIPS_FP_SUPPORT` and unless a platform override defines it as 0;
  `raw_cpu_has_fpu` reads `raw_current_cpu_data`.
- `cpu_probe()` fills `current_cpu_data` on each CPU, but a bit set or
  cleared only in a secondary CPU's entry does not change any `cpu_has_` macro
  other than `cpu_has_fpu`.
- Macros with no `#ifndef`, which a platform cannot override directly:
  `cpu_has_mipsmt_pertccounters` and the shortcut macros, for example
  `cpu_has_mips_r2_r6`.
- Override file: chosen by the `-I` flags in the platform's `Platform` file,
  for example `arch/mips/ath79/Platform`; `arch/mips/Makefile` appends
  `arch/mips/include/asm/mach-generic` last, as the fallback.
- An override need not be a literal: `cpu_has_dc_aliases` is
  `(PAGE_SIZE < 0x4000)` on some platforms, and
  `arch/mips/include/asm/mach-cavium-octeon/cpu-feature-overrides.h` defines
  `cpu_has_rixi` as a run-time test of `cpu_data[0].cputype`.
- An override changes the macro only, not the probed bits; code that tests
  `c->options` or `c->dcache.flags` directly can disagree with the macro.
- Hidden reads of `current_cpu_data`, for example: `cpu_has_fpu` and
  `current_cpu_type()` in `arch/mips/include/asm/cpu-type.h`;
  `boot_cpu_type()` reads `cpu_data[0]`.
- **Potentially unsafe usage**: reading `current_cpu_data`.
  - Unsafe: after boot, in preemptible context where the task can migrate;
    the value may belong to another CPU, also on identical CPUs, because
    `asid_cache`, `udelay_val`, `globalnumber` and `htw_seq` are per-CPU
    state; `debug_smp_processor_id()` warns under `CONFIG_DEBUG_PREEMPT`.
  - Safe: in a context that `check_preemption_disabled()` in
    `lib/smp_processor_id.c` accepts: non-zero preempt count, interrupts
    disabled, per-CPU thread, migration disabled, or `system_state` before
    `SYSTEM_SCHEDULING`.
  - Safe: under `local_irq_save()`, as `local_flush_tlb_all()` in
    `arch/mips/mm/tlb-r4k.c` does.
  - Safe: during early boot, as `cpu_probe()` called from `setup_arch()`.
- `raw_current_cpu_data`: skips the `CONFIG_DEBUG_PREEMPT` check and nothing
  else; where the task can migrate, the value is right only if it is the same
  on every CPU.

**Data cache aliases**

- `__flush_dcache_pages()` exists only under `arch/arc`; on MIPS
  `__flush_dcache_folio_pages()` in `arch/mips/mm/cache.c` does that, called
  by `flush_dcache_folio()` and `flush_dcache_page()` in
  `arch/mips/include/asm/cacheflush.h`.
- Deferral test: made on the `struct address_space`, not on the folio:
  `folio_flush_mapping()` is non-NULL and `mapping_mapped()` is false.
- A folio of a file that has any user mapping is flushed at once, even if
  this folio is mapped nowhere.
- Anonymous and swap-cache folios: `folio_flush_mapping()` returns NULL, so
  they are flushed at once.
- `__update_cache()`: called from `set_ptes()` in
  `arch/mips/include/asm/pgtable.h`, before the PTE is written;
  `update_mmu_cache_range()` calls only `__update_tlb()`.
- `set_ptes()` skips `__update_cache()` when the new PTE is not present, or
  every slot already holds a present PTE with the pfn of the new PTE.
- `__update_cache()`: flushes through `kmap_local_folio()`, the kernel
  address; it does not call `kmap_coherent()`.
- `__update_cache()`: its only early return is for `!pfn_valid()`; it does
  not test `cpu_has_dc_aliases`.
- `kmap_coherent()`: every caller under `arch/mips` tests `folio_mapped()`
  and `!folio_test_dcache_dirty()` first, for example `copy_to_user_page()`
  and `local_r4k_flush_cache_page()` in `arch/mips/mm/c-r4k.c`.
- `cpu_has_dc_aliases` for `kmap_coherent()`: tested in the same expression
  by every caller except `__flush_anon_page()`, where the caller
  `flush_anon_page()` tests it and `__flush_anon_page()` tests
  `pages_do_alias()`.
- `__flush_dcache_folio_pages()` does not call `kmap_coherent()`; it flushes
  the `kmap_local_page()` address.
- Clearing a user page: `clear_user_page()` in
  `arch/mips/include/asm/page.h` writes through the kernel address and
  flushes when `pages_do_alias()`; it does not call `kmap_coherent()`.
- `copy_user_highpage()`: `kmap_coherent()` maps the source only; the
  destination is written through `kmap_atomic()` and flushed when
  `!cpu_has_ic_fills_f_dc` or `pages_do_alias()`.
- `__kmap_pgprot()` checks only the dirty flag; `folio_mapped()` is tested by
  the callers, not inside it.
- **Unsafe usage**: calling `kmap_coherent()` on a folio whose
  `PG_dcache_dirty` is set; the `BUG_ON()` at the top of `__kmap_pgprot()`
  fires.
  - Safe: test `!folio_test_dcache_dirty()` first and fall back to the kernel
    address, as `copy_to_user_page()` does.

## Model gaps

### Other mistakes models make

- Models take other CPUs' contexts to be zeroed by every SMP flush. Without
  MMID, in the branch that sends no IPI, `flush_tlb_mm()` in
  `arch/mips/kernel/smp.c` writes 0, but `flush_tlb_page()` writes 1 and
  `flush_tlb_range()` writes 0 only for a `VM_EXEC` VMA.
- Models take every routine that loads EntryHi for a probe to save the
  register and write it back. `__update_tlb()` in `arch/mips/mm/tlb-r4k.c`
  saves nothing: without MMID it leaves the address in EntryHi with the ASID
  field it read there; with `cpu_has_mmid` it leaves the bare address and
  does not touch MemoryMapID.
- Models take `arch/mips/mm/tlbex.c` to share `UNIQUE_ENTRYHI()` with the
  flush code. It never uses the macro.
- Models take `cpu_has_mmid` to be fixed once the boot CPU is probed.
  `cpu_disable_mmid()` in `arch/mips/kernel/cpu-probe.c` clears
  `MIPS_CPU_MMID` later, reached from `cps_prepare_cpus()` through
  `mips_cm_update_property()`; under `CONFIG_GENERIC_ATOMIC64` the macro is
  the constant 0.
- Models take wired-count setup to be permanent. `r4k_tlb_pm_notifier()`
  calls only `r4k_tlb_configure()`, which writes Wired 0, so the `ntlb=`
  limit set in `tlb_init()` is dropped.
- Models list CONFIG_CPU_XLR among the configurations with empty barriers.
  No such symbol exists here.
- Models know `kmap_coherent()` as the only open-coded wired entry.
  `kmap_noncoherent()` is a second one, called from
  `arch/mips/kernel/pm-cps.c`.
- Models take `dump_tlb_all()` to print every entry. `dump_tlb()` in
  `arch/mips/lib/dump_tlb.c` skips, among others, non-global entries whose
  ASID or MMID is not the current one.
