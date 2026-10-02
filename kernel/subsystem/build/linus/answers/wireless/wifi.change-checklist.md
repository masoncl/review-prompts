- Signature mismatch in a built driver: a build error, not a warning;
  `scripts/Makefile.warn` sets `-Werror=incompatible-pointer-types`
  unconditionally.
- cfg80211 op checks live in two places: `wiphy_new_nm()` checks op pairs
  with `WARN_ON()` and continues; `wiphy_register()` checks ops against
  advertised features and interface modes and returns `-EINVAL`.
- mac80211 op checks: `ieee80211_alloc_hw_nm()` in `net/mac80211/main.c`
  returns `NULL` on a missing mandatory or inconsistent op;
  `ieee80211_register_hw()` has further checks against hw flags.
- All of these checks fire at runtime; none fails the build.
- Direct calls: in net/wireless every call through `rdev->ops` is in
  `net/wireless/rdev-ops.h`; in mac80211 some calls bypass the `drv_`
  wrappers, in `net/mac80211/cfg.c` (for example `testmode_cmd`,
  `set_sar_specs`) and in `ieee80211_bss_info_change_notify()` in
  `net/mac80211/main.c`; search for `local->ops->`.
- `mac80211_config_ops` in `net/mac80211/cfg.c`: one table shared by every
  mac80211 driver, so a cfg80211 test of `rdev->ops->x`, such as the
  `CMD()` macro in `net/wireless/nl80211.c`, is true for all of them; the
  mac80211 implementation has to return `-EOPNOTSUPP` itself when the
  driver lacks the `struct ieee80211_ops` callback.
