- Default `s->offset`: `ALIGN_DOWN(s->object_size / 2, sizeof(void *))`, not
  0; see `calculate_sizes()`.
- `SLAB_RED_ZONE`: moves the pointer after the object only when
  `s->object_size < sizeof(void *)` or `slub_debug_orig_size()` is true.
- `freeptr_offset`: allowed for a cache with `SLAB_TYPESAFE_BY_RCU` or with a
  constructor; `create_cache()` in `mm/slab_common.c` rejects it otherwise.
- There is no get_freepointer_safe() and no freelist_corrupted() in this
  tree.
- `mm/Makefile`: sets `KASAN_SANITIZE_slub.o := n`, so compiler-inserted
  KASAN checks do not cover accesses made in `mm/slub.c`.
- `kasan_reset_tag()`: still needed in slab code wherever an object address
  feeds arithmetic or a comparison, for example the hardened hash,
  `__obj_to_index()` and `check_valid_pointer()`.
- Pointers held in a freelist or a sheaf: still carry an old tag, for a
  freed object that of the previous allocation; `kasan_slab_alloc()` assigns
  the tag in `slab_post_alloc_hook()`, a new one unless the cache has a
  constructor or `SLAB_TYPESAFE_BY_RCU`.
- `metadata_access_enable()` and `metadata_access_disable()` in
  `mm/slab.h`: `check_bytes_and_report()` wraps `memchr_inv()`, a helper
  outside `mm/slub.c`, in them, on top of `kasan_reset_tag()`. Under
  `CONFIG_KASAN_HW_TAGS` `kasan_disable_current()` is an empty inline, so
  there only `kasan_reset_tag()` counts.
- **Potentially unsafe usage**: reading or writing `object + s->offset`
  without `get_freepointer()` or `set_freepointer()`.
  - Unsafe: while the object is linked on a slab freelist or a detached
    freelist; under `CONFIG_SLAB_FREELIST_HARDENED` the next
    `get_freepointer()` decodes the raw value to a wrong address.
  - Safe: zeroing the slot of an object that is leaving the free state, as
    `maybe_wipe_obj_freeptr()` does.
  - Safe: using the slot as a list node while the object is on no freelist,
    as `defer_free()` does; `deferred_percpu_work_fn()` rewrites it with
    `set_freepointer()` before `__slab_free()`.
- **Unsafe usage**: `set_freepointer()` with `fp` equal to `object`; it is a
  `BUG_ON()` under `CONFIG_SLAB_FREELIST_HARDENED`.
  - Safe: link an object only to a different object or NULL, as
    `build_slab_freelist()` does.
- **Unsafe usage**: `memset()` or a read of a free object through the pointer
  as stored, under `CONFIG_KASAN_HW_TAGS`; the hardware checks the stale
  pointer tag against memory that `kasan_slab_free()` has poisoned.
  - Safe: apply `kasan_reset_tag()` first, as `get_freepointer()` and
    `init_object()` do.
