- Count: lives in the top `SWP_TB_COUNT_BITS` bits of the slot's table word
  (`mm/swap_table.h`); there is no swap_map array, no SWAP_HAS_CACHE bit and
  no SWAP_MAP_MAX or SWAP_MAP_BAD in this tree.
- Formats of a table word, told apart by the low bits:

| Format | Low bits | Slot state | Test |
|---|---|---|---|
| NULL | word is 0 | free | `swp_tb_is_null()` |
| Shadow | bit 0 set | in use, not cached; count >= 1 | `swp_tb_is_shadow()` |
| PFN | `SWP_TB_PFN_MARK` (`0b10`) | folio in swap cache; count >= 0 | `swp_tb_is_folio()` |
| Bad | word equals `SWP_TB_BAD` | never allocatable | `swp_tb_is_bad()` |

- PFN format: stores the folio's PFN, not a pointer; `swp_tb_to_folio()`
  converts; no helper in `mm/swap_table.h` builds or tests a pointer format.
- Shadow format: used for every in-use uncached slot, also with a NULL
  workingset shadow (`__swap_cache_do_del_folio()` in `mm/swap_state.c`).
- Count 0: only a NULL or a PFN word has it once the cluster lock is dropped;
  `cluster_scan_range()` in `mm/swapfile.c` warns otherwise.
- `swp_tb_get_count()`: returns `-EINVAL` for a bad slot;
  `__swp_tb_get_count()` warns instead, use it only on a countable word.
- Constructors: `shadow_to_swp_tb()`, `pfn_to_swp_tb()` and its wrapper
  `folio_to_swp_tb()`, each takes the flags (count and zero flag) to keep;
  there is no shadow_swp_to_tb().
- Zero-filled marker: `SWP_TB_ZERO_FLAG` in the same word; when
  `SWAP_TABLE_HAS_ZEROFLAG` is 0 it is the per-cluster `zero_bitmap`. There is
  no zeromap bitmap in `struct swap_info_struct`; use
  `__swap_table_test_zero()`.
- `swap_table_get()`: the lockless reader; takes `rcu_read_lock()` itself and
  returns NULL format when the cluster has no table.
- `__swap_table_get()`: accepts the cluster lock or an RCU read section, and
  does not check for a missing table; `folio_maybe_swapped()` uses it under
  RCU with the folio locked.
