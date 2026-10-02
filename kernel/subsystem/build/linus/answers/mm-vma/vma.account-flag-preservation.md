- `mprotect_fixup()` clearing `VMA_ACCOUNT_BIT`: only when the new flags lack
  `VMA_WRITE_BIT`, the old flags have `VMA_ACCOUNT_BIT`, `vma_is_anonymous()`
  is true and `vma->anon_vma` is NULL.
- `mprotect_fixup()` uncharge on clear: `vm_unacct_memory(nrpages)` runs after
  `vma_flags_reset_once()` and `change_protection()`, so no failure can follow
  it.
- **Potentially unsafe usage**: clearing `VMA_ACCOUNT_BIT` and uncharging when
  a private mapping loses write permission.
  - Unsafe: when `vma_is_anonymous()` is false or `vma->anon_vma` is set; a
    VMA with an `anon_vma` may hold private pages that stay allocated after
    the charge is returned.
  - Safe: when `vma_is_anonymous()` is true and `vma->anon_vma` is NULL, as
    `mprotect_fixup()` tests; otherwise it leaves the flag and the charge.
- `unmap_source_vma()` in `mm/mremap.c`, for an accounted VMA moved without
  `MREMAP_DONTUNMAP`: clears `VMA_ACCOUNT_BIT` on the whole source VMA, not
  only the moved range, then sets it again on each remnant.
- `unmap_source_vma()` when `do_vmi_munmap()` fails: returns without setting
  `VMA_ACCOUNT_BIT` again; not a pattern to copy.
- Helpers used: `unmap_source_vma()` calls `vma_clear_flags()` and
  `vma_set_flags()`, and `mprotect_fixup()` calls `vma_flags_reset_once()`;
  none of the three takes or asserts the VMA write lock.
- `vm_flags_set()` and `vm_flags_clear()`: do call `vma_start_write()`, but no
  in-tree change of `VMA_ACCOUNT_BIT` uses them.
- **Unsafe usage**: changing `VMA_ACCOUNT_BIT` on an attached VMA with
  `vma_set_flags()`, `vma_clear_flags()` or `vma_flags_reset_once()` while the
  VMA is not write-locked.
  - Unsafe: these helpers update `vma->flags` non-atomically;
    `vma_set_atomic_flag()` sets `VMA_MAYBE_GUARD_BIT` in the same bitmap
    under a VMA read lock only, and that bit can be lost.
  - Safe: after `vma_start_write()` on that VMA; `move_vma()` calls it on the
    source before `unmap_source_vma()` clears the bit.
  - Safe: `unmap_source_vma()` calls `vma_start_write()` on each remnant
    before `vma_set_flags()`.
  - Safe: `mprotect_fixup()` calls `vma_start_write()` on the VMA that
    `vma_modify_flags()` returned, then `vma_flags_reset_once()`.
