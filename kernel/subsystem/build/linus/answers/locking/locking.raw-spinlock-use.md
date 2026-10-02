- Section length: `Documentation/locking/locktypes.rst` has no sentence asking
  that `raw_spinlock_t` sections be short or bounded; its only wording is that
  the type "can sometimes also be used when the critical section is tiny, thus
  avoiding RT-mutex overhead", which permits a use and limits nothing.
- `Documentation/core-api/real-time/differences.rst`: says nothing about raw
  section length either; under "Locking" it only names where raw locks are used
  (interrupt handling, scheduler, timers).
- Freeing memory: `locktypes.rst` ("raw_spinlock_t on RT") names only
  allocation; the ban on `kfree()` and `free_pages()` in non-preemptible
  sections is in `differences.rst`, "Memory allocation".
- **Potentially unsafe usage**: allocating or freeing memory while holding a
  `raw_spinlock_t`.
  - Unsafe: through `kmalloc()`, `kfree()` or the page allocator with any gfp
    mask, `GFP_ATOMIC` included, because the allocator takes `spinlock_t`; the
    failing example in `locktypes.rst` uses `GFP_ATOMIC`.
  - Safe: `kmalloc_nolock()` (`include/linux/slab.h`, implemented by
    `__kmalloc_nolock_noprof()` in `mm/slub.c`) and `kfree_nolock()` in
    `mm/slub.c`, which only trylock; `kmalloc_nolock()` can return NULL (always
    for sizes above `KMALLOC_MAX_CACHE_SIZE`, and on RT in hardirq or NMI via
    `can_spin_trylock()`), and the limits of `kfree_nolock()` are in the
    comment above it. On PREEMPT_RT not with `pi_lock` of
    `struct task_struct` held; see "Local trylocks".
