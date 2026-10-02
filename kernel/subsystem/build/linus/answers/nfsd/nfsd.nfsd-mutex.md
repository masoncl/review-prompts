- Names not in this tree: nfsd_put(), and the fields nfsd_net_up and
  keep_active. `nfsd_destroy_serv()` tears the server down; `NFSD_NET_UP` and
  `NFSD_NET_LOCKD_UP` are bits of `enum nfsd_net_flag` in `nn->flags`.
- `struct svc_serv`: has no reference count here.
- Pool mode: not protected by `nfsd_mutex`.
- `parallel_ops` is set in `nfsd_nl_family`, so genetlink takes no lock around
  handlers; a handler that needs `nfsd_mutex` takes it itself.
- Three states, told apart under `nfsd_mutex`: `nn->nfsd_serv` NULL;
  `nn->nfsd_serv` set but `NFSD_NET_UP` clear (listeners added, no threads
  yet); `NFSD_NET_UP` set. Only `nfsd_startup_net()`, reached from
  `nfsd_svc()`, sets the bit.
- `nfsd_destroy_serv()`: does not stop threads, and neither does
  `svc_destroy()`. Every caller reaches it with `sv_nrthreads` at 0;
  `nfsd_shutdown_threads()` calls `svc_set_num_threads()` with 0 first.
- `nfsd_destroy_serv()` order: clear `nn->nfsd_serv` under
  `nfsd_notifier_lock`, unregister the notifiers if last user,
  `svc_xprt_destroy_all()`, `nfsd_shutdown_net()`, `svc_destroy()`.
  `nfsd_file_dispose_list_delayed()` in `fs/nfsd/filecache.c` depends on the
  pointer being cleared before the file cache shuts down and freed after.
- `nfsd_shutdown_net()`: waits under the mutex for `nfsd_net_ref` to drain
  (`nfsd_net_free_done`), so a holder of an `nfsd_net_try_get()` reference
  that blocks on `nfsd_mutex` deadlocks shutdown.
- `svc_pool_stats_start()` takes the mutex through `si->mutex` and
  `svc_pool_stats_stop()` drops it; `svc_pool_stats_open()` does not take it.

| Helper | `nfsd_mutex` |
|---|---|
| `nfsd_nrthreads()`, `nfsd_shutdown_threads()` | takes it; deadlocks if the caller holds it |
| `nfsd_nrpools()`, `nfsd_get_nrthreads()` | neither takes nor asserts; caller must hold it |
| `nfsd_svc()`, `nfsd_set_nrthreads()`, `nfsd_destroy_serv()` | `lockdep_assert_held()` |
| `nfsd_create_serv()` | `WARN_ON(!mutex_is_locked())` |

- **Unsafe usage**: calling `nfsd_nrpools()` or `nfsd_get_nrthreads()` without
  `nfsd_mutex`; both dereference `nn->nfsd_serv` unlocked.
  - Safe: inside the locked region, as `write_pool_threads()` and
    `nfsd_nl_threads_get_doit()` do.
- **Potentially unsafe usage**: reading `nn->nfsd_serv` without `nfsd_mutex`.
  - Unsafe: outside an nfsd thread, with no lock that `nfsd_destroy_serv()`
    takes; the pointer is cleared and `svc_destroy()` frees the serv.
  - Safe: in an nfsd thread, because the pointer is cleared only once
    `sv_nrthreads` is 0; `check_forechannel_attrs()` does this.
  - Safe: under `nfsd_notifier_lock`, which `nfsd_create_serv()` and
    `nfsd_destroy_serv()` hold when they write the pointer;
    `nfsd_inetaddr_event()` does this. The lock is static to
    `fs/nfsd/nfssvc.c`.
  - Safe: under `nfsd_gc_lock`, as `nfsd_file_dispose_list_delayed()` does;
    `nfsd_file_cache_shutdown_net()`, reached from `nfsd_destroy_serv()`,
    takes that lock after the pointer is cleared and before `svc_destroy()`.
    The lock is static to `fs/nfsd/filecache.c`.
- **Potentially unsafe usage**: taking `nfsd_mutex` in an nfsd thread.
  - Unsafe: with `mutex_lock()`; `svc_stop_kthreads()` waits for the thread to
    exit while its caller holds the mutex.
  - Safe: with `mutex_trylock()`, as `nfsd()` does to spawn or retire a
    dynamic thread; a retiring thread keeps the mutex across
    `svc_exit_thread()`.
- **Unsafe usage**: calling `nfsd4_revoke_states()`,
  `nfsd4_revoke_export_states()` or `nfsd4_cancel_copy_by_sb()` without first
  testing `NFSD_NET_UP` under `nfsd_mutex`; they assert the mutex only, and
  walk `nn->conf_id_hashtbl`, which exists only between
  `nfs4_state_create_net()` and `nfs4_state_destroy_net()`.
  - Safe: test the bit inside the locked region, as
    `nfsd_nl_unlock_export_doit()` and `write_unlock_fs()` do.
