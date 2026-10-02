- Hugetlb folios: use the same `PG_mte_tagged` and `PG_mte_lock` bits, in
  `folio->flags.f`; there are no HPG_ bits for MTE in
  `enum hugetlb_page_flags`.
- Per-page helpers on a hugetlb folio: `VM_WARN_ON_ONCE()`; the hugetlb folio
  helpers warn on any other folio.
- Hugetlb flags: cleared by `arch_clear_hugetlb_flags()` in
  `arch/arm64/include/asm/hugetlb.h`, called from `add_hugetlb_folio()` and
  `free_huge_folio()`; the MTE part runs only if `system_supports_mte()`.
- Non-hugetlb pages: no arm64 code clears either flag;
  `__free_pages_prepare()` in `mm/page_alloc.c` clears them with the rest of
  `PAGE_FLAGS_CHECK_AT_PREP`.
- `__split_folio_to_order()` in `mm/huge_memory.c`: gives the first page of
  each new folio the `PG_arch_2` and `PG_arch_3` of the original head,
  replacing that page's own bits.
