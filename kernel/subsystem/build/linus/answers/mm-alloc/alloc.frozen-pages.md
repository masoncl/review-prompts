- Buddy frozen allocators: declared in `mm/page_alloc.h`, not in
  `mm/internal.h`. `__alloc_frozen_pages_noprof()` takes five arguments.
- Nolock pair: `alloc_frozen_pages_nolock_noprof()` and
  `free_frozen_pages_nolock()`, same header.
- Frozen contiguous allocators exist and are public, in `include/linux/gfp.h`:
  `alloc_contig_frozen_range_noprof()`, `alloc_contig_frozen_pages_noprof()`,
  `free_contig_frozen_range()`.
- Frozen CMA: `cma_alloc_frozen()`, `cma_alloc_frozen_compound()`,
  `cma_release_frozen()` in `include/linux/cma.h`.

| Allocator | Count | Compound |
|---|---|---|
| `alloc_contig_range_noprof()`, `alloc_contig_pages_noprof()` | 1 on every page | never; `__GFP_COMP` is rejected with `WARN_ON()` |
| `alloc_contig_frozen_range_noprof()`, `alloc_contig_frozen_pages_noprof()` without `__GFP_COMP` | 0 on every page | no |
| the same with `__GFP_COMP` | 0 | one compound page |
| `cma_alloc()` | 1 on every page | no |
| `cma_alloc_frozen_compound()` | 0 | yes |

- Frozen range with `__GFP_COMP`: the range must be a power of two and match
  the isolated range exactly, else `-EINVAL`; the order may exceed
  `MAX_PAGE_ORDER` up to `MAX_FOLIO_ORDER`.
- `free_contig_range()`: warns and frees nothing when given a compound head.
- `free_contig_frozen_range()`: frees both kinds; a compound frozen page may
  also go straight to `free_frozen_pages()`.
- There is no folio_alloc_gigantic(); hugetlb uses
  `alloc_gigantic_frozen_folio()` in `mm/hugetlb.c`.
