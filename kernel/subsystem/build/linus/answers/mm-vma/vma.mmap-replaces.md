- Point of no return: `vms_clean_up_area()`, which `__mmap_setup()` calls
  after its last failure return; not `vms_complete_munmap_vmas()` in
  `__mmap_complete()`.
- Failure after `__mmap_setup()` returned 0 (`mmap_prepare`,
  `mmap_action_prepare()`, `vm_area_alloc()`, `vma_iter_prealloc()`, the
  `mmap` hook, `shmem_zero_setup()`): the old mappings are gone and a gap is
  left.
- The gap: `vms_abort_munmap_vmas()` stores NULL over `vms->start` to
  `vms->end - 1`, which is the whole requested range.
- `reattach_vmas()`: only calls `vma_mark_attached()` on each VMA and
  destroys the side tree; it changes no flags and no `locked_vm`, because
  gathering only summed the counters into `struct vma_munmap_struct`.
- `vms_gather_munmap_vmas()` failure: it reattaches on its own error labels;
  `__mmap_setup()` then sets `vms->nr_pages = 0`, so
  `vms_abort_munmap_vmas()` returns at its first test.
- Splits at the range edges: `__split_vma()` in `vms_gather_munmap_vmas()` is
  not undone by any failure path, including the ones that reattach.
- Failure in `mmap_action_complete()`, including an error from the `mapped`
  callback: `mmap_action_finish()` unmaps the new VMA with `do_munmap()`; the
  old VMAs were already freed in `__mmap_complete()`, so a gap results.
