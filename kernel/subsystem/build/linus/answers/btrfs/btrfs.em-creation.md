- `btrfs_extent_item_to_extent_map()`, uncompressed regular or prealloc
  extent: `ram_bytes` is overwritten with `disk_num_bytes`; the item's
  `ram_bytes` is kept only for compressed, hole and inline items.
- `btrfs_alloc_extent_map()` uses `kmem_cache_zalloc()`; in-tree builders
  leave members that are 0 unset.
- For example `btrfs_cont_expand()` and `fill_holes()` do not set `offset`;
  `setup_relocation_extent_mapping()` sets neither `offset` nor `generation`.
- `btrfs_get_extent()` builds by hand only the implicit hole: `start`, `len`
  and `disk_bytenr = EXTENT_MAP_HOLE`, the rest 0; inline maps come from
  `btrfs_extent_item_to_extent_map()`.
- Hole maps added as modified set `ram_bytes = len`, as `fill_holes()` does;
  `log_one_extent()` copies `em->ram_bytes` into the logged item.
- Write maps: `btrfs_create_io_em()` sets `generation = -1` with
  `EXTENT_FLAG_PINNED`; `defrag_collect_targets()` reads
  `generation == (u64)-1` as under writeback and skips the map.
- `validate_extent_map()` on any real extent: `offset + len <= ram_bytes`,
  non-zero `disk_num_bytes`, and sector alignment of `start`, `len`,
  `disk_bytenr`, `disk_num_bytes`, `offset` and `ram_bytes`.
