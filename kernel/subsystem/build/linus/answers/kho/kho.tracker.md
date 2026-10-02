- Names: there is no kho_radix_encode_key(), kho_radix_add_page(),
  kho_radix_del_page(), KHO_ORDER_0_LOG2 or struct kho_mem_track in this tree.
- Key: built by `kho_encode_radix_key()` and decoded by
  `kho_decode_radix_key()`, both static in
  `kernel/liveupdate/kexec_handover.c`.
- Order bit: `1UL << (64 - (PAGE_SHIFT + order))`, OR-ed with
  `phys >> (PAGE_SHIFT + order)`.
- Lock: `struct kho_radix_tree` holds a `struct mutex lock`, not an
  rw_semaphore.
- `kho_radix_add_key()`, `kho_radix_del_key()` and `kho_radix_walk_tree()`:
  each takes `tree->lock`; add and del call `might_sleep()` before taking it.
- `kho_radix_walk_tree()`: holds the mutex across every callback, so a
  callback cannot add or delete in the tree being walked;
  `kho_extend_scratch()` adds to a second tree with its own lockdep class.
- `kho_radix_add_key()` errors: `-EINVAL` with `WARN_ON_ONCE()` when
  `tree->root` is NULL, `-ERANGE` for a key wider than `KHO_RADIX_KEY_WIDTH`,
  `-ENOMEM`.
- `kho_radix_del_key()`: returns void.
- `kho_radix_alloc_node()`: `get_zeroed_page(GFP_KERNEL)` once
  `slab_is_available()`, `memblock_alloc()` before that.
