- There is no svc_pool_victim() here; `svc_stop_kthreads()` works on the pool
  that `svc_set_pool_threads()` passes it.

| Flag | Set by | Cleared by |
|---|---|---|
| `SP_VICTIM_REMAINS` | `svc_stop_kthreads()` | `svc_exit_thread()`, on every call |
| `SP_NEED_VICTIM` | `svc_stop_kthreads()` | the thread that wins `svc_thread_should_stop()` |
| `RQ_VICTIM` | `svc_thread_should_stop()`, or `nfsd()` directly when it retires itself | never |

- `svc_exit_thread()` never clears `SP_NEED_VICTIM`.
- **Potentially unsafe usage**: a thread calling `svc_exit_thread()` while
  holding no lock.
  - Unsafe: when it left its loop for a reason other than claiming
    `SP_NEED_VICTIM`; `svc_exit_thread()` then changes `sp_nrthreads`,
    `sv_nrthreads` and `sp_all_threads` unlocked, and its clear of
    `SP_VICTIM_REMAINS` can release a controller waiting for another thread.
  - Safe: when `svc_thread_should_stop()` claimed `SP_NEED_VICTIM`, as in
    `lockd()` and `nfs4_callback_svc()`; the caller of `svc_stop_kthreads()`
    holds the service mutex for the whole wait.
  - Safe: when the thread took the service mutex with `mutex_trylock()` and
    holds it across `svc_exit_thread()`, as `nfsd()` does on `-ETIMEDOUT`.
- **Unsafe usage**: a service thread sleeping in `mutex_lock()` on the
  service mutex; the controller holds it while waiting in
  `svc_stop_kthreads()` for that thread to exit.
  - Safe: `mutex_trylock()`, giving up on failure, as `nfsd()` does.
- `kthread_stop()` is not used on a service thread; the only thread functions
  are `nfsd()`, `lockd()` and `nfs4_callback_svc()`.
