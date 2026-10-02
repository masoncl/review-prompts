- `struct slabobj_ext`: holds one union of `_objcg` and `_ctref`, not two
  members. An object's extension is one or two consecutive elements, objcg
  first; `slab_obj_ext_size()` gives the size.
- Access: `slab_obj_ext()` in `mm/slab.h` for the element, then
  `slab_obj_ext_objcg()`, `slab_obj_ext_set_objcg()` or
  `slab_obj_ext_codetag_ref()`, all inside `get_slab_obj_exts()` and
  `put_slab_obj_exts()`. Indexing the vector by object index is wrong: the
  stride is `slab_obj_ext_size()` or `s->size`.
- `slab->obj_exts_needs_objcg` (64-bit): fixes the layout per slab; set in
  `allocate_slab()` from `SLAB_MAY_ACCOUNT`.

| Place | Set up by | Condition |
|---|---|---|
| separate kmalloc memory | `alloc_slab_obj_exts()` | no in-slab vector |
| slab space after the last object | `alloc_slab_obj_exts_early()` | `obj_exts_fit_within_slab_leftover()` |
| padding of each object | `alloc_slab_obj_exts_early()` | cache has `SLAB_OBJ_EXT_IN_OBJ`, 64-bit only |

- In-object placement: marked per slab by `obj_exts_in_object`, not by the
  cache flag; test with `obj_exts_in_object()` in `mm/slab.h`.
- `alloc_slab_obj_exts_early()`: does nothing unless `need_slab_obj_exts()`
  is true when the slab is created.
- Low bits: only bit 0 is used. With a pointer it is `MEMCG_DATA_OBJEXTS`;
  alone it is `OBJEXTS_ALLOC_FAIL`. There is no OBJEXTS_NOSPIN_ALLOC;
  `free_slab_obj_exts()` picks `kfree()` or `kfree_nolock()` from its
  `allow_spin` argument.
- Without `CONFIG_MEMCG`: a valid vector pointer has no flag bit set.
- `OBJEXTS_ALLOC_FAIL`: written only under
  `CONFIG_MEM_ALLOC_PROFILING_DEBUG`. It does not stop retries:
  `slab_obj_exts()` returns 0 for it, and the next allocation tries again.
- `free_slab_obj_exts()`: sets `slab->obj_exts = 0` in every case; it does
  not free a vector for which `obj_exts_in_slab()` is true.
- Bad-page check on a non-zero field: `page_expected_state()` in
  `mm/page_alloc.c` tests `page->memcg_data`, only under `CONFIG_MEMCG`.
