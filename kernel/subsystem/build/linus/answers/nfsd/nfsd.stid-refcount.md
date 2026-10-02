| Kind | Count after creation | Holders |
|---|---|---|
| open, lock, delegation | 2: `nfs4_alloc_stid()` sets 1, the hash function does `refcount_inc()` | the creating operation puts one at its end; the caller for which the unhash helper returned true puts the other |
| layout | 1 | the creating operation; then one per `struct nfs4_layout` on `ls_layouts` |
| copy offload | 1 | the copy itself; `nfs4_put_copy()` puts it when the copy's own `refcount` reaches 0 |

- Stid allocated but never hashed: one put frees it, as
  `nfsd4_cleanup_open_state()` does for `op_stp`.
- `st_openstp`: a bare pointer; a lock stateid holds no reference on its open
  stateid.
- Layout lists `ls_perclnt` and `ls_perfile`, and the layout lease: hold no
  reference. `nfs4_put_stid()` does not unlink them;
  `nfsd4_free_layout_stateid()` does, after the count reached 0, so a list
  member can have a count of 0.
- v4.0 open stateid after CLOSE: the hash reference becomes the
  `oo_last_closed_stid` reference in `move_to_close_lru()`.
- `nfs4_put_stid()` on the final put, in order:
  1. `refcount_dec_and_lock()` takes `cl_lock`
  2. `idr_remove()` from `cl_stateids`
  3. decrement `cl_admin_revoked` if `SC_STATUS_ADMIN_REVOKED` is set
  4. read `sc_export`
  5. `nfs4_free_cpntf_statelist()`, which takes `s2s_cp_lock`
  6. unlock `cl_lock`
  7. `sc_free()`
  8. `exp_put()` on the export, if any
  9. `put_nfs4_file()` on the `sc_file` read at entry, if any
- `put_ol_stateid_locked()`: a second final-put path for open and lock
  stateids, entered with `cl_lock` held. It does steps 2 and 3, then queues
  the stid; `free_ol_stateid_reaplist()` does steps 7 to 9 after the unlock.
- `nfsd4_run_cb_notify()`: gives up, queueing nothing, when its
  `refcount_inc_not_zero()` fails.
- **Unsafe usage**: calling `nfs4_put_stid()` with `cl_lock` held; the final
  put takes `cl_lock`.
  - Safe: `put_ol_stateid_locked()` under the lock, then
    `free_ol_stateid_reaplist()` after unlocking, as `release_openowner()`
    does.
- **Potentially unsafe usage**: `refcount_inc()` on `sc_count` of a stid
  reached through a pointer or list.
  - Unsafe: when nothing held at that point keeps the count above 0; the
    final put may already have run and `sc_free()` follows.
  - Safe: under `cl_lock` on an entry just found in `cl_stateids`, as
    `find_stateid_by_type()` does; both final-put paths remove the entry
    under `cl_lock`.
  - Safe: under `fi_lock` on a member of `fi_stateids`, as
    `nfsd4_find_existing_open()` does; `unhash_ol_stateid()` unlinks
    `st_perfile` under `fi_lock` before the hash reference is put.
  - Safe: under `cl_lock` on a member of `st_locks` of a hashed open
    stateid, as `find_lock_stateid()` does; `unhash_lock_stateid()` unlinks
    `st_locks` under `cl_lock` before the hash reference is put.
  - Safe: under `deleg_lock` on a hashed delegation, as `nfs4_laundromat()`
    does; `unhash_delegation_locked()` asserts that lock.
  - Safe: under `flc_lock` on the `flc_owner` of a delegation lease still on
    `flc_lease`, as `nfsd4_deleg_getattr_conflict()` does;
    `destroy_unhashed_deleg()` removes the lease before its put.
  - Safe: under `ls_lock` with `ls_layouts` not empty, as
    `nfsd4_recall_file_layout()` does; `nfsd4_insert_layout()` takes one
    reference per entry.
  - Safe: when the caller already holds a reference, as `revoke_one_stid()`
    does with the one from `find_one_sb_stid()`.
  - Safe: `refcount_inc_not_zero()` under `ls_lock` where the pointer comes
    from the layout lease, as `nfsd4_layout_lm_breaker_timedout()` does;
    `nfsd4_free_layout_stateid()` removes the lease before it frees.
