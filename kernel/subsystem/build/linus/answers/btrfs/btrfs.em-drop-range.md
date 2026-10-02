- Tail piece, any real extent, compressed included:
  `offset = em->offset + end - em->start`; `disk_bytenr`, `disk_num_bytes`,
  `ram_bytes` copied.
- Hole or inline piece: `disk_bytenr` copied, `disk_num_bytes = 0`,
  `offset = 0`, `ram_bytes` = length of the piece.
- Flags of the pieces: the old flags without `EXTENT_FLAG_LOGGING`;
  `EXTENT_FLAG_PINNED` is inherited.
- Old map: loses `EXTENT_FLAG_PINNED`, keeps `EXTENT_FLAG_LOGGING`.
- Pieces go on `modified_extents` when `em->list` of the old map was not
  empty, which is also true of a map with `EXTENT_FLAG_LOGGING` that still
  waits on the private list of `btrfs_log_changed_extents()`.
- No spare map for a map still in the tree: the whole map is removed;
  `btrfs_set_inode_full_sync()` is called only if the map was on a list and
  reached outside the range.
- `btrfs_split_extent_map()` requires a map that is pinned, on
  `modified_extents`, without `EXTENT_FLAG_LOGGING`, uncompressed, a real
  extent, with `em->len == len`, and `0 < pre < len`.
- All of those are `ASSERT()`, compiled out without `CONFIG_BTRFS_ASSERT`.
- `btrfs_split_extent_map()` runtime errors: `-ENOMEM`, and `-EIO` only when
  the lookup finds no map.
- Callers skip `btrfs_split_extent_map()` for `BTRFS_ORDERED_NOCOW` ordered
  extents; see `btrfs_extract_ordered_extent()`.
