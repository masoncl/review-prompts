- There is no __alloc_pages_node() here; node-taking forms in
  `include/linux/gfp.h` are, for example, `alloc_pages_node()` and
  `__folio_alloc_node()`.
- `alloc_pages_node_noprof()` and `__folio_alloc_node_noprof()`: no
  `VM_BUG_ON()` or other range check on `nid`.
- `__alloc_pages()` and `__alloc_frozen_pages()`: declared in
  `mm/page_alloc.h`, not `include/linux/gfp.h`, and take a fifth argument
  `alloc_flags` (`ALLOC_DEFAULT` for ordinary callers).
- `alloc_pages_mpol()`: `static` in `mm/mempolicy.c`; the explicit-policy
  entry point is `folio_alloc_mpol()`.
- `alloc_pages()` and `folio_alloc()`: skip the task policy and use
  `default_policy` when `in_interrupt()` or when gfp has `__GFP_THISNODE`; see
  `alloc_frozen_pages_noprof()` in `mm/mempolicy.c`.
- `alloc_pages_bulk_mempolicy()`: task policy, same two exceptions.
- `alloc_pages_bulk()`: no policy, prefers `numa_mem_id()`.
- `vma_alloc_folio()`: uses the task policy when the VMA has none
  (`get_vma_policy()`).
- `vma_alloc_folio()` versus `folio_alloc()` at PMD order with
  `CONFIG_TRANSPARENT_HUGEPAGE`: for a policy that is neither interleave nor
  `MPOL_PREFERRED_MANY` and that allows the preferred node,
  `alloc_pages_mpol()` first tries that node with
  `__GFP_THISNODE | __GFP_NORETRY`, and returns NULL with no fallback if gfp
  lacks `__GFP_DIRECT_RECLAIM`; `folio_alloc()` passes `NO_INTERLEAVE_INDEX`
  and never does this.
- `NUMA_NO_NODE` handling, none of these apply a policy:

| Entry point | `nid == NUMA_NO_NODE` |
|---|---|
| `alloc_pages_node()`, `alloc_pages_bulk_node()` | becomes `numa_mem_id()` |
| `alloc_pages_nolock()` | becomes `numa_node_id()` |
| `__folio_alloc_node()`, `__folio_alloc()`, `__alloc_pages()`, `__alloc_frozen_pages()` | not mapped; with `CONFIG_NUMA`, `node_zonelist()` indexes `node_data[]` with it |

- `___kmalloc_large_node()`, and `alloc_slab_page()` in `mm/slub.c` when
  `allow_spin` is true: `NUMA_NO_NODE` goes to `alloc_frozen_pages_noprof()`
  (task policy), any other node to `__alloc_frozen_pages_noprof()` with a NULL
  nodemask; neither calls `alloc_pages()` or `__alloc_pages()`.
- Slab objects with `NUMA_NO_NODE`: `apply_strict_numa_policy()` substitutes
  `mempolicy_slab_node()` only when the static key `strict_numa` is on (boot
  parameter `slab_strict_numa`).
- `alloc_from_pcs()`: has no policy test of its own; in its object refill,
  `refill_objects()`, only `__refill_objects_any()` calls
  `mempolicy_slab_node()`, to pick the zonelist it walks.
- `warn_if_node_offline()`: only prints; the allocation proceeds.
- **Unsafe usage**: passing a nid that can be `NUMA_NO_NODE` to
  `__folio_alloc_node()`, `__folio_alloc()`, `__alloc_pages()` or
  `__alloc_frozen_pages()`; with `CONFIG_NUMA`, `node_zonelist()` indexes
  `node_data[]` with it and makes no test.
  - Safe: map it first, as `iommu_alloc_pages_node_sz()` does with
    `numa_mem_id()` and `alloc_migration_target()` does with
    `folio_nid(src)`.
  - Safe: `alloc_pages_node()`, which maps it itself.
- **Unsafe usage**: replacing a refcounted allocator with a frozen one, or the
  reverse, and leaving the free side unchanged; `put_page_testzero()` has a
  `VM_BUG_ON_PAGE()` on a zero refcount.
  - Safe: frozen allocation freed with `free_frozen_pages()`, as
    `___kmalloc_large_node()` and `free_large_kmalloc()` pair up.
