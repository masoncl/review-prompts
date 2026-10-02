- `count_objects` returning 0: `do_shrink_slab()` returns before it reads or
  writes `nr_deferred`, so no work is deferred for that call. Nothing in
  `mm/shrinker.c` stops `count_objects` from testing `sc->gfp_mask`.
- `scan_objects` returning `SHRINK_STOP`: that batch adds nothing to `freed`
  and its `sc->nr_scanned` is not read; `freed` from earlier batches is still
  returned.
- Deferred count after the loop: `nr + delta - scanned`, capped at
  `2 * freeable`. It is not the leftover `total_scan`.
- **Potentially unsafe usage**: `scan_objects` writing a smaller value to
  `sc->nr_scanned`.
  - Unsafe: leaving `sc->nr_scanned` at 0 and returning anything but
    `SHRINK_STOP`; the loop in `do_shrink_slab()` subtracts `nr_scanned` from
    `total_scan` and never ends.
  - Safe: return `SHRINK_STOP` when `sc->nr_scanned` is 0, as
    `i915_gem_shrinker_scan()` and `drm_pagemap_shrinker_scan()` do.
- **Unsafe usage**: a `SHRINKER_MEMCG_AWARE` `count_objects` returning
  `SHRINK_EMPTY` while the list for `sc->memcg` and `sc->nid` holds objects.
  `shrink_slab_memcg()` clears the bit, and `__list_lru_add()` sets it again
  only when a list goes from empty to non-empty.
  - Safe: return 0 when objects exist but must be skipped, as
    `zswap_shrinker_count()` does.
  - Safe: return `SHRINK_EMPTY` only when `list_lru_shrink_count()` is 0, as
    `deferred_split_count()` does.
- `shrinker_alloc()`: sets `seeks` to `DEFAULT_SEEKS`.
- Walkers: find the shrinker under `rcu_read_lock()`, then hold a
  `shrinker_try_get()` reference across `do_shrink_slab()` with RCU dropped;
  nothing in `mm/shrinker.c` uses SRCU.
- `shrink_slab()`: retakes `rcu_read_lock()` before `shrinker_put()`, because
  the walk continues from this shrinker's `list` node.
- `shrink_slab_memcg()`: calls `shrinker_put()` with no RCU lock held; it finds
  the next shrinker by id with `idr_find()`.
- `shrinker_free()` order, for a shrinker with `SHRINKER_REGISTERED`:
  `shrinker_put()`, `wait_for_completion()`, and only then `list_del_rcu()`
  and, with `SHRINKER_MEMCG_AWARE`, `idr_remove()` under `shrinker_mutex`.
  Without `SHRINKER_REGISTERED` there is no put and no wait.
- After the last reference is dropped, until `shrinker_free()` unlinks it: the
  shrinker is still on `shrinker_list` and in `shrinker_idr` with refcount 0.
  `shrinker_try_get()` fails, and `shrink_slab_memcg()` then clears the memcg
  bit.
- `shrinker_free()` called from that shrinker's own callback: never returns,
  because the walker drops its reference only after the callback returns.
- **Potentially unsafe usage**: calling `shrinker_free()` on a registered
  shrinker while holding a lock its callbacks take.
  - Unsafe: when a callback blocks on that lock; `shrinker_free()` sleeps in
    `wait_for_completion()` until the walker's `shrinker_put()`.
  - Safe: when the callback only trylocks and returns `SHRINK_STOP`, as
    `super_cache_scan()` does with `super_trylock_shared()`;
    `deactivate_locked_super()` calls `shrinker_free()` with `s_umount` held
    exclusively.
- **Potentially unsafe usage**: `shrinker_register()` before the object behind
  `private_data` is fully set up.
  - Unsafe: when a callback reads state that is not initialised yet.
  - Safe: when each callback first tests a readiness flag; `sget_fc()`
    registers a superblock that is not filled in, `super_cache_count()` returns
    0 until `SB_BORN`, and `super_cache_scan()` goes through
    `super_trylock_shared()`.
- `alloc_super()`: allocates and fills the shrinker but does not call
  `shrinker_register()`; `sget_fc()` in `fs/super.c` does.
- `CONFIG_SHRINKER_DEBUG`: `shrinker_debugfs_count_show()` and
  `shrinker_debugfs_scan_write()` in `mm/shrinker_debug.c` call the callbacks
  with no `shrinker_try_get()`.
- `shrinker_free()`: for a shrinker that has a debugfs entry, calls
  `shrinker_debugfs_remove()` after the wait and before `call_rcu()`.
