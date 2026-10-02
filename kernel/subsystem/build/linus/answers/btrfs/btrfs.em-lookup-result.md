- `btrfs_search_extent_mapping()`: takes `(tree, start, len)`; `strict` is a
  parameter of the static `lookup_extent_mapping()` only.
- `btrfs_search_extent_mapping()` order: the map that contains `start`, else
  the next map after `start`, else the previous map; `NULL` only for an empty
  tree.
- `btrfs_add_extent_mapping()` precondition: `*em_in` contains `start`;
  `btrfs_get_extent()` tests this before the call and returns `-EIO`.
- Without that precondition, on `-EEXIST` `merge_extent_mapping()` can return
  `-EINVAL`, which trips `ASSERT(ret == 0 || ret == -EEXIST)`.
- `btrfs_add_extent_mapping()` inserts as not modified, so `try_merge_map()`
  runs: on success `*em_in` may cover more than the caller filled in and
  carry `EXTENT_FLAG_MERGED`.
- `btrfs_add_extent_mapping()` failure: the map is already freed and
  `*em_in` is `NULL`; the caller must not free the pointer it passed in.
- After the call `btrfs_get_extent()` tests only the return value.
- After a lookup the caller tests that the map contains the offset it wants:
  `btrfs_get_extent()` drops a map with `em->start > start`;
  `btrfs_unpin_extent_cache()` returns `-EUCLEAN` if `em->start != start`.
