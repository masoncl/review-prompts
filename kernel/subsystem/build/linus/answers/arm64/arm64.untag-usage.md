- `find_vma()` in `mm/mmap.c`: passes `addr` straight to `mt_find()`; no VMA
  lookup helper untags.
- **Potentially unsafe usage**: a VMA lookup or range comparison on a
  user-supplied address without `untagged_addr()`.
  - Unsafe: when nothing earlier rejected or stripped a tag; the tagged value
    is above every VMA, so `find_vma()` returns `NULL`.
  - Safe: untag a copy first, as `do_mprotect_pkey()` in `mm/mprotect.c` and
    `arm64_notify_segfault()` in `arch/arm64/kernel/traps.c` do.
  - Safe: a tagged value was rejected when the address was registered, as
    `kvm_set_memory_region()` in `virt/kvm/kvm_main.c` does with
    `mem->userspace_addr != untagged_addr(mem->userspace_addr)`.
  - Safe: the address is left tagged so that the range check fails, as
    `validate_unaligned_range()` in `mm/userfaultfd.c` does against
    `mm->task_size`.
- Entry points that untag: search for `untagged_addr(`; the mm syscalls that
  untag do it in their own file, and `mm/mmap.c` has only the `munmap` one.
- `brk`: the syscall in `mm/mmap.c` does not untag.
- `mm/userfaultfd.c`: has no `untagged_addr()` call.
- `madvise`: untagged by `get_untagged_addr()`, called from
  `madvise_do_behavior()` in `mm/madvise.c`, not in `do_madvise()`.
- `get_untagged_addr()`: uses `untagged_addr()` when `mm` is `current->mm`,
  because only a per-VMA lock may be held and `untagged_addr_remote()` would
  trip its assertion.
- `untagged_addr_remote()`: the generic macro in `include/linux/uaccess.h`;
  it calls `mmap_assert_locked()` and does not take the lock.
- `__get_user_pages()` in `mm/gup.c`: untags `start` itself with
  `untagged_addr_remote()`; `get_user_page_vma_remote()` then calls
  `vma_lookup()` on the address as it was passed, and `__access_remote_vm()`
  in `mm/memory.c` untags before calling it.
- `do_mem_abort()` in `arch/arm64/mm/fault.c`: hands the tagged `far` to the
  handler; `do_page_fault()`, `do_translation_fault()` and `do_bad_area()` each
  untag a local copy.
