- **Potentially unsafe usage**: passing a length computed by subtraction to
  `for_each_element()` or `cfg80211_find_elem()`.
  - Unsafe: when nothing earlier checked that the frame is at least as long as
    its fixed part. `for_each_element()` trusts `_datalen`, and a negative
    `int len` of `cfg80211_find_elem()` becomes a large `unsigned int` in
    `cfg80211_find_elem_match()`, so the walk runs past the buffer.
  - Safe: after a length check, as `cfg80211_inform_bss_frame_data()` does
    with `len < min_hdr_len` before it computes `ielen`.
- **Potentially unsafe usage**: copying `elem->datalen` (or `elems->ssid_len`)
  bytes into a fixed-size buffer.
  - Unsafe: when the length was not bounded; it is the raw length byte, up to
    255, for example an SSID longer than `IEEE80211_MAX_SSID_LEN`.
  - Safe: bound it first, as `__cfg80211_connect_result()` does with `min()`
    and `ieee80211_mgd_assoc()` does by rejecting
    `datalen > sizeof(assoc_data->ssid)`.
- `for_each_element_completed()`: returns false after any `break` out of the
  loop, not only for a malformed tail.
- Extension elements: `data[0]` is the extension ID, so size helpers such as
  `ieee80211_he_capa_size_ok()` take `data + 1` and `datalen - 1`; a
  `sizeof()` test on `datalen` needs `+ 1`, unless a test of `datalen`
  against `ieee80211_he_oper_size()` follows, which counts the extension ID
  byte, as in `cfg80211_get_ies_channel_number()`.
- Size helpers such as `ieee80211_he_capa_size_ok()` and
  `ieee80211_mle_size_ok()`: defined in the split headers
  `include/linux/ieee80211-he.h`, `include/linux/ieee80211-eht.h`,
  `include/linux/ieee80211-uhr.h` and `include/linux/ieee80211-mesh.h`.
- `cfg80211_find_vendor_elem()`: a non-NULL result has `datalen >= 4`, also
  when `oui_type` is negative.
- Fragmented elements: `for_each_element()` yields each `WLAN_EID_FRAGMENT`
  as its own element; `cfg80211_defragment_element()` joins them.
- There is no ieee802_11_parse_elems_crc() here; the only wrapper is
  `ieee802_11_parse_elems()` in `net/mac80211/ieee80211_i.h`. CRC input is
  `filter` and `crc` in `struct ieee80211_elems_parse_params`, the result is
  `elems->crc`.
- `ieee802_11_parse_elems_full()` returns NULL also when
  `params->link_id >= 0` and `params->bss` are both set, after a `WARN_ON()`.
- `link_id` in the params: must be -1 when no per-link parse is wanted. A
  zeroed field asks for the per-STA profile of link 0.
- `params->mode`: elements of a newer generation than the mode are not stored,
  and no error bit is set. A zeroed `mode` is `IEEE80211_CONN_MODE_S1G`.
- S1G members (`s1g_capab`, `s1g_oper`, `s1g_bcn_compat`, `aid_resp`): stored
  only when `mode` is exactly `IEEE80211_CONN_MODE_S1G`, so never through
  `ieee802_11_parse_elems()`, which passes `IEEE80211_CONN_MODE_HIGHEST`.
- `elems->parse_error`: a `u8` bitmask of
  `enum ieee80211_elems_parse_error`.
- `parse_error == 0` does not mean every element was well formed:
  `ieee80211_parse_extension_element()` drops a wrong-sized extension element
  without setting `IEEE80211_PARSE_ERR_BAD_ELEM_SIZE`.
- Duplicates: for the IDs in the first `switch` of
  `_ieee802_11_parse_elems_full()` the first good occurrence wins and
  `IEEE80211_PARSE_ERR_DUP_ELEM` is set. For other IDs, including extension
  elements, a later occurrence overwrites the pointer. Exceptions:
  `WLAN_EID_EXT_TID_TO_LINK_MAPPING` is appended to `ttlm[]`, and with
  `params->bss` NULL `elems->ml_basic` is the first basic multi-link element,
  found by `ieee80211_prep_mle_link_parse()`.
