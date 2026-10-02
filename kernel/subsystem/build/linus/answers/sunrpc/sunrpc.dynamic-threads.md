- A pool has a range: `sp_nrthrmin` and `sp_nrthrmax` in `struct svc_pool`,
  set by `svc_set_pool_threads(serv, pool, min_threads, max_threads)`.
- `min_threads` nonzero: the count changes only when outside the range, so a
  pool started from zero runs `min_threads` threads.
- `min_threads` zero, or above `max_threads`: the pool runs exactly
  `max_threads` threads.
- `svc_set_num_threads(serv, min_threads, nrservs)`: divides `nrservs` over
  the pools, gives every pool at least one thread when `nrservs` is nonzero,
  and passes `min_threads` to each pool unchanged.
- `svc_recv()` is `int svc_recv(struct svc_rqst *rqstp, long timeo)`.

| Return | All of these hold |
|---|---|
| `-ETIMEDOUT` | the sleep timed out; `svc_thread_should_sleep()` is still true; `sp_nrthrmin` is nonzero; `sp_nrthreads > sp_nrthrmin` |
| `-EBUSY` | a transport was dequeued; `sp_idle_threads` is empty; `timeo` is nonzero; the sleep did not time out; this thread won `test_and_set_bit()` on `SP_TASK_STARTING` |
| 0 | otherwise |

- `svc_recv()` does not read `sp_nrthrmax`; the caller makes that test.
- `SP_TASK_STARTING` is the limiting flag, not `SP_TASK_PENDING`;
  `svc_recv()` sets it and never clears it.
- `nfsd()` in `fs/nfsd/nfssvc.c` is the only caller that acts on the return:
  it takes `nfsd_mutex` with `mutex_trylock()`, tests the count again, then
  calls `svc_new_thread()` or sets `RQ_VICTIM` on itself.
- `lockd()` and `nfs4_callback_svc()` pass `timeo` 0 and ignore the return;
  with `timeo` 0 neither signal is returned.
- **Unsafe usage**: a thread function that receives `-EBUSY` and leaves
  `SP_TASK_STARTING` set; the pool gets no further `-EBUSY`.
  - Safe: clearing it on every `-EBUSY` path, spawned or not, as `nfsd()`
    does.
  - Safe: passing `timeo` 0, as `lockd()` does; the flag is then never set.
