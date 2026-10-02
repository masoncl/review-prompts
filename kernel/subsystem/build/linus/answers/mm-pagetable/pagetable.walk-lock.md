| Value | mmap lock | Each VMA |
|---|---|---|
| `PGWALK_VMA_RDLOCK_VERIFY` | no assertion | `vma_assert_locked()` |

- `vma_assert_locked()`: passes for a VMA read lock and for a VMA write lock.
- `PGWALK_VMA_RDLOCK_VERIFY` drops the mmap lock requirement only for
  `walk_page_vma()`, `walk_page_range_vma()` and
  `walk_page_range_vma_unsafe()`.
- `walk_page_range()` and `walk_page_range_mm_unsafe()`: call `find_vma()`,
  which does `mmap_assert_locked()` itself, whatever `walk_lock` says.
- Without `CONFIG_PER_VMA_LOCK`: `process_vma_walk_lock()` is empty, so
  `PGWALK_WRLOCK` and `PGWALK_WRLOCK_VERIFY` only assert the mmap write lock,
  and `PGWALK_VMA_RDLOCK_VERIFY` asserts nothing.
- `PGWALK_WRLOCK`: `vma_start_write()` runs before `test_walk`, so a VMA that
  `test_walk` skips is write-locked too.
- `walk_page_mapping()`, `walk_kernel_page_table_range()`,
  `walk_kernel_page_table_range_lockless()` and `walk_page_range_debug()`: do
  not call `process_mm_walk_lock()` or `process_vma_walk_lock()`; `walk_lock`
  is ignored there.
