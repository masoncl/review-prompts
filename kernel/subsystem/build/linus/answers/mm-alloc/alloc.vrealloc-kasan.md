- `kasan_poison()`: does `WARN_ON()` and returns without poisoning when the
  address or the size is not a multiple of `KASAN_GRANULE_SIZE`; it rounds
  nothing.
- `__kasan_poison_vmalloc()` in `mm/kasan/shadow.c`: rounds the size up, then
  calls `kasan_poison()`; the start must still be aligned.
- `__kasan_vrealloc()`: in `mm/kasan/common.c`, under `CONFIG_KASAN_VMALLOC`;
  without it `kasan_vrealloc()` is an empty stub in `include/linux/kasan.h`.
- `__kasan_vrealloc()`: has no alignment test and no early return; equal sizes
  do nothing.
- Shrink, in order:
  - `kasan_poison_last_granule(addr, new_size)` marks the partly used granule
    at the new end.
  - Both sizes are rounded up to `KASAN_GRANULE_SIZE`.
  - If the rounded sizes still differ, `__kasan_poison_vmalloc()` poisons
    from the rounded new end to the rounded old end.
- Shrink never unpoisons, and leaves bytes below the new end accessible.
- Grow: rounds `old_size` down, then `__kasan_unpoison_vmalloc()` from there
  to `new_size`, with `KASAN_VMALLOC_PROT_NORMAL | KASAN_VMALLOC_VM_ALLOC |
  KASAN_VMALLOC_KEEP_TAG`; it does not start from `addr`.
- `addr`: `__kasan_vrealloc()` does not align it; the rounded offsets are
  granule aligned only if `addr` is.
- Outside `CONFIG_KASAN_GENERIC`: `kasan_poison_last_granule()` is an empty
  stub in `mm/kasan/kasan.h`, so a shrink that stays inside one granule
  changes nothing.
- Hardware tag-based KASAN: `__kasan_poison_vmalloc()` in
  `mm/kasan/hw_tags.c` is empty, so a shrink poisons nothing.
