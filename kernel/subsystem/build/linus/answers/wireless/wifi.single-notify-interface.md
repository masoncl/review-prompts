- `ieee80211_bss_info_change_notify()`: has `might_sleep()` only; it does not
  call `lockdep_assert_wiphy()`, and it bypasses the `drv_` wrappers that do.
- MLD interface: `WARN_ON_ONCE(ieee80211_vif_is_mld(&sdata->vif))` does not
  return; the call goes on, and the only link conf it passes is
  `&sdata->vif.bss_conf`.
- `NL80211_IFTYPE_P2P_DEVICE` or `NL80211_IFTYPE_NAN`: `WARN_ON_ONCE`, whole
  call dropped.
- `NL80211_IFTYPE_MONITOR`: `WARN_ON_ONCE` and drop when `changed` has any flag
  other than `BSS_CHANGED_TXPOWER`; the function has no `mu_mimo_owner` test.
- `BSS_CHANGED_BEACON` or `BSS_CHANGED_BEACON_ENABLED`: `WARN_ON_ONCE` and drop
  unless the type is `NL80211_IFTYPE_AP`, `NL80211_IFTYPE_ADHOC`,
  `NL80211_IFTYPE_MESH_POINT` or `NL80211_IFTYPE_OCB`.
- Interface not in the driver: the flag tested is `IEEE80211_SDATA_IN_DRIVER`,
  by `check_sdata_in_driver()`.
- **Potentially unsafe usage**: calling `ieee80211_bss_info_change_notify()` on
  an interface that can be an MLD.
  - Unsafe: when nothing before the call rules out `ieee80211_vif_is_mld()`;
    the `WARN_ON_ONCE` in the function fires and the only link conf the driver
    is handed is `&sdata->vif.bss_conf`.
  - Safe: in the non-MLD branch of an `ieee80211_vif_is_mld()` test, with
    `ieee80211_link_info_change_notify()` per link plus
    `ieee80211_vif_cfg_change_notify()` on the MLD branch, as
    `ieee80211_set_associated()` in `net/mac80211/mlme.c` does; the
    `WARN_ON_ONCE` in the function defines the requirement.
