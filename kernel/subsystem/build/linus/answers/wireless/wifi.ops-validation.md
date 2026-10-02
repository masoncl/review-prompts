- `config`: required, in the same `WARN_ON()` as the other seven callbacks.
- Channel context callbacks all NULL: rejected. Only two shapes pass:

| Shape | `add_chanctx`, `remove_chanctx`, `change_chanctx` | `assign_vif_chanctx`, `unassign_vif_chanctx` |
|---|---|---|
| emulation | exactly the three `ieee80211_emulate_add_chanctx()`, `ieee80211_emulate_remove_chanctx()`, `ieee80211_emulate_change_chanctx()` | both NULL |
| driver-managed | all non-NULL, none of them an emulation helper | both non-NULL |

- `switch_vif_chanctx`: not looked at by `ieee80211_alloc_hw_nm()` in either
  shape.
- `ampdu_action`: tested by neither `ieee80211_alloc_hw_nm()` nor
  `ieee80211_register_hw()`; `net/mac80211/agg-tx.c` tests it at run time.
