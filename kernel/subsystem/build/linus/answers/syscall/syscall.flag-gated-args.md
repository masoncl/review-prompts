- `vrm->new_addr` when `vrm_implies_new_addr()` is false: not left alone;
  `check_prep_vma()` in `mm/mremap.c` overwrites it with `vrm->addr`, and
  `vrm_set_new_addr()` passes 0 as the hint instead of the field.
- **Unsafe usage**: testing or using `vrm->new_addr` in code that runs before
  the overwrite in `check_prep_vma()` and where neither
  `vrm_implies_new_addr()` nor `MREMAP_FIXED` has been tested; the field still
  holds the caller's raw fifth argument, so the test fails callers that never
  set it.
  - Safe: after the `if (!vrm_implies_new_addr(vrm)) return 0;` in
    `check_mremap_params()`, where the range, alignment and `vrm_overlaps()`
    tests sit.
  - Safe: in `remap_move()`, which `do_mremap()` calls only when
    `vrm_move_only()` has seen `MREMAP_FIXED`.
  - Safe: through `vrm_set_new_addr()`, which tests the helper itself.
