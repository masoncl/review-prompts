- `struct drm_gem_lru`: has only `count` and `list`; there is no lock field.
- The lock: `gem_lru_mutex` in `struct drm_device`, one mutex for every LRU of
  the device. It protects `obj->lru` and `obj->lru_node` too.
- `drm_gem_lru_init()`: takes only the LRU. `drm_gem_lru_scan()`: takes the
  device as its first argument.
- `drm_gem_lru_scan()`: takes `resv` with
  `ww_mutex_trylock(&obj->resv->lock, ticket)` whether or not a ticket is
  given; it never blocks on `resv`.
- `ticket`: every in-tree caller passes NULL. The callbacks take other
  reservations with `dma_resv_trylock()` only, for example `with_vm_locks()`
  in `drivers/gpu/drm/msm/msm_gem_shrinker.c`.
- The callback may sleep: `panthor_gem_try_evict()` waits in
  `dma_resv_wait_timeout()`.
- **Unsafe usage**: calling `drm_gem_lru_move_tail_locked()` from the `shrink`
  callback without taking `gem_lru_mutex`; its
  `lockdep_assert_held_once()` fails, because `drm_gem_lru_scan()` dropped
  the mutex.
  - Safe: `drm_gem_lru_move_tail()` or `drm_gem_lru_remove()`, as
    `panthor_gem_update_reclaim_state_locked()` does.
  - Safe: take `dev->gem_lru_mutex`, then call the `_locked` form, as
    `update_lru()` in `drivers/gpu/drm/msm/msm_gem.c` does.
