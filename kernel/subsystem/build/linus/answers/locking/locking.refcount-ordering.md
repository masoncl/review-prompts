- A lookup needs more than the control dependency of
  `refcount_inc_not_zero()` when the memory can be reused for another object
  while the reader holds the pointer, as with `SLAB_TYPESAFE_BY_RCU`. The
  identity check after the increment is a load, which the control dependency
  does not order.
- For that case: `refcount_inc_not_zero_acquire()` or
  `refcount_add_not_zero_acquire()` on the reader side, paired with
  `refcount_set_release()` after the new object is fully initialised. All
  three are in `include/linux/refcount.h`.
- After `refcount_set_release()` on memory that can be reused: the object
  counts as visible to other tasks even before it is linked anywhere, because
  a reader may still hold the address from the previous object.
- In-tree pair: `vma_mark_attached()` in `include/linux/mmap_lock.h` uses
  `refcount_set_release()` on `vma->vm_refcnt`; the RCU reader
  `vma_start_read()` in `mm/mmap_lock.c` uses
  `__refcount_inc_not_zero_limited_acquire()`.
