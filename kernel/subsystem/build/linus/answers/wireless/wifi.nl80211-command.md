- `nl80211_ops` (`struct genl_ops`): holds two commands,
  `NL80211_CMD_GET_WIPHY` and `NL80211_CMD_GET_STATION`, both with `.done`;
  every other command is in `nl80211_small_ops` (`struct genl_small_ops`).
- `.internal_flags`: a `u8` index of `enum nl80211_internal_flags_selector`
  into `nl80211_internal_flags[]`, not the flag bitmask;
  `NL80211_FLAG_MLO_UNSUPPORTED` is 0x100.
- `IFLAGS()`: matches the OR of the flags against each `SELECTOR()` value by
  equality, so a combination must match one line exactly.
- New combination: add one `SELECTOR()` line to `INTERNAL_FLAG_SELECTORS()` in
  `net/wireless/nl80211.c`; the enum and `nl80211_internal_flags[]` are
  generated from it, and `nl80211_pre_doit()` needs no change.
- Missing `SELECTOR()` line: the entry's static initializer becomes a call to
  `__missing_selector()`, which is declared but defined nowhere, so the build
  fails.
- Entry with no `.internal_flags`: no lookup, both `info->user_ptr[]` NULL, no
  wiphy mutex; the handler looks up and locks itself, as `nl80211_set_wiphy()`
  does.
- `info->user_ptr[1]`: `struct net_device *` with `NL80211_FLAG_NEED_NETDEV`,
  `struct wireless_dev *` with `NL80211_FLAG_NEED_WDEV`, NULL with
  `NL80211_FLAG_NEED_WIPHY`.
- P2P device and NAN: no flag variants; `NL80211_FLAG_CHECK_NETDEV_UP` calls
  `wdev_running()`, which tests `wdev->is_running` when there is no netdev.
- `NL80211_FLAG_MLO_VALID_LINK_ID`: on an MLD `NL80211_ATTR_MLO_LINK_ID` must
  be present and in `wdev->valid_links`; on a non-MLD its presence gives
  `-EINVAL`.
- `nl80211_pre_doit()` failure: `genl_family_rcv_msg_doit()` skips the handler
  and `nl80211_post_doit()`, so `nl80211_pre_doit()` must undo its own locks
  and reference on every error path.
- `.dumpit`: `genl_family_rcv_msg_dumpit()` calls neither hook, so
  `.internal_flags` covers `.doit` only; see `nl80211_prepare_wdev_dump()`.
- **Unsafe usage**: a `NL80211_FLAG_NEED_WDEV` handler frees a wdev that has
  no netdev and leaves `info->user_ptr[1]` set.
  - Unsafe: `nl80211_post_doit()` reads `wdev->netdev` from the freed wdev.
  - Safe: set `info->user_ptr[1] = NULL` before the free, as
    `nl80211_del_interface()` does.
