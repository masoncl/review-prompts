- `fuse_use_readdirplus()` in auto mode (`fc->readdirplus_auto`): true when
  `FUSE_I_ADVISE_RDPLUS` was set (test-and-clear, so one advice buys one
  request) and also true whenever `ctx->pos == 0`.
- `fc->do_readdirplus`: set only from the INIT reply. No error from
  `FUSE_READDIRPLUS` clears it; there is no fallback to `FUSE_READDIR`.
- `fuse_advise_use_readdirplus()` callers: `fuse_lookup()` on a positive
  result, and `fuse_dentry_revalidate()` only when the dentry has not expired
  and `FUSE_I_INIT_RDPLUS` was set on the child. Getattr never calls it.
- Existing dentry with the same node id, not stale, not bad:
  `fuse_direntplus_link()` does `fi->nlookup++` under `fi->lock` itself and
  calls `fuse_change_attributes()`; it does not call `fuse_iget()`.
- Existing dentry that is negative, has another node id, or is stale:
  `fuse_make_bad()` if stale, then `d_invalidate()` and a retry through
  `d_alloc_parallel()`.
- Existing dentry with the same node id, not stale, whose inode is bad:
  `-EIO`.
- `fuse_iget()` is reached only for a dentry that is `d_in_lookup()`.
- `d_splice_alias()` failure after `fuse_iget()`: `fuse_direntplus_link()`
  does `fi->nlookup--` before it returns the error, because the caller sends a
  FORGET for the same reply.
- `parse_dirplusfile()`: any nonzero return of `fuse_direntplus_link()`
  (`-EIO`, `-ENOMEM`, a `d_alloc_parallel()` error) leads to
  `fuse_force_forget()` for that node id. The error is then dropped; readdir
  itself still succeeds.
- Name with zero length, longer than `FUSE_NAME_MAX`, or containing `/`:
  `parse_dirplusfile()` returns `-EIO` at once. That entry and all entries
  after it get neither `nlookup` nor a FORGET.
