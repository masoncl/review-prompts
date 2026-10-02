- There is no extent_map_end() here; `btrfs_extent_map_end()` gives the end
  of the file range.
- `btrfs_submit_compressed_read()`: reads `em->disk_num_bytes` directly for
  the compressed length and never reads `ram_bytes`; the decompressed length
  it handles is the size of the original bio, and `cb->start` is
  `em->start - em->offset`.
- `ram_bytes` readers outside `fs/btrfs/extent_map.c`: only
  `btrfs_encoded_read()` (as `unencoded_len`) and `log_one_extent()`.
