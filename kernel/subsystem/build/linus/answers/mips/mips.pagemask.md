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
