- `iflist_mtx`: the only other sleeping lock in `struct ieee80211_local`; it
  is the only `struct mutex` declared in `net/mac80211/ieee80211_i.h`.
- key_mtx, sta_mtx and chanctx_mtx: exist nowhere in this tree; keys,
  stations and channel contexts are under the wiphy mutex.
- `struct ieee80211_local` has no member named `sta_lock`; the spinlock next
  to the station list is `tim_lock`.
- Comments in `net/mac80211/ieee80211_i.h` that say "RTNL and local->mtx"
  are stale; `struct ieee80211_local` has no `mtx` member.
- `iflist_mtx` nests inside the wiphy mutex: order is RTNL, wiphy mutex,
  `iflist_mtx`; see `ieee80211_if_add()` in `net/mac80211/iface.c`.
- `iflist_mtx` covers writes to `local->interfaces`, and the writes to
  `local->monitor_sdata` in `net/mac80211/iface.c`; `__iterate_interfaces()`
  in `net/mac80211/util.c` accepts `iflist_mtx` or the wiphy mutex for
  reading.
- Scoped locking: `DEFINE_GUARD(wiphy, ...)` in `include/net/cfg80211.h`;
  code writes `guard(wiphy)(wiphy)` or `scoped_guard(wiphy, wiphy)`, so a
  search for `wiphy_lock()` alone misses lock sites, for example
  `cfg80211_wiphy_work()` and `cfg80211_netdev_notifier_call()`.
