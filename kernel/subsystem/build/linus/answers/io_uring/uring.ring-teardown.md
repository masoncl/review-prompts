- `io_ring_ctx_wait_and_kill()`: under `uring_lock` kills `ctx->refs` and
  unregisters personalities, then queues `ctx->exit_work` on `iou_wq`. It
  frees no other registered resource and flushes no fallback work.
- `io_ring_exit_work()` first step: `io_terminate_zcrx()` under
  `uring_lock`, before the cancel loop.
- `io_req_caches_free()` in the loop: each cached request holds one
  `ctx->refs` reference (taken in `__io_alloc_req_refill()`), so
  `ctx->ref_comp` cannot complete until this call has emptied the cache.
- Timeout: after `IO_URING_EXIT_WAIT_MAX` the loop warns once and the wait
  interval goes from `HZ / 20` to `HZ * 60`.
- tctx-list walk: holds `uring_lock` and `ctx->tctx_lock`; both are dropped
  while waiting for the callback.
- `task_work_add()` failure in the walk: warns and retries with the next
  node; the walk does not remove the failed node.
- `io_tctx_exit_cb()`: skips the removal when `current->io_uring` is NULL or
  `in_cancel` is set, and still completes.
- Before the free: one lock and unlock of `ctx->completion_lock`, then
  `synchronize_rcu()` for `IORING_SETUP_DEFER_TASKRUN` only.
- `io_ring_ctx_free()` first call: `io_unregister_bpf_ops()`, then
  `io_sq_thread_finish()`.
- `io_ring_ctx_free()` steps that rely on an earlier step:

  | Step | Relies on |
  |---|---|
  | `io_unregister_zcrx()` | `io_terminate_zcrx()` in `io_ring_exit_work()` marked every entry; it warns and stops otherwise |
  | `io_rings_free()` and `kfree(ctx)` | `io_sq_thread_finish()` took the ring off `sqd->ctx_list`; `io_sq_thread()` dereferences `ctx->rings` of every ring on that list |
  | `mmdrop(ctx->mm_account)` | `io_sqe_buffers_unregister()` ran; `io_buffer_unmap()` unaccounts against `ctx->mm_account` |
  | `io_rings_free()` | `io_cqring_overflow_kill()` ran; it dereferences `ctx->rings` |
  | `free_uid(ctx->user)` | buffer unregister, `io_destroy_buffers()`, the `param_region` free and `io_rings_free()` ran; all unaccount against `ctx->user` |
  | `percpu_ref_exit(&ctx->refs)` | `ctx->ref_comp` completed |
  | `io_req_caches_free()` | request cache already empty; it runs after `percpu_ref_exit()` |
  | `xa_destroy(&ctx->hpage_acct)` | buffer unregister ran; `io_buffer_unaccount_pages()` uses it |

- `io_rings_free()` after `mmdrop()`: safe because `io_free_region()`
  unaccounts against the `struct user_struct` only.
- `WARN_ON_ONCE(ctx->nr_req_allocated)`: checks that the last
  `io_req_caches_free()` left no request allocated.
