- `folio->flags` and `page->flags`: type `memdesc_flags_t`, a struct with the
  single member `unsigned long f`, in `include/linux/mm_types.h`; code writes
  `folio->flags.f`.
- Fields above the flags, from the top: section, node, zone, last cpupid,
  KASAN tag, MGLRU generation, MGLRU refs; see `LRU_GEN_PGOFF` and
  `LRU_REFS_PGOFF` in `include/linux/mmzone.h`.
- Bits left unused between the flags and the MGLRU refs: hold an allocation
  tag index when `mem_profiling_compressed` is on; see `alloc_tag_sec_init()`
  in `mm/alloc_tag.c`.
- `PF_NO_TAIL` and `PF_NO_COMPOUND`: assert only in modifying accessors
  (`enforce` is 1), never in tests.
- Without `CONFIG_DEBUG_VM_PGFLAGS`: `VM_BUG_ON_PGFLAGS()` compiles to nothing,
  so a write through a tail lands on the head with `PF_NO_TAIL` and on the
  page given with `PF_NO_COMPOUND`.
- Flags declared only with `FOLIO_FLAG()` and its single-operation forms: have
  no page accessor, so nothing redirects a tail for them. For example there is
  no PageActive(), PageReferenced(), PageSwapBacked(), PageUnevictable(),
  PageMlocked() or PageSwapCache() in this tree.
