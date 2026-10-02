- `folio_page()`: `&(folio)->page + (n)` in every configuration; nth_page() is
  defined nowhere in this tree.
- Index check: none, with or without `CONFIG_DEBUG_VM`.
- Memmap contiguity inside a folio: guaranteed by `MAX_FOLIO_ORDER` in
  `include/linux/mmzone.h`, which is at most one memory section under
  `CONFIG_SPARSEMEM` without `CONFIG_SPARSEMEM_VMEMMAP`.
- Index beyond the folio under that configuration: the result may not be the
  `struct page` of `folio_pfn(folio) + n`; `page_range_contiguous()` in
  `mm/util.c` is the test for ranges not known to lie in one folio.
- File index: not a valid `n`; `folio_file_page()` in
  `include/linux/pagemap.h` masks it with `folio_nr_pages(folio) - 1`.
- `folio_file_page()` with an index outside the folio: wraps to a page inside
  the folio instead of going out of range.
- `try_to_unmap_one()` and `try_to_migrate_one()` in `mm/rmap.c`: take the pfn
  from the PTE value they read (`pte_pfn()`, or `softleaf_to_pfn()` for a
  non-present entry) and subtract `folio_pfn()`; they do not index with
  `pvmw.pfn`.
- `folio_within_vma()` in `mm/internal.h`: computes no index of a page within
  the folio.
- **Potentially unsafe usage**: `n` derived from a virtual address.
  - Unsafe: when the result is used as the page mapped at that address and
    the offset is taken from a base that is not where page 0 of the folio is
    mapped; `folio_page()` then returns another page.
  - Safe: `folio_zero_user()` in `mm/memory.c` takes the offset from
    `ALIGN_DOWN(addr_hint, folio_size(folio))`, so it is below
    `folio_nr_pages()`, and uses it only to choose the zeroing order.
