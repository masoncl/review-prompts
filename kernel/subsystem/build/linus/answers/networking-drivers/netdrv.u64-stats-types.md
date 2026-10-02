- Variant selection: `include/linux/u64_stats_sync.h` tests `BITS_PER_LONG`
  only; no `CONFIG_` symbol appears in the header.
- `u64_stats_add()` and `u64_stats_inc()` on 64-bit: `local64_add()` and
  `local64_inc()` resolve to the arch `local_add()` and `local_inc()`; x86
  uses an unlocked `add`/`inc` in `arch/x86/include/asm/local.h`, while
  `include/asm-generic/local.h` maps them to `atomic_long_add()` and
  `atomic_long_inc()`.
- `u64_stats_update_begin()` on 32-bit: `preempt_disable_nested()` then
  `write_seqcount_begin()`; `u64_stats_update_end()` is
  `write_seqcount_end()` then `preempt_enable_nested()`.
- `u64_stats_add()`: takes `unsigned long` on both word sizes, so on 32-bit a
  value wider than 32 bits is truncated before the add; `u64_stats_sub()`
  takes `s64` and `u64_stats_set()` takes `u64`.
- `u64_stats_copy()`: defined for both word sizes; a loop of `local64_read()`
  over 64-bit words on 64-bit, `memcpy()` on 32-bit; `BUILD_BUG_ON()` if `len`
  is not a multiple of `sizeof(u64_stats_t)`.
- `u64_stats_copy()` arguments are `void *`; in-tree callers pass structs of
  plain `u64`, for example `struct macsec_rx_sc_stats`.
- Plain `u64` counters under a `struct u64_stats_sync`: present in-tree, for
  example `struct vxlan_vni_stats` in `include/net/vxlan.h`; nothing enforces
  `u64_stats_t`.
- Plain `u64` counters on 64-bit: the begin, end and fetch helpers are empty,
  so those fields get ordinary loads and stores and nothing else.
