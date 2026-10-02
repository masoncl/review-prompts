- Shrink in place: zeroes `[p + size, p + old_size)` when
  `want_init_on_free() || want_init_on_alloc(flags)`; either one is enough.
- Grow in place: zeroes nothing, whatever `flags` holds, `__GFP_ZERO`
  included.
- Grown bytes are zero only if the first allocation and every earlier shrink
  of that area ran with zeroing in effect.
- In-place grow bound: `size <= vm->nr_pages << PAGE_SHIFT`, not
  `get_vm_area_size()`; `alloced_size` only feeds the mismatch `WARN()`.
- Shrink across a page boundary: unmaps and frees the tail pages and lowers
  `vm->nr_pages`, after the `memset()`, when all of these hold:
  - `vm_area_page_order(vm)` is 0
  - `vm->flags` has neither `VM_FLUSH_RESET_PERMS` nor `VM_USERMAP`
  - `gfp_has_io_fs(flags)` is true
  - the new page count is below `vm->nr_pages`
- After such a shrink: a grow past the remaining pages goes to a new
  allocation through `__vmalloc_node_noprof()`; only growing the area is
  still a TODO.
