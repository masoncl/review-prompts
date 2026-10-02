- `sta_info_get()`, `sta_info_get_bss()` and `ieee80211_find_sta()`: take and
  drop `rcu_read_lock()` internally and check nothing about the caller, so
  lockdep stays silent for a caller that holds neither RCU nor the wiphy
  mutex.
- Among the station lookups, lockdep accepts the wiphy mutex only in list
  walks, for example `sta_info_get_by_idx()` and `__iterate_stations()` in
  `net/mac80211/util.c`.
- `ieee80211_find_sta_by_ifaddr()` and `ieee80211_find_sta_by_link_addrs()`:
  take no `rcu_read_lock()` themselves and walk the rhashtable, so the caller
  needs `rcu_read_lock()` even under the wiphy mutex, as
  `sta_info_insert_check()` does.
- `ieee80211_find_sta()` and `ieee80211_find_sta_by_ifaddr()`: return NULL
  for a station whose `sta->uploaded` is false, although mac80211 has it.
- ath9k TX completion: the `ieee80211_find_sta_by_ifaddr()` call is in
  `ath_tx_process_buffer()`, which passes the result to
  `ath_tx_complete_aggr()`.
