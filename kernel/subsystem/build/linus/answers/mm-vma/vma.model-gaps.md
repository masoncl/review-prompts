- Models take the mm-core entry points to pass `vm_flags_t`. `do_mmap()`,
  `mmap_region()` and `do_brk_flags()` take a `vma_flags_t` by value, and
  `may_expand_vm()` a `const vma_flags_t *`; convert with
  `legacy_to_vma_flags()`.
- Models take `anon_vma_clone()` to have two arguments. It takes a third, an
  `enum vma_operation` (`mm/internal.h`), and `mm/rmap.c` warns, under
  `CONFIG_DEBUG_VM`, when the operation does not match the state of the two
  VMAs.
- Models look for `insert_vm_struct()` and `__vm_munmap()` in `mm/mmap.c`.
  Both are in `mm/vma.c`.
