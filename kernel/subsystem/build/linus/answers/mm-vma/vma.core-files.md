| Job | File | Not where expected |
|---|---|---|
| Allocate, duplicate, free a VMA | `mm/vma_init.c` | `kernel/fork.c` holds none of it; built as `obj-y`, so `mm/nommu.c` uses it too |
| Split, merge, unmap, body of mmap | `mm/vma.c`, API in `mm/vma.h` | built only with `CONFIG_MMU`; `mmap_region()`, `__mmap_region()` and `do_brk_flags()` are here, not in `mm/mmap.c`; `mm/nommu.c` has its own static `split_vma()` |
| Stack setup for exec | `mm/vma_exec.c` | `relocate_vma_down()`, `create_init_stack_vma()`; `fs/exec.c` keeps the callers `setup_arg_pages()` and `bprm_mm_init()`; no shift_arg_pages() exists |
| mmap and brk syscalls, fork and exit of an mm | `mm/mmap.c` | `vm_mmap_pgoff()` is in `mm/util.c` |
| mmap lock, per-VMA lock | `include/linux/mmap_lock.h`, `mm/mmap_lock.c` | `vma_start_read()` is `static inline` in `mm/mmap_lock.c`, not in the header; `lock_mm_and_find_vma()` is in `mm/mmap_lock.c` |
| Userland tests | `tools/testing/vma/` | there is no tools/testing/vma/vma.c; see `main.c`, `shared.c`, `tests/merge.c`, `tests/mmap.c`, `tests/vma.c` |
