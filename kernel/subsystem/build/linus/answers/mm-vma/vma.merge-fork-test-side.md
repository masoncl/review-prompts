- Test name: `vma_is_fork_child()` in `mm/vma.c`; there is no
  vma_had_uncowed_parents().
- `is_mergeable_anon_vma()`: `tgt` is `vmg->next` or `vmg->prev`, `src` is
  `vmg->middle`, and the source `anon_vma` is `vmg->anon_vma`.

| Case | VMA tested |
|---|---|
| only source has an `anon_vma` | `vmg->middle` and `vmg->copied_from`; either one forked refuses |
| only target has an `anon_vma` | `tgt` |
| both have one | none; the two pointers must be equal |

- `copy_vma()`: `vma_merge_copied_range()` moves the source VMA from
  `vmg->middle` to `vmg->copied_from`, so a forked mremap source blocks
  the first case.
- `vma_merge_existing_range()`: warns if `vmg->copied_from` is set, under
  `CONFIG_DEBUG_VM`.
