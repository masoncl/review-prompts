- `softleaf_to_pfn()`: always returns `swp_offset(entry) & SWP_PFN_MASK`, on
  every architecture; there is no swp_offset_pfn() here.
- `SWP_PFN_BITS`: `MAX_PHYSMEM_BITS - PAGE_SHIFT` when `MAX_PHYSMEM_BITS` is
  defined; the `min_t()` against `SWP_TYPE_SHIFT` applies only when it is not.
- Migration entry offset: PFN plus `SWP_MIG_YOUNG` and `SWP_MIG_DIRTY`
  directly above it; no other PFN-carrying kind uses bits above the PFN.
- Device-private entry offset: an ordinary `page_to_pfn()` value.
- Marker offset: read with `softleaf_to_marker()`, which masks with
  `PTE_MARKER_MASK`.
- **Unsafe usage**: taking `swp_offset()` of a migration entry as the PFN.
  - Safe: `softleaf_to_pfn()`, as `check_pte()` does; `SWP_PFN_MASK` in
    `include/linux/swapops.h` defines which bits are PFN.
  - Safe: passing the whole `swp_offset(entry)` to
    `make_readable_migration_entry()` when rewriting an entry, as
    `copy_nonpresent_pte()` does; that keeps the A/D bits on purpose.
