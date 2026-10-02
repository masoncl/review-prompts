- `deleg_lock`: a spinlock in `struct nfsd_net`. `fs/nfsd` has no lock named
  `state_lock`.
- `se_lock`: a spinlock in `struct nfsd4_session`, taken only in
  `fs/nfsd/nfs4callback.c`. It nests with none of the listed locks.

| Outer | Inner | Function |
|---|---|---|
| `deleg_lock` | `client_lock` | `nfs4_laundromat()` |
| `deleg_lock` | `cl_lock`, then `fi_lock` | `nfs4_set_delegation()`, `nfsd_get_dir_deleg()` |
| `client_lock` | `async_lock` | `nfsd4_async_copy_reaper()`, `nfsd4_cancel_copy_by_sb()` |
| `client_lock` | `cl_lock`, then `flc_lock` | `nfs4_get_client_reaplist()` via `nfs4_anylock_blockers()` |
| `cl_lock` | `sc_lock` | `nfsd4_free_stateid()` |
| `cl_lock` | `s2s_cp_lock` | `nfs4_put_stid()` |
| `cl_lock` | `ls_lock` | `nfsd4_return_all_client_layouts()` |
| `cl_lock` | `fi_lock`, then `flc_lock` | `nfsd4_release_lockowner()` via `check_for_locks()` |
| `fi_lock` | `ls_lock` | `nfsd4_insert_layout()` |
| `ls_lock` | `sc_lock` | `nfsd4_insert_layout()` |
| `flc_lock` | `ls_lock` | `nfsd4_layout_lm_break()` |
| `st_mutex` | `cl_lock`, then `fi_lock` | `nfsd4_close()` via `nfsd4_close_open_stateid()` |
| `st_mutex` | `sc_lock` | `nfsd4_open_downgrade()` |
| `st_mutex` | `s2s_cp_lock` | `nfsd4_close()` via `nfsd4_close_open_stateid()` |
| `st_mutex` | `flc_lock` | `nfsd4_lock()` via `vfs_lock_file()` |
| `ls_mutex` | `fi_lock`, then `ls_lock`, then `sc_lock` | `nfsd4_layoutget()` via `nfsd4_insert_layout()` |
| `nfsd_mutex` | `client_lock` | `nfsd4_revoke_states()` |
| `nfsd_mutex` | `st_mutex`, `deleg_lock` | `nfsd4_revoke_states()` via `revoke_one_stid()` |
| `nfsd_mutex` | `nfsd_ssc_lock` | `nfsd_destroy_serv()` via `nfsd4_ssc_shutdown_umount()` |

- `deleg_lock` is outside `client_lock`, `cl_lock` and `fi_lock`; no code
  takes it while holding one of them.
- `nfs4_put_stid()`: its `refcount_dec_and_lock()` is on `cl_lock`, not
  `fi_lock`.
- Two `st_mutex` at once: only in `init_open_stateid()` and
  `init_lock_stateid()`. The outer one belongs to the new stateid, which is
  not hashed yet.
- `nfsd4_lock()`: unlocks the open stateid's `st_mutex` before it locks the
  lock stateid's.
- `nfsd4_process_open2()`: unlocks `st_mutex` before
  `nfs4_open_delegation()`, so `deleg_lock` is not taken under it there.
- `nfsd_break_deleg_cb()` and `nfsd4_lm_lock_expirable()`: run under
  `flc_lock` and take none of the listed locks.
- `nfsd_ssc_lock`: initialised and taken only under
  `CONFIG_NFSD_V4_2_INTER_SSC`; dropped around every `mntput()`.
