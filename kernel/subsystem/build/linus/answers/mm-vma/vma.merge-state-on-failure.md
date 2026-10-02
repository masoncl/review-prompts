- Restoring: neither `vma_merge_new_range()` nor
  `vma_merge_existing_range()` restores any member on failure, with or
  without `just_expand`.

| Function | Members a failed call can leave changed |
|---|---|
| `vma_merge_existing_range()` | `state`, `next`, `target`, `start`, `end`, `pgoff`, `anon_pgoff`, `__remove_middle`, `__remove_next`, `__adjust_middle_start`, `__adjust_next_start` |
| `vma_merge_new_range()` | `state`, `target`, `start`, `end`, `pgoff`, `anon_pgoff` |
| `vma_expand()` | `__remove_next`, `state` |
| `vma_merge_copied_range()` | `middle` (set NULL), `copied_from` |

- Never written by the functions in the table or by `commit_merge()`:
  `prev`, `anon_vma`, `file`, `policy`, `uffd_ctx`, `anon_name`,
  `vma_flags`.
- `__adjust_middle_start` and `__adjust_next_start`: only ever set to
  true, never cleared at entry.
- Iterator: only the `abort:` label of `vma_merge_existing_range()` sets
  it back to the original start; `commit_merge()` reconfigures it with
  `vma_iter_config()` before the allocation that can fail.
- Reset helper: none in `mm/`; `vmg_set_range()` in
  `tools/testing/vma/tests/merge.c` is test code; it resets the iterator
  and every member in the table except `state` and `copied_from`.
- **Potentially unsafe usage**: passing a vmg to a second merge call, or
  reading its range, after a failed attempt.
  - Unsafe: with no reset in between, `vma_merge_new_range()` warns on a
    set `vmg->target` and `vma_merge_existing_range()` on a set
    `vmg->next`, under `CONFIG_DEBUG_VM`.
  - Unsafe: with no reset in between, a stale `__adjust_next_start` or
    `__adjust_middle_start` is acted on by `commit_merge()` and
    `vmg_adjust_set_range()`.
  - Safe: reset the changed members and the iterator before the next
    call, as `try_merge_new_vma()` in `tools/testing/vma/tests/merge.c`
    does with `vmg_set_range()`.
  - Safe: copy `start`, `end` and `middle` to locals before the attempt,
    as `vma_modify()` does before `split_vma()`.
  - Safe: build a new vmg for each attempt; every caller in `mm/` does,
    with `VMG_STATE()`, `VMG_VMA_STATE()` or `VMG_MMAP_STATE()`.
  - Safe: set the iterator range again before storing, as
    `__mmap_new_vma()` does with `vma_iter_config()`.
