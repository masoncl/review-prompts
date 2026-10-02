- `___slab_alloc()` here has one retry label, `new_objects`, and no CPU
  slab; there is no retry_load_slab or redo label and no
  defer_deactivate_slab() in `mm/slub.c`.
- Of the cache's own locks, `___slab_alloc()` tries only `n->list_lock`, in
  `get_from_partial_node()`, `alloc_from_new_slab()` and
  `alloc_single_from_new_slab()`; there is no get_partial_node() here.
- Per-CPU sheaf lock: tried by `alloc_from_pcs()` with `local_trylock()`
  before `___slab_alloc()` is called; nothing checks
  `local_lock_is_locked()` first.
- `local_trylock()` without `CONFIG_PREEMPT_RT`: fails only when this CPU
  already holds the lock, so the failure lasts for the whole call.
- `local_trylock()` with `CONFIG_PREEMPT_RT`: always fails in NMI and
  hardirq.
- Failed `n->list_lock` trylock on a fresh slab: `free_new_slab_nolock()`
  frees the slab pages directly through `free_frozen_pages_nolock()`; the
  slab is not queued for `irq_work`.
- `get_from_any_partial()`: without `allow_spin` it does not call
  `read_mems_allowed_begin()`, and its `do`/`while` loop runs once.
- **Potentially unsafe usage**: jumping back to allocate another slab after
  `alloc_from_new_slab()` or `alloc_single_from_new_slab()` returned too
  little.
  - Unsafe: when `allow_spin` is false; the `n->list_lock` trylock can fail
    on every pass, and each pass allocates and discards a slab.
  - Safe: behind `if (allow_spin)`, as the second `goto new_objects` in
    `___slab_alloc()`.
  - Safe: when the call passes `allow_spin` true, as the `goto new_slab` in
    `refill_objects()`; `alloc_from_new_slab()` then spins on `n->list_lock`
    and never discards the slab.
