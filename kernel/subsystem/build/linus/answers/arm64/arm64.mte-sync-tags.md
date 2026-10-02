- `__sync_cache_and_tags()`: static inline in
  `arch/arm64/include/asm/pgtable.h`; its only caller is `__set_ptes_anysz()`,
  which passes `nr * stride` pages and calls it before the first store.
- `mte_sync_tags()` is called only if all four hold: `system_supports_mte()`,
  `pte_access_permitted_no_overlay(pte, false)`, `!pte_special(pte)`,
  `pte_tagged(pte)`.
- `pte_access_permitted_no_overlay()` with `write` false: tests `PTE_VALID`
  and `PTE_USER` only; unlike `pte_access_permitted()` it does not read
  `POR_EL0`.
- Ordering barrier: the `smp_wmb()` at the end of `mte_sync_tags()` in
  `arch/arm64/kernel/mte.c`, separate from the one in `set_page_mte_tagged()`.
- That `smp_wmb()`: runs on the hugetlb and the normal path, also when this
  caller lost `try_page_mte_tagging()` and wrote no tags.
- PTE store after it: `__set_pte_nosync()`, a `WRITE_ONCE()`;
  `__set_pte_complete()` emits no barrier for a user PTE.
- Hugetlb folio in `mte_sync_tags()`: `nr_pages` is ignored;
  `folio_nr_pages()` pages are cleared, starting at `pte_page(pte)`.
