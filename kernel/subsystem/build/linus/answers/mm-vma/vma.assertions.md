With `CONFIG_PER_VMA_LOCK`:

| Helper | mmap read only | mmap write only | VMA read | VMA write | Can fire when |
|---|---|---|---|---|---|
| `mmap_assert_locked()` | yes | yes | no | yes | always |
| `mmap_assert_write_locked()` | no | yes | no | yes | always |
| `vma_assert_write_locked()` | no | no | no | yes | `CONFIG_DEBUG_VM` |
| `vma_assert_locked()` | no | no | yes | yes | `CONFIG_DEBUG_VM` |
| `vma_assert_stabilised()` | yes | yes | yes | yes | `CONFIG_DEBUG_VM` |

- Path reachable under either lock: `vma_assert_stabilised()`. With a
  `struct vm_fault` in hand, `assert_fault_locked()` in `include/linux/mm.h`
  picks the assertion from `FAULT_FLAG_VMA_LOCK`.
- VMA write column: a VMA write lock implies the mmap write lock, so both mmap
  assertions pass under it.
- `mmap_assert_locked()` and `mmap_assert_write_locked()`: compiled in without
  any debug option. `rwsem_assert_held()` and `rwsem_assert_held_write()` use
  lockdep under `CONFIG_LOCKDEP`, otherwise a `WARN_ON()` on the rwsem state
  that any task's hold satisfies.
- `vma_assert_write_locked()`: `VM_WARN_ON_ONCE_VMA()`, a one-time warning, not
  `VM_BUG_ON_VMA()`. Without `CONFIG_DEBUG_VM` the condition is not evaluated,
  so the `mmap_assert_write_locked()` nested in `__vma_raw_mm_seqnum()` does
  not run either.
- `vma_assert_locked()` under `CONFIG_LOCKDEP`: lockdep only decides a pass
  (this task holds the read lock). The failing check is still
  `vma_assert_write_locked()`, so nothing fires without `CONFIG_DEBUG_VM`.
- `vma_assert_locked()` without `CONFIG_LOCKDEP`: passes whenever `vm_refcnt`
  is above 1, which any task's read lock causes.
- `vma_assert_stabilised()` without `CONFIG_LOCKDEP`: passes whenever any task
  holds the mmap lock, tested with `rwsem_is_locked()`.
- `vma_assert_attached()` and `vma_assert_detached()`: plain `WARN_ON_ONCE()`
  on `vma_is_attached()`, compiled in without debug options; empty stubs
  without `CONFIG_PER_VMA_LOCK`.
- `vma_assert_can_modify()`: passes on a detached VMA with no lock; on an
  attached VMA it is `vma_assert_write_locked()`.
