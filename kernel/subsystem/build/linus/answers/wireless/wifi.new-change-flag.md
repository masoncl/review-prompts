- Per-link flag on `NL80211_IFTYPE_NAN` or `NL80211_IFTYPE_P2P_DEVICE`:
  `drv_link_info_changed()` and `ieee80211_bss_info_change_notify()` warn and
  drop it; only `drv_vif_cfg_changed()`, called directly or through
  `ieee80211_vif_cfg_change_notify()`, reaches such an interface.
- `ieee80211_reconfig()` in `net/mac80211/util.c`: builds the set of flags
  replayed after a restart by hand, partly in its helpers
  `ieee80211_reconfig_ap_links()` and `ieee80211_reconfig_nan()`; it does not
  replay a flag that is not added there.
