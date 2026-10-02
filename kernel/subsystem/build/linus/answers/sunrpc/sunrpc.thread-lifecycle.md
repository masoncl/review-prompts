| Function | Runs in | Service mutex |
|---|---|---|
| `svc_new_thread()` | controller, or `nfsd()` growing its own pool | held by the caller |
| `svc_thread_init_status()` | the new thread | not taken by the thread; the creator holds it and waits |
| `svc_exit_thread()` | the exiting thread, or `svc_new_thread()` on failure | held by someone: the controller waiting in `svc_stop_kthreads()`, the caller of `svc_new_thread()`, or the thread itself |

- "Service mutex" is the service's own lock: `nfsd_mutex`, `nlmsvc_mutex` or
  `nfs_callback_mutex`; none of the three functions takes or asserts it.
- `svc_prepare_thread()` takes no lock: it changes `sv_nrthreads`,
  `sp_nrthreads` and `sp_all_threads` under the caller's mutex alone, not
  under `sv_lock`.
- `svc_exit_thread()` changes the same three with no lock around them; it
  takes `sv_lock` only afterwards, inside `svc_sock_update_bufs()`.
- Failed initialisation: `svc_thread_init_status()` with a nonzero error ends
  in `kthread_exit()`, so the thread never calls `svc_exit_thread()`;
  `svc_new_thread()` calls it on the thread's behalf.
- `kthread_create_on_node()` failure: `svc_new_thread()` likewise calls
  `svc_exit_thread()` itself.
