- `vma_complete()` on a removed VMA: `__remove_shared_vm_struct()` if
  file-backed, then `vma_mark_detached()`, `uprobe_munmap()` and `fput()` if
  file-backed, `unlink_anon_vmas()`, `mpol_put()`, `vm_area_free()`.
- `vma_complete()` and `commit_merge()`: no check for `close` on the VMA they
  remove.
- `vma_expand()`: its only check is
  `VM_WARN_ON_VMG(remove_next && !can_merge_remove_vma(next), vmg)`, which is
  compiled out without `CONFIG_DEBUG_VM` and does not stop the removal.
- **Unsafe usage**: calling `vma_expand()` with `vmg->next` set,
  `vmg->target != vmg->next` and `vmg->end == vmg->next->vm_end` without
  testing `next` first.
  - Safe: test `can_merge_remove_vma()` and shrink `vmg->end` when it fails,
    as `vma_merge_new_range()` does.
  - Safe: leave `vmg->next` unset, as `relocate_vma_down()` in
    `mm/vma_exec.c` does.
  - Safe: `vmg->target` is `vmg->next`, as in `vma_merge_new_range()` when
    only the right side merges; `vma_expand()` then removes nothing.
- Comment above `anon_vma_compatible()` in `mm/vma.c` says a VMA with `close`
  is refused merging; the code refuses only its removal.
