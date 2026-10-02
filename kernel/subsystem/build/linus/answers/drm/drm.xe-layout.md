- `xe_device_get_gt()`: an id at or above
  `xe->info.tile_count * xe->info.max_gt_per_tile` returns NULL with no
  warning; the only `xe_assert()` is for a slot other than 0 or 1.
- GT id to tile: divided by `xe->info.max_gt_per_tile` (per platform, set
  in `xe_pci.c`), not by `XE_MAX_GT_PER_TILE`.
- There is no xe_tile_get_gt() in this tree.
- `for_each_gt_on_tile()`: wraps `for_each_gt()` over the whole device and
  keeps GTs with `gt->tile == tile`; `id__` is the device-wide GT id, not a
  slot within the tile.
- `for_each_gt_with_type()`: in `xe_device.h`; wraps `for_each_gt()` and
  filters on a mask of `BIT(gt->info.type)`.
- `xe->info.gt_count`: number of GTs present, counted with `for_each_gt()`
  in `xe_pci.c`; it is not the bound of GT ids, which is
  `xe->info.tile_count * xe->info.max_gt_per_tile`; with
  `max_gt_per_tile` 2, a tile with no media GT leaves its second id unused.
