# Btrfs Subsystem Details

## Extent Map Fields

The `extent_map` struct (`fs/btrfs/extent_map.h`) maps file offsets to on-disk
locations. Fields correspond to the on-disk `btrfs_file_extent_item`.

- `start`: file offset (matches the key offset of `BTRFS_EXTENT_DATA_KEY`)
- `len`: number of file bytes this extent map covers (`num_bytes` on disk; for inline extents always `sectorsize`)
- `disk_bytenr`: physical byte address on disk (or sentinel `EXTENT_MAP_HOLE` / `EXTENT_MAP_INLINE`)
- `disk_num_bytes`: full size of the on-disk allocation (compressed size when compression is used)
- `offset`: offset within the decompressed extent where this file range starts (nonzero for reflinked/cloned partial references)
- `ram_bytes`: decompressed size of the entire on-disk extent (equals `disk_num_bytes` for uncompressed extents)

### Uncompressed vs Compressed Layout

```
Uncompressed:
  On-disk:    [disk_bytenr .................. disk_bytenr + disk_num_bytes]
                           |<-- offset -->|<------- len ------->|
  File:                                   [start ... start + len]
  ram_bytes == disk_num_bytes

Compressed:
  On-disk:    [disk_bytenr ... disk_bytenr + disk_num_bytes]  (smaller)
  Decompressed: [0 ................................ ram_bytes]
                    |<-- offset -->|<------- len ------->|
  File:                            [start ... start + len]
  ram_bytes > disk_num_bytes
```

### Computed Helpers (Replaced Legacy Fields)

The old `block_start`, `block_len`, `orig_block_len`, and `orig_start` fields
have been removed. Use the helper functions instead:

- `btrfs_extent_map_block_start(em)`: for uncompressed returns `disk_bytenr + offset`, for compressed returns `disk_bytenr`
- `extent_map_block_len(em)`: for uncompressed returns `len`, for compressed returns `disk_num_bytes`

### Invariants (from `validate_extent_map()`)

For real data extents (`disk_bytenr < EXTENT_MAP_LAST_BYTE`):
- `disk_num_bytes != 0`
- `offset + len <= ram_bytes`
- Uncompressed: `offset + len <= disk_num_bytes`
- Uncompressed: `ram_bytes == disk_num_bytes`

For holes/inline (`disk_bytenr >= EXTENT_MAP_LAST_BYTE`):
- `offset == 0`

### BT-001: Extent Map Field Confusion

These fields each represent a different size, but code sometimes uses the wrong
one (e.g., `ram_bytes` where `len` is needed). This is hard to catch because
for uncompressed extents without partial references all three are equal — the
wrong field gives the right answer. The fields only diverge with compressed
extents or partial references into shared extents (reflinks and bookend extents):

- `len` vs `ram_bytes`: `ram_bytes` is the full decompressed extent size,
  which may be much larger than `len` (the file range). Using `ram_bytes`
  where `len` is intended causes over-reads or oversized allocations.
- `len` vs `disk_num_bytes`: for compressed extents, `disk_num_bytes` is
  smaller than `len`. Using `len` for on-disk I/O sizing reads past the
  extent. Using `disk_num_bytes` for file-level sizing truncates data.
- `disk_bytenr` vs `btrfs_extent_map_block_start()`: raw `disk_bytenr`
  is the start of the full on-disk extent. For uncompressed partial
  references, the actual data starts at `disk_bytenr + offset`.

| Intent | Correct Field | Common Mistake |
|--------|--------------|----------------|
| File range covered by this extent | `len` | `ram_bytes` |
| On-disk bytes to read/write | `disk_num_bytes` | `len` |
| Decompressed extent size | `ram_bytes` | `disk_num_bytes` |
| Physical disk location for I/O | `btrfs_extent_map_block_start()` | raw `disk_bytenr` |

**REPORT as bugs**: Code that uses `ram_bytes` or `disk_num_bytes` where `len`
is intended (or vice versa), particularly in I/O paths, extent splitting, or
size calculations that feed into allocations or boundary checks.
