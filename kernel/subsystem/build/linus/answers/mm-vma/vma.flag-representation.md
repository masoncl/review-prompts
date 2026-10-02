- Union in `struct vm_area_struct` (`include/linux/mm_types.h`): exactly two
  members, `const vm_flags_t vm_flags` and `vma_flags_t flags`.
- There is no __vm_flags member here, and no `ACCESS_PRIVATE()` on VMA flags
  outside `tools/testing/vma/`; the `vm_flags_set()` family writes through
  `&vma->flags`.
- `vma->flags` is not const: `vma->flags = x` compiles, and `mm/` does it (for
  example `__mmap_new_vma()` in `mm/vma.c`).
- `struct vm_area_desc`: has only `vma_flags_t vma_flags`; it has no
  `vm_flags` member, so `desc->vm_flags` does not compile.
- Bit numbers: type `vma_flag_t`, spelled only with the prefix `VMA_` and the
  suffix `_BIT`, for example `VMA_READ_BIT`; there is no VM_READ_BIT.
- `VM_PKEY_BIT0` to `VM_PKEY_BIT4`: masks, despite the name.
- Helper names, by the object they take (bits are a variadic list of
  `vma_flag_t` bit numbers such as `VMA_READ_BIT`, except the one-bit test):

| Object | one bit | any of | all of | set | clear |
|---|---|---|---|---|---|
| `vma_flags_t *` | `vma_flags_test()` | `vma_flags_test_any()` | `vma_flags_test_all()` | `vma_flags_set()` | `vma_flags_clear()` |
| `struct vm_area_struct *` | `vma_test()` | `vma_test_any()` | `vma_test_all()` | `vma_set_flags()` | `vma_clear_flags()` |
| `struct vm_area_desc *` | `vma_desc_test()` | `vma_desc_test_any()` | `vma_desc_test_all()` | `vma_desc_set_flags()` | `vma_desc_clear_flags()` |

- There is no vma_test_flags(), vma_test_all_flags() or vma_desc_test_flags().
- `_mask` suffix: every any/all/set/clear name above has a function with
  `_mask` appended that takes a `vma_flags_t` by value, for example
  `vma_set_flags_mask(vma, VMA_REMAP_FLAGS)`.
- Converters: `legacy_to_vma_flags()` and `vma_flags_to_legacy()` in
  `include/linux/mm_types.h`; the second returns word 0 only.
- Composite masks: some exist in both spellings, and the legacy one may be
  derived, as `VM_SPECIAL` is `vma_flags_to_legacy(VMA_SPECIAL_FLAGS)`; others
  have only the bitmap spelling, for example `VMA_REMAP_FLAGS`.
- Atomic single-bit access: `vma_set_atomic_flag()` and
  `vma_test_atomic_flag()`.
- Flag configured out: the legacy mask is `VM_NONE`, for example
  `VM_DROPPABLE`; some flags also have a bitmap mask macro that becomes
  `EMPTY_VMA_FLAGS`, for example `VMA_DROPPABLE`, tested with
  `vma_test_single_mask()`.
- **Potentially unsafe usage**: passing a `vma_flag_t` bit number of 32 or
  more to `mk_vma_flags()`.
  - Unsafe: in code that is also built for 32-bit; `NUM_VMA_FLAG_BITS` is
    `BITS_PER_LONG`, `vma_flags_set_flag()` does no range check, and for
    example `VMA_SEALED_BIT` is declared in every configuration.
  - Safe: in code built only for 64-bit, as `__mseal_range()` in
    `mm/mseal.c`; `mm/Makefile` builds it only under `CONFIG_64BIT`.
  - Safe: through the mask macro that is `EMPTY_VMA_FLAGS` when the flag is
    unavailable, as `VMA_UFFD_MINOR` in `include/linux/mm.h`;
    `CONFIG_HAVE_ARCH_USERFAULTFD_MINOR` is selected only on 64-bit.
