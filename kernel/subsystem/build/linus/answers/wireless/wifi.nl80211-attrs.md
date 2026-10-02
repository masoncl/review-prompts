- Missing policy entry: an attribute sent by userspace is rejected by
  `validate_nla()` with `-EINVAL` ("Unsupported attribute") before a `.doit`
  handler runs; it is never accepted unvalidated, since every new number is
  above the strict start.
- Attributes only sent by the kernel: need no entry (for example
  `NL80211_ATTR_WIPHY_RADIOS`, `NL80211_ATTR_TX_HW_TIMESTAMP`); some carry
  `{ .type = NLA_REJECT }`, as `NL80211_ATTR_RECONNECT_REQUESTED` does.
- `NL80211_ATTR_MLO_LINK_ID` policy:
  `NLA_POLICY_RANGE(NLA_U8, 0, IEEE80211_MLD_MAX_NUM_LINKS - 1)`; it bounds the
  index into `wdev->links[]`, not whether the link exists.
- `nl80211_link_id()`: returns 0 when the attribute is absent, for handlers
  that index `wdev->links[]`, for example `nl80211_color_change()`.
- `nl80211_link_id_or_invalid()`: returns -1 when the attribute is absent, for
  handlers where the link id is optional.
- Per-link ids inside `NL80211_ATTR_MLO_LINKS`: `nl80211_process_links()`
  parses each link with no policy; the bound comes from the entry
  `NLA_POLICY_NESTED_ARRAY(nl80211_policy)`.
- **Potentially unsafe usage**: using the link id in an op without
  `NL80211_FLAG_MLO_VALID_LINK_ID`.
  - Unsafe: when the handler treats the link as existing and nothing has
    tested `wdev->valid_links`; on an MLD `nl80211_link_id()` returns 0 for an
    absent attribute.
  - Safe: the handler tests `wdev->valid_links & BIT(link_id)` itself and
    rejects an id on a non-MLD, as `nl80211_del_station()` does.
  - Safe: the handler calls `nl80211_validate_key_link_id()` before the op, as
    `nl80211_new_key()` does; it makes the same `wdev->valid_links` tests for
    a group key and rejects any link id for a pairwise key.
