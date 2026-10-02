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
