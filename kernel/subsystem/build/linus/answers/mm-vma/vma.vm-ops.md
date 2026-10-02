- `struct vm_operations_struct`: defined in `include/linux/mm.h`.
- `mapped`, `may_split`, `mremap` and `mprotect` return `int`; `open` and
  `close` return `void`.

| Callback | Called from | When | Locks | Failure |
|---|---|---|---|---|
| `mapped` | `call_vma_mapped()` in `mm/util.c`, via `mmap_action_complete()` | file has `mmap_prepare` and `__mmap_region()` allocated a new VMA (not on merge); after the VMA is in the tree, after `__mmap_complete()` and after the mmap action succeeded | mmap write lock, VMA write-locked | `mmap_action_finish()` calls `do_munmap()` on the new VMA, so `close` runs; mmap returns the error or `action->error_override` |
| `may_split` | `__split_vma()`; also `prep_move_vma()` in `mm/mremap.c` | before anything is allocated or copied | mmap write lock; VMA not necessarily write-locked | the split, or the whole mremap move |
| `mremap` | `copy_vma_and_data()` in `mm/mremap.c` | after `move_page_tables()` moved the full length | mmap write lock | page tables moved back, new range unmapped, mremap fails |
| `mprotect` | `do_mprotect_pkey()` | per VMA, before `mprotect_fixup()` | mmap write lock | loop stops; VMAs already changed stay changed |

- `mapped` from `__compat_vma_mmap()` (`is_compat`): on failure nothing is
  unmapped; the error returns to the legacy `mmap` hook that called it.
- `mapped` receives no VMA: it gets the range, `pgoff`, file and a pointer
  through which it may replace `vm_private_data`.
- `prep_move_vma()`: calls `may_split` once for each end of the moved range
  that lies inside the VMA.
- `may_split` in `__split_vma()`: `vma_start_write()` on both VMAs comes after
  `open`; `mprotect_fixup()` and `vms_gather_munmap_vmas()` write-lock the VMA
  only after the split.
- `mremap`: the test is on `vm_ops` of the old VMA, the argument is the new
  VMA, which is an existing neighbour when `copy_vma()` merged.
- There is no vma_dup() here; `vm_area_dup()` in `mm/vma_init.c` makes the copy
  that `open` is called on.
- `open` in `dup_mmap()` (`mm/mmap.c`): after `vma_iter_bulk_store()`, before
  the file rmap insert and before `copy_page_range()`.
- `close` from `vms_clean_up_area()`: when a new mapping overwrites old VMAs,
  `__mmap_setup()` closes the old VMAs before the new file's `mmap_prepare` or
  `mmap` hook runs.
- `close` from `vms_complete_munmap_vmas()`: with `vms->unlock` (for example
  the munmap syscall) the mmap lock is already downgraded to read.
