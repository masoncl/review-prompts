- `mm->page_table_lock`: not taken by `expand_downwards()` or
  `expand_upwards()` themselves; `__anon_vma_prepare()`, reached through
  `anon_vma_prepare()`, takes it while it sets `vma->anon_vma`.
- Growers exclude each other through the mmap write lock, which both
  functions check with `mmap_assert_write_locked()`.
- `expand_stack_locked()`: takes no lock and upgrades nothing; it calls the
  grow function, so its caller must hold the mmap write lock.
- File-backed growable VMA: excluded at creation; `do_mmap()` returns
  `-EINVAL` when `vma_flags_can_grow()` for any file mapping, for anonymous
  `MAP_SHARED` and for `MAP_DROPPABLE`.
- `expand_downwards()` and `expand_upwards()` have no file test of their
  own and do not take `i_mmap_rwsem`; they rely on that `do_mmap()` test.
- Anon tree update: done with `anon_rmap_tree_pre_update_vma()` and
  `anon_rmap_tree_post_update_vma()` under `anon_vma_lock_write()`, which
  locks the root anon_vma's `rwsem`.
