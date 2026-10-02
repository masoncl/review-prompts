- `btrfs_prev_leaf()`: `static` in `fs/btrfs/ctree.c`, not callable from other
  files; at `path->slots[0] == 0` use `btrfs_previous_item()`,
  `btrfs_previous_extent_item()`, `btrfs_search_backwards()`, or
  `btrfs_search_slot_for_read()` with `find_higher` 0.
- `btrfs_next_item()`: increments `path->slots[0]` before it tests against
  `btrfs_header_nritems()`, so straight after a not-found search it skips the
  item at the insert slot; `btrfs_get_next_valid_item()` tests without
  incrementing.
- `btrfs_next_leaf()`: releases the path and searches again, so a leaf pointer
  saved before the call is stale; reload it from `path->nodes[0]`, as
  `btrfs_lookup_csums_list()` in `fs/btrfs/file-item.c` does.
- `btrfs_next_leaf()` returning 0: the slot can be a later slot of the same
  leaf, not slot 0 of a new one, when items were added while the path was
  released; see `btrfs_next_old_leaf()`.
