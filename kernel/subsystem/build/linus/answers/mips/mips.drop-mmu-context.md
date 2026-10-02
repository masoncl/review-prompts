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
