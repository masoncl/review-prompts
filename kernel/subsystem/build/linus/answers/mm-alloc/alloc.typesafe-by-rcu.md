- There is no __sk_nulls_lookup() in this tree; `__inet_lookup_established()`
  in `net/ipv4/inet_hashtables.c` is a lookup of this form.
- Ordering: the identity check must come after the reference is taken. The
  comment at the flag names `refcount_inc_not_zero_acquire()`,
  `refcount_add_not_zero_acquire()` and `refcount_set_release()` in
  `include/linux/refcount.h` as the helpers with the needed fences.
- Writer side: initialise the whole object before the refcount;
  `refcount_set_release()` gives the store ordering, as
  `vma_mark_attached()` in `include/linux/mmap_lock.h` uses.
- `freeptr_offset` in `struct kmem_cache_args`: puts the free pointer inside
  the object, so the field under it can be overwritten while the object is
  free. It must not overlay a field a reader uses to detect reuse;
  `create_cache()` in `mm/slab_common.c` does not check what it overlays.
- **Potentially unsafe usage**: taking a lock inside the object before taking
  a reference.
  - Unsafe: when the lock is initialised after each allocation; the reader
    can take a lock that the new owner is initialising.
  - Safe: when a constructor initialises the lock and no allocation path
    reinitialises it, as with `sighand_ctor()` in `kernel/fork.c` and
    `anon_vma_ctor()` in `mm/rmap.c`; then recheck identity under the lock,
    as `lock_task_sighand()` does.
