- Kerneldoc above `struct ieee80211_ops`: states "must be atomic" or "can
  sleep" for many callbacks, but not all; for example `wake_tx_queue`,
  `get_txpower` and `net_setup_tc` state nothing.
- The kerneldoc has no general rule about the wiphy mutex; it names the
  mutex for two callbacks only, `get_et_sset_count` and `get_et_strings`,
  both "not held".
- The wrapper is where the context shows: a `drv_` wrapper that starts with
  `might_sleep()` and `lockdep_assert_wiphy()` is a sleeping callback under
  the mutex.
- `drv_configure_filter()`, `drv_get_tsf()` and `drv_sta_pre_rcu_remove()`:
  all sleep and assert the wiphy mutex.
- Wrappers that sleep without asserting the mutex: for example
  `drv_net_setup_tc()`, `drv_can_neg_ttlm()` and `drv_vif_add_debugfs()`
  call `might_sleep()` only.
- `drv_tx()`: calls the driver with no check and no tracepoint.
- `check_sdata_in_driver()` result is ignored by some wrappers, for example
  `drv_start_nan()`; they warn and call the driver anyway.
- There is no sdata_assert_lock here; wrappers use `lockdep_assert_wiphy()`.
- `for_each_interface()`, `for_each_active_interface()`,
  `for_each_station()` in `include/net/mac80211.h`: require the wiphy
  mutex; the assertion is in `__ieee80211_iterate_interfaces()` and
  `__ieee80211_iterate_stations()`, which
  `ieee80211_iterate_active_interfaces_mtx()` and
  `ieee80211_iterate_stations_mtx()` also use.
- **Potentially unsafe usage**: `ieee80211_iterate_interfaces()` or
  `ieee80211_iterate_active_interfaces()` from driver code.
  - Unsafe: in a callback that mac80211 makes with `iflist_mtx` held;
    `ieee80211_del_virtual_monitor()` holds it across
    `ieee80211_link_release_channel()` and `drv_remove_interface()`, so the
    iterator deadlocks on `iflist_mtx`.
  - Safe: from a context that holds no mac80211 lock, as the plain work
    handler `rt2x00lib_intf_scheduled()` does.
  - Safe: under the wiphy mutex use
    `ieee80211_iterate_active_interfaces_mtx()` or
    `for_each_active_interface()`; `__ieee80211_iterate_interfaces()` takes
    no lock.
