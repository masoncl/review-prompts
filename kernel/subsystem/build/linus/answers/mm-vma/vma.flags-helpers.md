- Rows for `vm_flags_init()`, `vm_flags_reset()`, `vm_flags_set()`,
  `vm_flags_clear()`, `vm_flags_mod()` and `__vm_flags_mod()`: models have
  these right; see `include/linux/mm.h`. The rows below are the rest.

| Helper | Bits already set | VMA write lock |
|---|---|---|
| `vma_flags_reset_once()` | replaced; word 0 with `WRITE_ONCE()` | neither |
| `vma_set_flags()`, `vma_set_flags_mask()` | kept, new bits ORed in | neither |
| `vma_clear_flags()`, `vma_clear_flags_mask()` | kept, except those named | neither |
| direct `vma->flags = x` | replaced | neither |
| `vma_set_atomic_flag()` | kept, one bit set with `set_bit()` | neither; `vma_assert_stabilised()` |
| `vma_desc_set_flags()`, `vma_desc_clear_flags()` | kept, set or cleared in `desc->vma_flags` | neither; only the desc changes |

- There is no vm_flags_reset_once() here; `vma_flags_reset_once()` does that
  job, takes a `vma_flags_t *`, and has no assertion.
- Bitmap spelling of `vm_flags_reset()`: none that asserts; `mm/` assigns
  `vma->flags` after `vma_start_write()`, as `madvise_update_vma()` does.
- `vma_set_atomic_flag()`: accepts only bits in `VM_ATOMIC_SET_ALLOWED`
  (`VM_MAYBE_GUARD`); any other bit hits `WARN_ON_ONCE()` and is not set.
- Without `CONFIG_PER_VMA_LOCK`: `vma_start_write()` is an empty stub, so
  `vm_flags_set()`, `vm_flags_clear()` and `vm_flags_mod()` make no lock check
  at all; `vma_assert_write_locked()` becomes `mmap_assert_write_locked()`.
- With `CONFIG_PER_VMA_LOCK`: the mmap write lock assertions inside
  `vma_start_write()` are in `__vma_raw_mm_seqnum()` in
  `include/linux/mmap_lock.h` and in `__vma_start_exclude_readers()` in
  `mm/mmap_lock.c`.
