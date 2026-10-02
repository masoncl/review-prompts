- `__sta_info_destroy()` and `__sta_info_flush()`: every downward transition
  they make runs after the grace period, in `__sta_info_destroy_part2()`;
  none runs before `synchronize_net()`.
- `drv_sta_pre_rcu_remove()`: called in `__sta_info_destroy_part1()` after
  the station has left both hashes and `local->sta_list`, so a lookup from
  inside the callback does not find it.
- `sta->uploaded` false in `__sta_info_destroy()` and `__sta_info_flush()`:
  neither `sta_pre_rcu_remove` nor the step to `IEEE80211_STA_NOTEXIST` is
  called.
- Driver with `sta_remove`: its last state callback is on
  `IEEE80211_STA_ASSOC` to `IEEE80211_STA_AUTH`, also after the grace period;
  nothing is called on the step to `IEEE80211_STA_NOTEXIST`.
- Free: `cleanup_single_sta()` calls `sta_info_free()`, which calls `kfree()`
  directly; no RCU delay follows the last transition.
- Failed insertion in `sta_info_insert_finish()`: the driver sees the unwind
  down to `IEEE80211_STA_NOTEXIST` while the station is still hashed;
  `sta_pre_rcu_remove` is not called; `synchronize_net()` runs after the
  unwind and before the free.
- **Potentially unsafe usage**: clearing a driver's RCU-published station
  pointer in the last `sta_state` or `sta_remove` call.
  - Unsafe: on the path through `__sta_info_destroy_part2()` when the pointer
    was still published until that call and the driver returns without its
    own grace period; `sta_info_free()` frees the station while driver
    readers may still dereference it.
  - Safe: clear it in `sta_pre_rcu_remove`, as `mt76_sta_pre_rcu_remove()`
    does; the `synchronize_net()` in `__sta_info_destroy()` or
    `__sta_info_flush()` follows. This covers only the removal of a station
    with `sta->uploaded` set.
