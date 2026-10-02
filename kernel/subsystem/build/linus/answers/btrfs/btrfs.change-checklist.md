- Fiemap (`extent_fiemap()` in `fs/btrfs/fiemap.c`) and seek
  (`find_desired_extent()` in `fs/btrfs/file.c`): read file extent items, not
  extent maps; there is no btrfs_get_extent_fiemap().
- `btrfs_swap_activate()`: reads file extent items with `btrfs_search_slot()`.
- Compressed readahead is `add_ra_bio_folios()` in `fs/btrfs/compression.c`;
  there is no add_ra_bio_pages().
- `add_ra_bio_folios()` adds a folio only when
  `btrfs_extent_map_block_start()` of the map it looks up equals the sector
  of the original bio, that is, the map points to the same compressed extent.
- Direct I/O: `btrfs_dio_iomap_begin()` and
  `btrfs_get_blocks_direct_write()` in `fs/btrfs/direct-io.c`; there is no
  btrfs_get_blocks_direct().
- `defrag_get_extent()`: builds a map from the file extent item and never
  inserts it; the tree reader is `defrag_lookup_extent()`.
- `log_one_extent()`: writes `trans->transid` as the item's generation, not
  `em->generation`; `em->generation` only decides whether the map is logged.
- `btrfs_get_extent_allocation_hint()`: uses
  `btrfs_search_extent_mapping()`, so the map may not overlap the range; it
  needs only a real `disk_bytenr`.
- `btrfs_find_new_delalloc_bytes()`: sets `EXTENT_DELALLOC_NEW` over ranges
  whose map has `disk_bytenr == EXTENT_MAP_HOLE`.
- `btrfs_rewrite_logical_zoned()`: requires `em->offset == 0` (`ASSERT()`)
  and writes `disk_bytenr`.
- Other readers: search for callers of `btrfs_get_extent()`,
  `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`.
