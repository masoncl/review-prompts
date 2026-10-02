- `sysctl_max_map_count`: defined in `mm/util.c`; every check reads it
  through `get_sysctl_max_map_count()` in `mm/internal.h`.
- Checks in MMU builds, complete: `do_mmap()`, `do_brk_flags()`,
  `split_vma()`, `vms_gather_munmap_vmas()` and
  `__check_map_count_against_split()` in `mm/mremap.c`.
- `insert_vm_struct()` and `vma_link()`: no check.
- `mmap_region()`: no check for the VMA it adds; the only check below it is
  the one in `vms_gather_munmap_vmas()`, made when the range lies strictly
  inside one existing VMA.
- `__check_map_count_against_split()` from `prep_move_vma()`: passes when
  `map_count + 2` is at most the limit.
- `__check_map_count_against_split()` from `do_mremap()`: runs on every
  mremap right after the mmap write lock is taken, and passes when
  `map_count + 4` is at most the limit.
- `split_vma()` and `__split_vma()`: both static in `mm/vma.c`;
  `vma_modify()` is the only caller of `split_vma()`, and
  `vms_gather_munmap_vmas()` is the only caller of `__split_vma()` besides
  `split_vma()`.
- `mm/nommu.c` has its own `split_vma()`, which checks with `>=`.
