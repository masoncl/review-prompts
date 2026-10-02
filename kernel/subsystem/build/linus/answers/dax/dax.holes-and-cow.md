- `dax_load_hole()`: takes the pfn from `zero_pfn()` and maps it with
  `vmf_insert_page_mkwrite(vmf, pfn_to_page(pfn), false)`; there is no
  my_zero_pfn() here.
- `dax_pmd_load_hole()`: maps the huge zero folio with
  `vmf_insert_folio_pmd(vmf, zero_folio, false)`; it does not call
  `set_pmd_at()` itself.
- Hole read path: taken for `IOMAP_UNWRITTEN` as well as `IOMAP_HOLE`, when
  `IOMAP_WRITE` is clear and a PTE fault has no `vmf->cow_page`.
- `dax_fault_cow_page()`: returns `VM_FAULT_DONE_COW` when `finish_fault()`
  returns 0, otherwise what `finish_fault()` returned.
- Entry after the `cow_page` path: the entry `grab_mapping_entry()` locked,
  unlocked again; an existing entry is unchanged, a new one is `DAX_EMPTY`
  and stays in the xarray. No mark is set.
- `grab_mapping_entry()` at order 0: removes a zero or empty PMD entry before
  it makes the PTE-sized entry; this holds for every PTE fault, the
  `cow_page` path included.
- `IOMAP_F_SHARED` in `dax_insert_entry()`: always calls
  `unmap_mapping_pages()` and always replaces the entry, even over a normal
  pfn entry.
- `PAGECACHE_TAG_TOWRITE` in `dax_insert_entry()`: set when `IOMAP_WRITE` and
  `IOMAP_F_SHARED` are both set, synchronous faults included.
- Order in `dax_fault_iter()`: `dax_insert_entry()` runs before
  `dax_iomap_copy_around()`, so the entry and its marks remain when the copy
  fails.
- `dax_iomap_copy_around()` from the fault path: gets `size` as both length
  and alignment, so it copies or zeroes the whole page or PMD, not head and
  tail.
- Zero test in `dax_iomap_copy_around()`: `IOMAP_F_SHARED` set on the map from
  `iomap_iter_srcmap()`, or type `IOMAP_UNWRITTEN`; it does not test
  `IOMAP_HOLE`.
- `iomap_iter_srcmap()` in `include/linux/iomap.h`: returns `iter->iomap` when
  the filesystem filled no `srcmap`, which is how a hole source shows up as
  `IOMAP_F_SHARED`.
- **Unsafe usage**: a filesystem setting `IOMAP_F_SHARED` on the `srcmap` it
  fills for a DAX write.
  - Unsafe: `dax_iomap_copy_around()` tests `srcmap->flags` and zeroes the
    destination instead of copying the old data.
  - Safe: flag only `iomap`, and fill `srcmap` without `IOMAP_F_SHARED`, as
    `xfs_direct_write_iomap_begin()` does in `fs/xfs/xfs_iomap.c`.
