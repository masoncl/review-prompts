- `ieee80211_restart_hw()`: flushes nothing and cancels nothing. Flushing
  `local->workqueue` and `ieee80211_scan_cancel()` happen in
  `ieee80211_restart_work()` in `net/mac80211/main.c`.
- `ieee80211_restart_work()` before `ieee80211_reconfig()`: also flushes all
  wiphy work, cancels `csa_connection_drop_work` and drops the connection of a
  station with `csa_active`, flushes `dec_tailroom_needed_wk` and the ROC
  work, and calls `synchronize_net()`.
- `ieee80211_reconfig()` order, for a restart:
  1. `drv_start()`.
  2. `drv_set_frag_threshold()`, `drv_set_rts_threshold()` (once per radio
     when `n_radio` is nonzero), `drv_set_coverage_class()`.
  3. `drv_add_interface()`: the virtual monitor vif (only with
     `IEEE80211_HW_WANT_MONITOR_VIF`), then each running interface.
  4. `drv_add_chanctx()` for each context not in state
     `IEEE80211_CHANCTX_REPLACES_OTHER`.
  5. `ieee80211_hw_config()`, then `ieee80211_configure_filter()`.
  6. Per running interface: `drv_change_vif_links()` (MLD only), chanctx
     assignment per active link, `drv_join_ibss()`, stations (not for
     `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_AP_VLAN`,
     `NL80211_IFTYPE_MONITOR`, `NL80211_IFTYPE_NAN` and
     `NL80211_IFTYPE_NAN_DATA` interfaces), `drv_conf_tx()` (not for
     `NL80211_IFTYPE_AP_VLAN`, `NL80211_IFTYPE_MONITOR`,
     `NL80211_IFTYPE_NAN` and `NL80211_IFTYPE_NAN_DATA` interfaces), then by
     type: the vif and link change notifications; for `NL80211_IFTYPE_AP`
     `drv_start_ap()` before the notification that carries the beacon flags;
     for `NL80211_IFTYPE_NAN` `ieee80211_reconfig_nan()`.
  7. `ieee80211_recalc_ps()`.
  8. Stations of `NL80211_IFTYPE_AP` and `NL80211_IFTYPE_AP_VLAN`
     interfaces.
  9. Keys, with `ieee80211_reenable_keys()`.
  10. Remaining MLD links, with `ieee80211_set_active_links()`.
  11. Scheduled scan restart.
  12. BA sessions torn down with `ieee80211_sta_tear_down_BA_sessions()`;
      they are not restored.
  13. `drv_reconfig_complete()`.
  14. `local->in_reconfig` cleared, `ieee80211_reconfig_roc()` called,
      interface work requeued.
  15. Queues woken.
  16. `ieee80211_sta_restart()` for station interfaces.
- Step 3 skips: `NL80211_IFTYPE_AP_VLAN`, `NL80211_IFTYPE_NAN_DATA` (added
  later by `ieee80211_reconfig_nan()`), and monitor interfaces unless
  `IEEE80211_HW_NO_VIRTUAL_MONITOR` is set.
- Channel of an emulating driver: restored in step 4, not step 5.
  `ieee80211_hw_config()` warns on `IEEE80211_CONF_CHANGE_CHANNEL`;
  `local->in_reconfig` forces that flag in `ieee80211_calc_hw_conf_chan()`.
- `reconfig_complete` op on a restart: runs while `local->in_reconfig` is
  still true and the queues are still stopped.
- `local->open_count` of 0: `ieee80211_reconfig()` jumps to `wake_up`;
  neither `drv_start()` nor `drv_reconfig_complete()` is called.
