- `dma_fence_signal_timestamp_locked()`: sets `fence->ops` to NULL only when
  the ops table has neither `release` nor `wait`; otherwise the pointer stays
  for the life of the fence.
- The clearing happens before the callback list is run, so a `dma_fence_cb`
  callback can already see `fence->ops` as NULL.
- `fence->ops` is `__rcu`: read it with `rcu_dereference()` under
  `rcu_read_lock()` and handle NULL; `rcu_access_pointer()` only to compare.
- **Potentially unsafe usage**: dereferencing `fence->ops`, or testing a
  fence's type by comparing `fence->ops` with an ops table, without a NULL
  check.
  - Unsafe: when the ops table sets neither `release` nor `wait` and the fence
    may have signalled; the pointer is NULL, so the dereference faults and the
    comparison is false for a fence of that type.
  - Safe: when the ops table sets `release` or `wait`, as
    `dma_fence_is_array()` relies on for `dma_fence_array_ops`; the test in
    `dma_fence_signal_timestamp_locked()` defines this.
  - Safe: under the fence lock before the pointer is cleared, as the
    `trace_dma_fence_signaled()` call in
    `dma_fence_signal_timestamp_locked()`; its event class `dma_fence_ops` in
    `include/trace/events/dma_fence.h` dereferences `fence->ops` directly.
- `dma_fence_driver_name()` and `dma_fence_timeline_name()`: do not take
  `rcu_read_lock()`; the caller must hold it across the call and every use of
  the string.
- Return type of both is `const char __rcu *`; pass it through
  `rcu_dereference()` to use it, as `sync_file_get_name()` in
  `drivers/dma-buf/sync_file.c` does.
- Missing `rcu_read_lock()` around the name helpers: caught only by
  `rcu_dereference()`, under `CONFIG_PROVE_RCU`.
- Placeholder strings are `"detached-driver"` and `"signaled-timeline"`; both
  helpers return them whenever the signalled bit is set, also for a fence
  whose ops stay attached.
- Module reference: the core takes none for fence ops; nothing stops an
  unload while fences exist.
- Ops with `release` or `wait`: the module must stay loaded until every such
  fence has been freed, not only signalled.
- External lock: see "Fence structure and lock"; a lock in driver memory keeps
  the driver tied to the fence until the fence is freed.
