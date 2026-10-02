- **Potentially unsafe usage**: taking a lock inside the object under
  `rcu_read_lock()` without first holding a reference.
  - Unsafe: when the lock is initialised on allocation; a stale reader may
    hold or spin on it while it is re-initialised.
  - Safe: when the cache's ctor initialises the lock and nothing
    re-initialises it, and the reader rechecks identity after locking.
    `lock_task_sighand()` in `kernel/signal.c` relies on `sighand_ctor()` in
    `kernel/fork.c` and rechecks `tsk->sighand`.
- **Potentially unsafe usage**: `kmem_cache_zalloc()`, `__GFP_ZERO` or a
  whole-object `memset()` on allocation.
  - Unsafe: when a stale reader operates on a field that the zeroing changes:
    a lock, the `next` pointer of its chain, or a count in which zero is not
    the free value (`FILE_REF_ONEREF` is 0).
  - Safe: when readers only load fields and then revalidate against something
    outside the object. `journal_alloc_journal_head()` in `fs/jbd2/journal.c`
    zeroes; its reader `jbd2_write_access_granted()` rechecks `jh->b_bh`.
  - Safe: zeroing around the field readers follow. `sk_prot_alloc()` in
    `net/core/sock.c` strips `__GFP_ZERO` and calls `sk_prot_clear_nulls()`.
  - Safe: zeroing a count that is already zero on a free object and that
    readers take only with an inc-not-zero form. `vma_init()` in
    `include/linux/mm.h` does `memset()` on the whole object;
    `vma_start_read()` in `mm/mmap_lock.c` takes `vm_refcnt` with
    `__refcount_inc_not_zero_limited_acquire()`.
- `slab_want_init_on_alloc()` and `slab_want_init_on_free()` in `mm/slab.h`:
  `init_on_alloc` and `init_on_free` do not zero objects of these caches or of
  ctor caches; an explicit `__GFP_ZERO` still zeroes an object of a type-safe
  cache that has no ctor.
- Cache with a ctor: `new_slab()` in `mm/slub.c` has
  `WARN_ON_ONCE(s->ctor && (flags & __GFP_ZERO))`; it fires only when a new
  slab page is allocated.
- `refcount_inc_not_zero()`: a relaxed cmpxchg, no ordering against the key
  recheck that follows.
- `refcount_inc_not_zero_acquire()` and `refcount_set_release()` in
  `include/linux/refcount.h`: the pair meant for these caches.
  `vma_mark_attached()` in `include/linux/mmap_lock.h` uses the release form;
  `vma_start_read()` in `mm/mmap_lock.c` uses
  `__refcount_inc_not_zero_limited_acquire()`.
- After the count is set non-zero the object is visible to stale readers even
  before it is linked anywhere, so every field a reader rechecks must be
  written before that store.
- `freeptr_offset` in `struct kmem_cache_args`: the free pointer must not
  overlay a field that guards against recycling (count, key, ctor-set lock).
  `create_cache()` in `mm/slab_common.c` checks only range, alignment and that
  the cache is type-safe or has a ctor.
- `CONFIG_SLUB_RCU_DEBUG`: `slab_free_hook()` in `mm/slub.c` defers the free
  of each object of such a cache through `call_rcu()`, unless its
  `GFP_NOWAIT` allocation fails, so a missing recheck is hidden on such a
  build.
