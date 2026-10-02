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
