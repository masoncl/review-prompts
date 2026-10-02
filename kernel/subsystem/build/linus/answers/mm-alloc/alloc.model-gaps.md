- Models take __GFP_NO_OBJ_EXT to stop recursion inside slab. There is no
  such gfp bit here; for a sheaf of a kmalloc cache `__alloc_empty_sheaf()` in
  `mm/slub.c` passes the slab alloc flag `SLAB_ALLOC_NO_RECURSE` (`mm/slab.h`)
  through `kmalloc_flags()`.
- Models take every allocation call to carry an explicit GFP argument.
  `kmalloc_obj()`, `kzalloc_obj()`, `kvmalloc_obj()`, `kvzalloc_obj()` and
  their array and flex forms in `include/linux/slab.h` use `default_gfp()`
  (`include/linux/gfp.h`), which gives `GFP_KERNEL` when the argument is left
  out.
- Models take the zonelist walk to use the first zone that passes its
  watermark. With more than one online node, `get_page_from_freelist()` first
  skips nodes whose kswapd is not asleep on `kswapd_wait`, and retries
  without the skip only if that pass found nothing.
