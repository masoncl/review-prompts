- `struct ttm_operation_ctx` in `include/drm/ttm/ttm_bo.h`: six fields; it
  has no `force_alloc` member.
- `no_wait_gpu` during allocation does not produce `-EBUSY`: busy eviction
  victims are skipped, the LRU walk only trylocks, and a place whose manager
  has an unsignalled eviction fence is passed over for the next place. When
  nothing fits the result is `-ENOMEM`. See
  `ttm_bo_add_pipelined_eviction_fences()` and `__ttm_bo_lru_cursor_next()`.
- `-EBUSY` reaches the caller from `ttm_bo_wait_ctx()`, typically inside the
  driver's `move` callback. Without `no_wait_gpu` it still returns `-EBUSY`
  after a 15 second wait.
- `-EDEADLK` is not returned by TTM's eviction locking:
  `ttm_lru_walk_ticketlock()` turns it into `-ENOSPC`, which ends as
  `-ENOMEM`.
- `-EINTR` can come back with `interruptible` set:
  `ttm_lru_walk_ticketlock()` returns the result of
  `dma_resv_lock_interruptible()` unconverted, unlike `ttm_bo_reserve()`.
  `ttm_bo_evict()` skips its "Buffer eviction failed" message for both
  `-EINTR` and `-ERESTARTSYS`.
- `-ERESTARTSYS` is the restart code, from interruptible fence waits; pass
  it up unchanged.
- `-EAGAIN` from the dmem cgroup charge in `ttm_resource_try_charge()`:
  `ttm_bo_alloc_at_place()` converts it to `-EBUSY` or `-ENOSPC` before it
  can leave.
- `-ENOSPC` at the end of `ttm_bo_validate()` becomes `-ENOMEM` unless
  `bdev->alloc_flags` has `TTM_ALLOCATION_PROPAGATE_ENOSPC`; no driver in this
  tree sets that flag. `ttm_bo_bounce_temp_buffer()` failures are returned
  unconverted.
- Placement naming only absent or unused managers: those places are skipped
  in `ttm_bo_alloc_resource()`, giving `-ENOMEM`, not `-EINVAL`.
- `-EINVAL` from `ttm_bo_validate()` itself means a pinned BO would have to
  move.
- Pinned BO and `TTM_PL_FLAG_FALLBACK`: the compatibility test before the pin
  test runs with `evicting == false`, which ignores fallback places. A pinned
  BO sitting in a place the placement lists only as fallback gets `-EINVAL`.
- Pinned BOs are moved to the `bdev->unevictable` list by
  `ttm_resource_move_to_lru_tail()`, not unlinked;
  `ttm_device_clear_dma_mappings()` still walks them.
- Pinning also makes `ttm_bo_shrink_suitable()` return false.
