- `rcu_dereference_wiphy()`: `rcu_dereference_check()` on `wiphy->mtx`, for
  code reached both under `rcu_read_lock()` and under the mutex; defined in
  `include/net/cfg80211.h`.
- `rcu_dereference_wiphy()` kerneldoc says "or RTNL"; the macro tests only
  `wiphy->mtx`, so holding the RTNL alone trips the check.
- mac80211 forms: `sdata_dereference()` in `net/mac80211/ieee80211_i.h`;
  `link_conf_dereference_protected()`, `link_conf_dereference_check()`,
  `link_sta_dereference_protected()`, `link_sta_dereference_check()` in
  `include/net/mac80211.h`, usable from drivers.
- `lockdep_sta_mutex_held()`: an inline that returns `true` without
  `CONFIG_LOCKDEP`; with it, tests the wiphy mutex of the station's `local`.
- `rcu_dereference_protected_tid_tx()` in `net/mac80211/sta_info.h`: accepts
  `sta->lock` or the wiphy mutex.
- net/wireless often writes the assertion as
  `lockdep_assert_held(&rdev->wiphy.mtx)` instead of
  `lockdep_assert_wiphy()`; both mean the same.
