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
