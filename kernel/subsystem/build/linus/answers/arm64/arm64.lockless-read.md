- `contpte_ptep_get_lockless()`: reads the target entry first, not the first
  entry of the block, and returns it as read if it is not valid with
  `PTE_CONT`.
- Block scan: stops as soon as both dirty and young are found; entries after
  that point are neither read nor checked by `contpte_is_consistent()`.
- `ptep_get()`: expects the page table lock; `contpte_ptep_get()` gathers
  bits with no consistency check and no retry.
- Without `CONFIG_ARM64_CONTPTE`: there is no arm64 `ptep_get_lockless()`; the
  generic one in `include/linux/pgtable.h` is a plain `ptep_get()`.
- `pud_offset_lockless()` with the PUD folded: ignores the value `p4d` and
  returns `p4d_to_folded_pud(p4dp, addr)`, computed from the pointer.
- `p4d_offset_lockless()` with the P4D folded: the same, through
  `pgd_to_folded_p4d(pgdp, addr)`.
- `p4d_offset_lockless_folded()`: used in every build with
  `CONFIG_PGTABLE_LEVELS <= 4`; returns `p4d_offset(pgdp, addr)` from the
  original pointer.
- After `p4d_offset_lockless_folded()`: the caller loads the same live entry
  a second time, as the P4D entry; each level still loads it once.
- **Potentially unsafe usage**: passing the address of a local copy of the
  upper entry as `p4dp` or `pgdp` to an offset helper.
  - Unsafe: with the level folded at run time; `p4d_to_folded_pud()` and
    `pgd_to_folded_p4d()` align the pointer down to a page and index it, and
    their `VM_BUG_ON()` checks the pointer against `addr`.
  - Safe: pass the pointer into the live table together with the value read
    from it, as `gup_fast_pud_range()` and `gup_fast_p4d_range()` in
    `mm/gup.c` do.
  - Safe: with `CONFIG_PGTABLE_LEVELS <= 3`, where arm64 defines no
    `pud_offset_lockless()` and the generic one in `include/linux/pgtable.h`
    passes `&(p4d)` to `pud_offset()` in
    `include/asm-generic/pgtable-nopud.h`, which returns the pointer as it is.
