- Capacity `ks`: `__do_krealloc()` does not call `ksize()`. `ks` is
  `s->object_size` for a slab object, `page_size()` for a large kmalloc and
  `kfence_ksize()` for a KFENCE object.
- In-place conditions: `new_size <= ks`, the pointer satisfies `align`, and
  not (`__GFP_THISNODE` with a `nid` that is neither `NUMA_NO_NODE` nor the
  page's node). Otherwise it allocates anew.
- Requested size tracking, for a slab object: only when
  `slub_debug_orig_size()` is true, that is `SLAB_STORE_USER` debugging active
  on a `SLAB_KMALLOC` cache. `CONFIG_KASAN` or `CONFIG_SLUB_DEBUG` alone do not
  store it, and `SLAB_RED_ZONE` is not required.
- Settings consulted on the in-place path: `want_init_on_alloc()` only;
  `want_init_on_free()` is not tested, on a shrink or on a grow.
- Grow with the size not tracked: when `want_init_on_alloc()` is true it
  zeroes `[new_size, ks)` only; the bytes between the old and new size are not
  touched.
