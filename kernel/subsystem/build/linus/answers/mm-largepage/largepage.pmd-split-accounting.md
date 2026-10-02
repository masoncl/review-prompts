- Split without `freeze`: `folio_add_anon_rmap_ptes()` with `RMAP_EXCLUSIVE`
  sets `PG_anon_exclusive` on every subpage.
- Device-private PMD: accounted like a present PMD, but there is no
  `pmdp_invalidate()`; sharing cannot fail for a device-private folio.
- Migration PMD without `freeze`: no reference or mapcount change.
- Migration PMD with `freeze`: `put_page()` still drops one reference;
  `migrate_vma_split_unmapped_folio()` takes one first for that reason.
- Invalidate: `pmdp_invalidate()`, for a present PMD only;
  `pmdp_invalidate_ad()` is not used here.
- Order for a present PMD:
  1. `pmdp_invalidate()`
  2. share attempt if `freeze` and the page is exclusive
  3. `folio_ref_add()` and `folio_add_anon_rmap_ptes()` if not `freeze`
  4. `pgtable_trans_huge_withdraw()`
  5. PTE writes
  6. `folio_remove_rmap_pmd()`, then `put_page()` if `freeze`
  7. `smp_wmb()`, `pmd_populate()`
- Withdraw after invalidate: powerpc hash keeps per-PMD state in the deposited
  table; see `arch/powerpc/mm/book3s64/hash_pgtable.c`.
