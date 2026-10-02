- `dom` and `gdtc` in `struct dirty_throttle_control`
  (`include/linux/writeback.h`): exist only under `CONFIG_CGROUP_WRITEBACK`,
  so code outside that `#ifdef` must use `dtc_dom()` and `mdtc_gdtc()`, not
  the fields.
- **Potentially unsafe usage**: handing a dtc built with `MDTC_INIT()` to
  code that calls `dtc_dom()`.
  - Unsafe: when nothing tested the domain first and the wb belongs to a
    memcg without parent; `mem_cgroup_wb_domain()` returns NULL and
    `__wb_calc_thresh()` and `hard_dirty_limit()` dereference it.
  - Safe: after `mdtc_valid()`, as in `balance_dirty_pages()` and
    `wb_over_bg_thresh()`.
  - Safe: `cgwb_calc_thresh()`, because its caller `cgwb_debug_stats_show()`
    tests `mem_cgroup_wb_domain()` first.
- `domain_dirty_limits()` on a memcg dtc: reads only `gdtc->avail` from the
  global dtc; the ratios come from the sysctls.
- Needed first: `domain_dirty_avail()` on the gdtc, then on the mdtc
  (`mdtc_calc_avail()` reads `gdtc->avail` and `gdtc->dirty`);
  `domain_dirty_limits()` on the gdtc is not needed, see
  `cgwb_calc_thresh()`.
- `gdtc->avail` left at 0 with `vm_dirty_bytes` or `dirty_background_bytes`
  set: `domain_dirty_limits()` divides by it.
- `domain_dirty_limits()`: does not call `dtc_dom()`; its one domain read is
  `global_wb_domain.dirty_limit` in the `rt_or_dl_task()` boost, applied to
  memcg dtcs too.
- `dom->dirty_limit` readers other than `update_dirty_limit()`: plain reads
  without `dom->lock` and without `READ_ONCE()`, for example
  `hard_dirty_limit()`.
- Direct users of `global_wb_domain`: search for the name;
  `node_dirty_limit()` and the sysctl handlers are not among them, and
  `global_dirty_limits()` goes through a dtc built with `GDTC_INIT_NO_WB`.
- Tracepoints cannot call `dtc_dom()`: it is static in `mm/page-writeback.c`
  and the bodies in `include/trace/events/writeback.h` are built in
  `fs/fs-writeback.c`.
- `balance_dirty_pages` tracepoint: takes the chosen dtc and reports
  `dtc->limit`, which already holds that dtc's own hard limit.
- `dtc->limit`: written only by `wb_position_ratio()`, which
  `balance_wb_limits()` skips in freerun; a tracepoint that reads it must
  fire only after `wb_position_ratio()` ran on that dtc.
- `global_dirty_state` tracepoint: reads `global_wb_domain.dirty_limit`; it
  takes no dtc and `domain_dirty_limits()` emits it only when `mdtc_gdtc()`
  is NULL.
