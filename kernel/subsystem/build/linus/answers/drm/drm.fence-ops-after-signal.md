- `wait` on a signalled fence: still called; `dma_fence_wait_timeout()` makes
  no signalled test before `ops->wait`, and calls it after
  `rcu_read_unlock()`.
- Every other callback except `release`, on a fence whose ops stay attached:
  the core tests the signalled bit first and does not call it; see
  `dma_fence_driver_name()`, `__dma_fence_enable_signaling()`,
  `dma_fence_is_signaled()` and `dma_fence_set_deadline()`.
- Exception: `trace_dma_fence_signaled()` in
  `dma_fence_signal_timestamp_locked()`, when that tracepoint is enabled,
  calls `get_driver_name` and `get_timeline_name` right after the signalled
  bit is set, still inside the signalling call.
- There are no fence_value_str or timeline_value_str members in
  `struct dma_fence_ops` here.
- Ops without `release`: `dma_fence_release()` calls `dma_fence_free()`, which
  is `kfree_rcu()` on the `struct dma_fence` pointer, so that pointer must be
  the start of the allocation, as in `drm_crtc_create_fence()`.
