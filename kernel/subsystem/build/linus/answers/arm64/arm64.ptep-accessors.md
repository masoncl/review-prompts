- `mm_is_user()` in `arch/arm64/mm/contpte.c`: false for `init_mm` and the EFI
  mm; `__contpte_try_fold()` and `__contpte_try_unfold()` return there, so a
  public accessor never converts a kernel block.
- Public setters strip `PTE_CONT` from the value they are given, with
  `pte_mknoncont()`: `set_pte()`, `set_ptes()`, `ptep_set_access_flags()`.
- `ptep_get()`: has no mm test; on any valid entry with `PTE_CONT`, kernel
  ones included, it returns `contpte_ptep_get()`, the entry with access and
  dirty gathered from the block.
- `set_pte()`: cannot unfold (no mm, no address); it warns once if the entry
  it overwrites is valid with `PTE_CONT`.
- Without `CONFIG_ARM64_CONTPTE` the public names are `#define`s of the `__`
  forms, so a wrong choice changes nothing in such a build.
- Under `arch/arm64/mm/` the only public calls are `get_and_clear_ptes()` in
  `modify_prot_start_ptes()` and `set_ptes()` in `modify_prot_commit_ptes()`,
  both on a user mm.
- **Potentially unsafe usage**: a public accessor that writes an `init_mm` or
  EFI mm entry.
  - Unsafe: when the entry or the new value carries `PTE_CONT`; the bit is
    stripped from the value, nothing is unfolded, and one entry of a live
    block is rewritten on its own.
  - Safe: when neither carries `PTE_CONT`, as `set_pte_at()` in
    `vmap_pte_range()` in `mm/vmalloc.c`; contiguous sizes go to
    `set_huge_pte_at()` there. `mm_is_user()` and `pte_mknoncont()` in
    `set_ptes()` define the limit.
