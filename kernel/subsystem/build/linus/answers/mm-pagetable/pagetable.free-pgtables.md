- Signature: `free_pgtables(tlb, struct unmap_desc *)`; floor and ceiling
  are `pg_start` and `pg_end`, and `mm_wr_locked` is a member
  (`mm/vma.h`).
- hugetlb: no separate path; hugetlb_free_pgd_range is not in this tree and
  every VMA goes to `free_pgd_range()`.
- No TLB flush is required before the call: `unmap_region()` runs
  `unmap_vmas()` and `free_pgtables()` on one gather and finishes it once.
- `tlb_free_vmas()`: first call in `free_pgtables()`; if the gather is not
  `fullmm` and saw a `VM_PFNMAP` or `VM_MIXEDMAP` VMA it flushes the TLB
  before any VMA is unlinked from rmap, so `unmap_mapping_range()` cannot
  miss the VMA while its flush is pending.
- mmap lock: must be held in some mode; `unlink_anon_vmas()` asserts
  `mmap_assert_locked()`.
- Between detach and `free_pgtables()`: rmap walkers still reach the VMA
  through `anon_vma` or `i_mmap` and work on its tables under the PTL; on
  the unmap path the unlink happens inside `free_pgtables()`.
- After the unlink: `free_pgd_range()` clears and frees with no page table
  lock, so code that does not own the mm must not use `pte_offset_map()` and
  the like once the VMA is detached or `mm_users` is zero.
- `try_collapse_pte_mapped_thp()` does `vma_lookup()` first and
  `retract_page_tables()` tests `collapse_test_exit()` for that reason.
- Callers whose VMAs were not detached by munmap: `exit_mmap()` and
  `dup_mmap()` on failure, where the VMAs are still attached and
  `tear_down_vmas()` detaches them afterwards; and `__mmap_new_file_vma()`
  on a failed `mmap_file()`, where the VMA is not yet stored in the tree.
  All three hold the mmap write lock for `free_pgtables()`; the last two
  use `UNMAP_STATE()`.
