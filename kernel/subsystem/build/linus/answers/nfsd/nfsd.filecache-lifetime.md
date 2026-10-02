- The hash table holds no reference.
- LRU reference: `nfsd_file_lru_add()` takes it, and is called once, from
  `nfsd_file_do_acquire()` when a GC entry is constructed.
- `nfsd_file_put()`: for a hashed GC entry sets `NFSD_FILE_REFERENCED` and
  `NFSD_FILE_RECENT`, then only decrements; it never touches the LRU.
- Laundrette: walks with `nfsd_file_gc_cb()`, which clears `NFSD_FILE_RECENT`
  and `NFSD_FILE_REFERENCED` and rotates; an entry is disposed on a later pass
  if it was not used in between.
- Shrinker: walks with `nfsd_file_lru_cb()` directly; it tests
  `NFSD_FILE_REFERENCED` and ignores `NFSD_FILE_RECENT`.
- `EXPORT_OP_FLUSH_ON_CLOSE`: makes `nfsd_file_lru_cb()` skip an entry opened
  for write that has dirty or writeback pages; see
  `nfsd_file_check_writeback()`. It starts no writeback.
- Without that flag, dirty pages do not keep an entry on the LRU.
- `EXPORT_OP_CLOSE_BEFORE_UNLINK`: gates `nfsd_file_close_inode_sync()` in
  `nfsd_unlink()` and `nfsd_rename()`.
- `nfsd_rename()`: acts on the rename target only, and only if
  `nfsd_file_is_cached()` finds a GC entry; it closes after `end_renaming()`
  and then retries the rename.
- `nfsd_file_lease_notifier_call()`: runs when a lease is being set, not when
  one is broken, and acts only for `FL_LEASE`.
- `nfsd_file_queue_for_close()`: skips non-GC entries, so the lease, fsnotify
  and unlink/rename closes never touch NFSv4 state's files.
- `nfsd_file_close_export()`: closes GC entries under an export path, in the
  caller; reached from `nfsd_nl_unlock_export_doit()` in `fs/nfsd/nfsctl.c`.
- No cache entry is closed or purged on unmount, on unlock-filesystem, or to
  evict an entry after a writeback error.
- `__nfsd_file_cache_purge()`: unhashes GC and non-GC entries alike.
- `nfsd_file_cond_queue()`, used by every close above except the LRU walks:
  closes an entry only if dropping the LRU reference leaves none; an entry
  still held is only unhashed and closes at its holder's last put.
- "Sync" therefore means the unreferenced entries are closed on return, not
  that the inode has no open file.
- Queued closes (laundrette, shrinker, lease, fsnotify): moved to
  `nn->fcache_dispose_list`; nfsd threads close them in
  `nfsd_file_net_dispose()`, called from the `nfsd()` thread loop.
