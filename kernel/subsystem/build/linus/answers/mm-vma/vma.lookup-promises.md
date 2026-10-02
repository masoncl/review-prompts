- Guarantees, rechecks and the `NULL` return: models have this right; see
  `lock_vma_under_rcu()` and `vma_start_read()` in `mm/mmap_lock.c`.
- `vmf_anon_prepare()` with `anon_vma` unset under `FAULT_FLAG_VMA_LOCK`:
  `__vmf_anon_prepare()` in `mm/memory.c` returns `VM_FAULT_RETRY` only when
  `mmap_read_trylock()` fails. Otherwise it allocates under the mmap read lock
  and the fault goes on under the VMA lock.
- `vmf_anon_prepare()` returning `VM_FAULT_RETRY`: the wrapper in
  `mm/internal.h` has already called `vma_end_read()`.
- Fallback where the caller cannot block: `mmap_read_trylock()` and give up on
  failure, as `stack_map_lock_vma()` in `kernel/bpf/stackmap.c` does.
