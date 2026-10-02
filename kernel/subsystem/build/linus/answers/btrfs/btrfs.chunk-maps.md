- `struct btrfs_chunk_map`: has no `io_align` or `io_width` member; in
  `fs/btrfs/volumes.h` those belong to `struct btrfs_device`.
- `type` and `on_disk_type`: `on_disk_type` is the chunk item's value;
  `btrfs_chunk_alloc_add_chunk_item()` writes it to the chunk item and
  `fill_dummy_bgs()` copies it to the block group flags; `type` is what
  mapping code uses.
- `set_real_chunk_type()` in `fs/btrfs/volumes.c`: for a RAID5 or RAID6
  chunk with one data stripe, sets `type` to RAID1 or RAID1C3 instead.
- There is no btrfs_clone_chunk_map() here; a zoned block group keeps a
  counted pointer to the in-tree map in `physical_map`, taken with
  `btrfs_find_chunk_map()` in `btrfs_load_block_group_zone_info()`.
