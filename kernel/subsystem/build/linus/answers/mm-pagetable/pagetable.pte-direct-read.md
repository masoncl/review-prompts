- Generic code under `mm/` has no direct read of a PTE slot; every
  `*ptentp` or `*entry` there points to a copy.
- **Potentially unsafe usage**: dereferencing a `pte_t *`.
  - Unsafe: in generic code when the pointer is a page table slot; the read
    skips the `ptep_get()` override of the architecture.
  - Safe: the pointer is a copy that `ptep_get()` filled, as `ptentp` in
    `folio_pte_batch_flags()` in `mm/internal.h`, which warns if it points into
    a page table.
  - Safe: architecture code whose `ptep_get()` is the generic one, under the
    page table lock, as x86 `ptep_set_access_flags()` in
    `arch/x86/mm/pgtable.c`.
  - Safe: the private accessor of the architecture, as arm64 `__ptep_get()`.
- `ptep_get()` overrides: search `arch/` for `define ptep_get`; arm64 with
  `CONFIG_ARM64_CONTPTE` and powerpc 8xx with `CONFIG_PPC_16K_PAGES` return
  more than the raw word.
