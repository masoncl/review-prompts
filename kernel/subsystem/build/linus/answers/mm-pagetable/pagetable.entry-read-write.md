- `ptep_get_lockless()` is overridden in two places: under
  `CONFIG_GUP_GET_PXX_LOW_HIGH` in `include/linux/pgtable.h`, and on arm64
  under `CONFIG_ARM64_CONTPTE`.
- arm64 `ptep_get()` under `CONFIG_ARM64_CONTPTE`: expects the page table
  lock; `contpte_ptep_get()` reads the neighbours with no consistency check.
- `contpte_ptep_get_lockless()` retries until the whole block is consistent, so
  a lockless read on arm64 needs `ptep_get_lockless()` even though the entry is
  one word.
- Elsewhere `ptep_get_lockless()` is `ptep_get()`, so a wrong choice does not
  fail on x86-64.
- `handle_pte_fault()`: reads `vmf->orig_pte` with `ptep_get_lockless()`; code
  that then rewrites the entry compares it with `pte_same()` after taking the
  lock, for example `handle_pte_fault()` itself, `do_numa_page()` and the
  async branch of `do_uffd_rwp()`.
