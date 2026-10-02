- Implemented, with CB_NOTIFY: `nfsd4_get_dir_delegation()` calls
  `nfsd_get_dir_deleg()`; `nfsd4_cb_notify_ops` sends the notifications.
- Notifications granted: `requested & SUPPORTED_NOTIFY_MASK`, and only if
  the client set `NOTIFY4_GFLAG_EXTEND` and not `NOTIFY4_CFLAG_ORDER`;
  otherwise the delegation is recall-only.
- Lease: `F_RDLCK` with `FL_DELEG`, plus one `FL_IGN_DIR_CREATE`,
  `FL_IGN_DIR_DELETE` or `FL_IGN_DIR_RENAME` flag per granted add, remove or
  rename notification, from `nfsd_notify_to_ignore()`.
- Hashing: same three locks and same `nfs4_delegation_exists()` test as a
  file delegation.
- Two routes carry a directory change to NFSD:

| Route | Used for | Path |
|---|---|---|
| Lease break | event types not granted | `try_break_deleg()` (`include/linux/filelock.h`), called from `fs/namei.c` with a `LEASE_BREAK_DIR_CREATE`, `LEASE_BREAK_DIR_DELETE` or `LEASE_BREAK_DIR_RENAME` flag, then `nfsd_break_deleg_cb()` |
| fsnotify | event types granted | `nfsd_dir_fsnotify_handle_event()` in `fs/nfsd/filecache.c`, then `nfsd_handle_dir_event()` |

- `ignore_dir_deleg_break()` in `fs/locks.c`: makes `__break_lease()` skip
  a lease whose `FL_IGN_DIR_CREATE`, `FL_IGN_DIR_DELETE` or
  `FL_IGN_DIR_RENAME` flag matches the event.
- `nfsd_fsnotify_recalc_mask()`: rebuilds the fsnotify mark's mask from
  `inode_lease_ignore_mask()`; call it after adding or removing a directory
  lease.
- Without `CONFIG_NFSD_V4`: `nfsd_dir_fsnotify_handle_event()` is a stub
  that returns 0.
- `nfsd_handle_dir_event()`: turns `FS_MOVED_FROM` into `FS_DELETE` and
  `FS_MOVED_TO` into `FS_CREATE`.
- `nfsd_handle_dir_event()`: drops `FS_RENAME` when the dentry's parent is
  not this directory.
- `should_notify_deleg()`: skips a lease that lacks the `FL_IGN_DIR_CREATE`,
  `FL_IGN_DIR_DELETE` or `FL_IGN_DIR_RENAME` flag for the event.
- Queue: `ncn_evt[]` in `struct nfsd4_cb_notify`, one per delegation,
  `NOTIFY4_EVENT_QUEUE_SIZE` (3) entries, under `ncn_lock`.
- Send limit: `nfsd4_cb_notify_prepare()` keeps one slot back when
  `NOTIFY4_CHANGE_DIR_ATTRS` was granted, so 2 events fit.
- Encode buffer: `NOTIFY4_PAGE_ARRAY_SIZE` (1) page.
- In flight: `nfsd4_cb_notify_release()` requeues the callback if events
  arrived meanwhile and `sc_status` is 0.
- A recall replaces the notification when:
  - `alloc_nfsd_notify_event()` fails: `nfsd_recall_all_dir_delegs()`
    recalls every NFSD lease on the directory.
  - `ncn_evt_cnt` has reached `NOTIFY4_EVENT_QUEUE_SIZE` in
    `nfsd_handle_dir_event()`.
  - `nfsd4_cb_notify_prepare()` finds more events than its limit, finds
    `fi_deleg_file` NULL, or fails to encode an event or the directory
    attributes.
  - `nfsd4_cb_notify_done()`, with `sc_status` 0, sees `ncn_encode_err`, or
    a `tk_status` other than 0 or `-NFS4ERR_DELAY`.
