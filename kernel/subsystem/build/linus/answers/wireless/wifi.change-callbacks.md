- Wrong-kind flag in `ieee80211_vif_cfg_change_notify()` or
  `ieee80211_link_info_change_notify()`: `WARN_ON_ONCE()` only; the function
  neither masks nor returns on it, and passes the full `changed` on to the
  `drv_` wrapper.
- `drv_vif_cfg_changed()`: static inline in `net/mac80211/driver-ops.h`;
  `drv_link_info_changed()` is in `net/mac80211/driver-ops.c`.
