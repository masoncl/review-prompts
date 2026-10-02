- `__cfg80211_get_bss()` and the inline `cfg80211_get_ibss()`: also return a
  referenced entry, or NULL.
- Functions that consume the caller's reference on every path, so the caller
  must not put again: `cfg80211_connect_done()` and `cfg80211_roamed()`, for
  each `links[].bss` passed in.
- `cfg80211_rx_assoc_resp()` and `cfg80211_assoc_failure()`: consume the
  reference and the hold that `cfg80211_mlme_assoc()` took when the `assoc`
  op succeeded; on a successful association
  `__cfg80211_connect_result()` keeps both for `current_bss`.
- `cfg80211_unlink_bss()`: drops the scan list's own reference through
  `__cfg80211_unlink_bss()`, not the caller's. It also unlinks every entry on
  the `nontrans_list` of the entry.
- A reference keeps the memory, not the place in the list. `hold` in
  `struct cfg80211_internal_bss`, not `refcount`, stops
  `__cfg80211_bss_expire()` and `cfg80211_bss_expire_oldest()`; see
  `cfg80211_hold_bss()` in `net/wireless/core.h`.
- An unlinked entry has `list_empty()` true on its `list`;
  `cfg80211_update_link_bss()` in `net/wireless/sme.c` handles that case.
- `ieee80211_bss_get_elem()` in `net/wireless/util.c`: takes no lock itself.
  It calls `rcu_dereference(bss->ies)`, so the caller holds `rcu_read_lock()`
  across the call and every use of the result.
- **Unsafe usage**: reading `ies`, `beacon_ies` or `proberesp_ies` of an
  entry under `wiphy->mtx` alone, for example with `wiphy_dereference()`.
  `cfg80211_update_known_bss()` replaces them and calls `kfree_rcu()` under
  `rdev->bss_lock` only, and mac80211 reaches it from `ieee80211_scan_rx()` in
  the RX path.
  - Safe: `rcu_read_lock()`, `rcu_dereference()`, copy out, unlock, as
    `ieee80211_mgd_assoc()` does for the SSID.
  - Safe: inside `net/wireless/scan.c` with `rdev->bss_lock` held and
    `rcu_access_pointer()`, as `is_bss()` does when called from
    `__cfg80211_get_bss()`.
- `beacon_ies` and `proberesp_ies`: either can be NULL. `ies` is non-NULL on
  an inserted entry; `__cfg80211_bss_update()` rejects a NULL one.
- `cfg80211_bss_iter()`: calls the callback under
  `spin_lock_bh(&rdev->bss_lock)`. The callback must not sleep and must not
  call `cfg80211_ref_bss()`, `cfg80211_put_bss()` or the get and inform
  functions, which take the same lock.
- A `cfg80211_bss_iter()` callback still takes `rcu_read_lock()` before
  `rcu_dereference(bss->ies)`, as
  `iwl_mvm_check_he_obss_narrow_bw_ru_iter()` does.
- `inform_bss` op in `struct cfg80211_ops`: `rdev_inform_bss()` calls it
  inside the `bss_lock` section of `cfg80211_inform_single_bss_data()`, so the
  same limits apply as for a `cfg80211_bss_iter()` callback. mac80211's
  `ieee80211_inform_bss()` is the only implementation outside the kunit test
  `net/wireless/tests/scan.c`.
