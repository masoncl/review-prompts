- There is no walk_page_range_novma() and no walk_page_range_mm() here. The
  entry points besides `walk_page_range()`, `walk_page_range_vma()`,
  `walk_page_vma()` and `walk_page_mapping()` are:

| Entry point | Scope | Asserted on the caller | `test_walk` |
|---|---|---|---|
| `walk_page_range_mm_unsafe()` | as `walk_page_range()` | as `walk_page_range()` | called |
| `walk_page_range_vma_unsafe()` | as `walk_page_range_vma()` | as `walk_page_range_vma()` | not called |
| `walk_kernel_page_table_range()` | `init_mm`, or `pgd` if given; no VMAs | `mmap_assert_locked(&init_mm)` | not called |
| `walk_kernel_page_table_range_lockless()` | same | nothing | not called |
| `walk_page_range_debug()` | any `mm`, or `pgd` if given; no VMAs | `mmap_assert_write_locked()` on `mm` and on `init_mm` | not called |

- `walk_page_range_debug()`: does not forward to
  `walk_kernel_page_table_range()`; it calls `walk_pgd_range()` itself, for
  `init_mm` too.
- `walk_kernel_page_table_range_lockless()`: takes and asserts no lock, so
  excluding every concurrent change to the range is left to the caller.
- No-VMA walks: take no PTE lock, split no huge entry, and leave `walk->vma`
  NULL; leaf and non-present PUDs and PMDs reach `pud_entry` and `pmd_entry`
  and are then skipped.
- `walk_page_mapping()`: iterates with `mapping_rmap_tree_foreach()`; there is
  no vma_interval_tree_foreach() in this tree.
- `walk_page_mapping()`: passes the whole VMA, `vm_start` to `vm_end`, to
  `test_walk`, not the clipped range it then walks.
