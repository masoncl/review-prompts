| Job | Structure | Easy to miss |
|---|---|---|
| What the hook asks the core to do after the VMA exists | `struct mmap_action` in `include/linux/mm_types.h` | embedded as `action` in `struct vm_area_desc`; `__mmap_region()` passes `&desc.action` to `__mmap_new_vma()` and `mmap_action_complete()` |
| An unmap: which VMAs go and the accounting | `struct vma_munmap_struct` in `mm/vma.h` | holds no tree; the detached VMAs are in a side tree reached through a separate `struct ma_state *mas_detach` passed beside it, on the stack in `do_vmi_align_munmap()` and in `struct mmap_state` for mmap |
| An unmap: page-table teardown range | `struct unmap_desc` in `mm/vma.h` | argument of `unmap_region()`, `unmap_vmas()` and `free_pgtables()`; set up by `UNMAP_STATE()`, `unmap_all_init()` or by hand in `vms_clear_ptes()` |
