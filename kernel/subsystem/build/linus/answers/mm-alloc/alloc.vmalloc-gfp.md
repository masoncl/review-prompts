- Scope location: `__vmalloc_area_node()` in `mm/vmalloc.c`, around the static
  `__vmap_pages_range()`; `__vmalloc_node_range_noprof()` applies none itself.
- `vmap_pages_range()` (not static, declared in `include/linux/vmalloc.h`):
  applies no scope.
- `memalloc_apply_gfp_scope()` and `memalloc_restore_scope()`: defined in
  `mm/vmalloc.c`; the first matching row wins:

| Mask | Scope |
|---|---|
| lacks `__GFP_DIRECT_RECLAIM`, or has `__GFP_NORETRY` or `__GFP_RETRY_MAYFAIL` | `memalloc_noreclaim_save()` |
| has `__GFP_IO`, lacks `__GFP_FS` | `memalloc_nofs_save()` |
| lacks both `__GFP_IO` and `__GFP_FS` | `memalloc_noio_save()` |
| anything else | none; returns 0 |

- `GFP_NOFS | __GFP_NORETRY`: gets only the `memalloc_noreclaim_save()` scope,
  because that row is tested first.
- KASAN shadow page tables: `__kasan_populate_vmalloc_do()` in
  `mm/kasan/shadow.c` uses the same two helpers around
  `apply_to_page_range()`.
- `vmalloc_fix_flags()`: clears every bit outside `GFP_VMALLOC_SUPPORTED` and
  does one `WARN_ONCE()`; the allocation goes on.
- `vmalloc_fix_flags()` callers: `__vmalloc_noprof()` and
  `vmalloc_huge_node_noprof()` only.
- Unfiltered entry points: `__vmalloc_node_noprof()`,
  `__vmalloc_node_range_noprof()`, `__kvmalloc_node_noprof()` and
  `vrealloc_node_align_noprof()` pass the mask on as given.
- `GFP_VMALLOC_SUPPORTED`: includes `__GFP_RETRY_MAYFAIL` and
  `__GFP_SKIP_KASAN`; `__GFP_NOWARN` and `__GFP_ACCOUNT` are in it through
  `GFP_NOWAIT` and `GFP_KERNEL_ACCOUNT`.
- Zone bits and `__GFP_HIGHMEM`: outside `GFP_VMALLOC_SUPPORTED`, so the two
  filtered entry points strip them; `vmalloc_32_noprof()` passes
  `GFP_VMALLOC32` through the unfiltered `__vmalloc_node_noprof()`.
- `__GFP_SKIP_KASAN` from the caller, under hardware tag-based KASAN:
  `__vmalloc_node_range_noprof()` skips `kasan_unpoison_vmalloc()` and does not
  add `__GFP_SKIP_KASAN | __GFP_SKIP_ZERO` or change `prot`.
- `__GFP_NOFAIL` with a mask that lacks `__GFP_DIRECT_RECLAIM`:
  `__vmalloc_area_node()` sets `nofail = false`, so the mapping step is not
  retried.
