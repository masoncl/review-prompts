- After a merge of real extents (`merge_ondisk_extents()`):

| Member | Value |
|---|---|
| `disk_bytenr` | minimum of the two |
| `disk_num_bytes` | larger disk end of the two, minus new `disk_bytenr` |
| `offset` | `prev->disk_bytenr + prev->offset`, minus new `disk_bytenr` |
| `ram_bytes` | new `disk_num_bytes` |
| `generation` | maximum of the two |

- Merged hole: only `start`, `len`, `generation` and `flags` change;
  `ram_bytes` is not updated.
- `EXTENT_FLAG_MERGED` is set on the surviving map;
  `defrag_lookup_extent()` in `fs/btrfs/defrag.c` discards such a map and
  rebuilds from the file extent item.
- `refs > 2` test in `try_merge_map()`: covers only the map that survives.
- Absorbed neighbour: removed from the tree whatever its `refs`, members
  untouched; a holder detects it with `btrfs_extent_map_in_tree()`, as
  `get_extent_map()` in `fs/btrfs/extent_io.c` does.
- `try_merge_map()` is reached through `setup_extent_mapping()` with
  `modified` false, from `add_extent_mapping()` and from
  `replace_extent_mapping()`.
- `btrfs_unpin_extent_cache()`: merges nothing while the map is still on
  `modified_extents`, which is where `btrfs_create_io_em()` put it.
