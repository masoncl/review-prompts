- `ieee80211_find_available_radio()` in `net/mac80211/chan.c` picks the radio;
  it returns the first index, in ascending order, that passes all its tests.
- `radio_mask`: the easy part to miss. A radio is skipped unless its bit is
  set in the `sdata->wdev.radio_mask` of the interface that asks for the
  context.
- `radio_idx` of -1: not proof of a wiphy without radios.
  `ieee80211_alloc_chanctx()` is the only writer, and
  `ieee80211_replace_chanctx()` calls it with a literal -1.
- Readers of `radio_idx` in mac80211 test it for `>= 0` before using it as an
  index or bit number, for example `ieee80211_replace_chanctx()` and
  `__ieee80211_get_radio_mask()` in `net/mac80211/util.c`.
