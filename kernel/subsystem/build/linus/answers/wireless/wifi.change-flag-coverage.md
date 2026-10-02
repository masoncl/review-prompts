- `BSS_CHANGED_NAN_LOCAL_SCHED`: not in `BSS_CHANGED_VIF_CFG_FLAGS`, yet
  delivered to `vif_cfg_changed`.
- Delivery of `BSS_CHANGED_NAN_LOCAL_SCHED`: by direct `drv_vif_cfg_changed()`
  calls in `net/mac80211/nan.c` and in `ieee80211_reconfig_nan()` in
  `net/mac80211/util.c`, which skip `ieee80211_vif_cfg_change_notify()` and its
  `WARN_ON_ONCE`.
- `BSS_CHANGED_NAN_LOCAL_SCHED` passed to `ieee80211_vif_cfg_change_notify()`:
  would warn; passed to `ieee80211_bss_info_change_notify()` on an
  `NL80211_IFTYPE_NAN` interface: warns and is dropped.
- `drv_link_info_changed()`: every check returns, so the whole call is dropped,
  not single flags.

| Condition in `drv_link_info_changed()` | Warns |
|---|---|
| `BSS_CHANGED_BEACON` or `BSS_CHANGED_BEACON_ENABLED` on a type other than `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_ADHOC`, `NL80211_IFTYPE_MESH_POINT`, `NL80211_IFTYPE_OCB` | `WARN_ON_ONCE` |
| `NL80211_IFTYPE_P2P_DEVICE` or `NL80211_IFTYPE_NAN`, any flag | `WARN_ON_ONCE` |
| `NL80211_IFTYPE_MONITOR` with any flag other than `BSS_CHANGED_TXPOWER` and `BSS_CHANGED_MU_GROUPS` | `WARN_ON_ONCE` |
| `BSS_CHANGED_MU_GROUPS` while `sdata->vif.bss_conf.mu_mimo_owner` is false, any type | `WARN_ON_ONCE` |
| interface without `IEEE80211_SDATA_IN_DRIVER` (`check_sdata_in_driver()`) | `WARN_ONCE`, unless `local->reconfig_failure` is set |
| link for which `ieee80211_vif_link_active()` is false | silent |

- `BSS_CHANGED_MU_GROUPS` check: reads `sdata->vif.bss_conf`, not the `info`
  argument.
- `ieee80211_vif_link_active()`: on a non-MLD interface true only for link 0;
  on an MLD it tests `vif->active_links`.
- `drv_link_info_changed()`: has no test that names `NL80211_IFTYPE_AP_VLAN`,
  `NL80211_IFTYPE_NAN_DATA` or `NL80211_IFTYPE_PD`; of its checks only the
  beacon-flag one drops a call for these types.
- `ieee80211_link_info_change_notify()`: returns silently, before the wrapper,
  for `NL80211_IFTYPE_AP_VLAN`, and for `NL80211_IFTYPE_MONITOR` unless the
  hardware has `IEEE80211_HW_WANT_MONITOR_VIF`.
- Direct `drv_link_info_changed()` callers skip that pre-filter; for example
  `ieee80211_chanctx_update_npca_links()` in `net/mac80211/chan.c` sends
  `BSS_CHANGED_NPCA` this way.
