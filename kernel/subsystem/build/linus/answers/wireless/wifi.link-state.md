- `for_each_vif_active_link()`: needs `rcu_read_lock()` or the wiphy mutex,
  either one; it reads slots with `link_conf_dereference_check()`.
  `iwl_mvm_update_smps_on_active_links()` takes `rcu_read_lock()` around it,
  `ieee80211_stop_mbssid()` runs it under the mutex.
- `for_each_valid_link()` in `include/net/cfg80211.h`: walks link IDs of a
  `valid_links` bitmap only; dereferences no RCU pointer and checks no lock.
- `link_conf[id]`: non-NULL for every valid link, inactive and dormant ones
  too; the filter on `active_links` is in the iterator, not in the array.
- `dormant_links`: valid links that cannot be activated;
  `_ieee80211_set_active_links()` returns `-EINVAL` on a running interface
  for a link outside `ieee80211_vif_usable_links()`.
- `suspended_links`: the part of `dormant_links` caused by negotiated TTLM;
  written in `ieee80211_ttlm_set_links()` and cleared in
  `ieee80211_process_ttlm_teardown()`.
- AP and AP_VLAN: `ieee80211_set_vif_links_bitmaps()` sets `active_links` to
  `valid_links` and warns on any dormant link;
  `_ieee80211_set_active_links()` returns `-EINVAL` on a running interface
  unless the type is `NL80211_IFTYPE_STATION`.
- **Potentially unsafe usage**: a driver publishing
  `struct ieee80211_bss_conf` pointers to its own RCU readers.
  - Unsafe: when a link is removed and `change_vif_links` returns with
    readers still running; `ieee80211_free_links()` calls `kfree()` on the
    link after `drv_change_vif_links()` with no grace period guaranteed in
    between, and the `synchronize_rcu()` in `ieee80211_tear_down_links()` ran
    before the callback.
  - Safe: unpublish and call `synchronize_rcu()` before returning, as
    `rtw89_ops_change_vif_links()` does.
