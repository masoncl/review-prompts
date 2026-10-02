- `fi->i_time`: written only by `fuse_change_attributes_common()`; no
  invalidation helper touches it, staleness is marked in `fi->inval_mask` only.
- `fuse_invalidate_attr_mask()`: uses `set_mask_bits()`, not `atomic_or()`.
- Applying a reply: clears `STATX_BASIC_STATS` from `fi->inval_mask` (except
  when the `evict_ctr` test in `fuse_change_attributes_common()` fails), and
  `STATX_BTIME` only for a statx reply; other bits stay set.
- Refresh test in `fuse_update_get_attr()`:
  `request_mask & inval_mask & ~cache_mask`.
- Writeback cache, regular file: an invalid size, mtime or ctime bit alone
  never sends a request; expiry of `fi->i_time` still does.
- `fuse_get_cache_mask()`: 0 for anything that is not `S_ISREG()`, also with
  `fc->writeback_cache`.
- `fuse_do_setattr()` on a regular file under writeback cache: mtime and ctime
  come from the `struct iattr`, not the reply; size comes from the reply only
  for a truncate.
- `fuse_do_statx()`: applies the reply to the cache only if `sx->mask` holds
  all of `STATX_BASIC_STATS`.
- Page cache in `fuse_change_attributes_i()`: a size change truncates without
  `fc->auto_inval_data`; an mtime change invalidates only with it; both only
  when the cache mask is 0.
