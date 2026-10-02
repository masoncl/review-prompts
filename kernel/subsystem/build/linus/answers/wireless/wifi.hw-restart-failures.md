- Failures that end the reconfiguration: `drv_start()`, and
  `drv_add_interface()` in the loop over `local->interfaces`. Both call
  `ieee80211_handle_reconfig_failure()` and return the error.
- `drv_resume()` returning negative (reached only with `local->wowlan`, under
  `CONFIG_PM`): also ends the reconfiguration and returns the error, without
  `ieee80211_handle_reconfig_failure()`.
- A fatal return skips `drv_reconfig_complete()`; the `reconfig_complete` op
  is not called.
- Queues on a `drv_start()` failure: woken by `ieee80211_reconfig()` itself,
  before `ieee80211_handle_reconfig_failure()`, which does not clear
  `IEEE80211_QUEUE_STOP_REASON_SUSPEND`.
- Other callback failures do not end the reconfiguration:

| Call | On failure |
|---|---|
| `drv_add_chanctx()`, `drv_join_ibss()`, `drv_sta_state()` in `ieee80211_reconfig_stations()` | `WARN_ON()`, continue |
| `ieee80211_reconfig_nan()` | `WARN_ON()`, continue; the rest of the NAN restore is skipped |
| `drv_assign_vif_chanctx()`, `drv_change_vif_links()`, `drv_conf_tx()`, `drv_start_ap()`, `ieee80211_hw_config()` | return value dropped, no warning |
| key upload in `ieee80211_reenable_keys()` | return value dropped; `ieee80211_key_enable_hw_accel()` logs with `sdata_err()` unless the error is `-ENOSPC` or `-EOPNOTSUPP` |
| scheduled scan restart | scan reported stopped with `cfg80211_sched_scan_stopped_locked()` |

- `ieee80211_reconfig_disconnect()`: never called by `ieee80211_reconfig()` on
  a failure. Only a driver reaches it, through
  `ieee80211_hw_restart_disconnect()` or `ieee80211_resume_disconnect()`.
- The flag set that way is acted on at the very end, by
  `ieee80211_sta_restart()` in `net/mac80211/mlme.c`.
