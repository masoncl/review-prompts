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
