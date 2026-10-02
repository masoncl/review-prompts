- `genpd_power_off()` in `drivers/pmdomain/core.c`: is `void`; with `stay_on`
  set it returns silently, there is no error code for a caller to see.
- `genpd_set_stay_on()`: sets `stay_on` to `!is_off` only under
  `CONFIG_PM_GENERIC_DOMAINS_OF` and without `GENPD_FLAG_NO_STAY_ON`;
  otherwise `stay_on` is false.
- `GENPD_FLAG_NO_STAY_ON` and `GENPD_FLAG_NO_SYNC_STATE`: both exist, in
  `include/linux/pm_domain.h`.
- `GENPD_FLAG_NO_STAY_ON`: read once, in `pm_genpd_init()`; setting it
  after that call has no effect.
- Clearing sites: `of_genpd_sync_state()` and the `GENPD_SYNC_STATE_SIMPLE`
  case of `genpd_provider_sync_state()`; after `pm_genpd_init()` no other
  code writes `stay_on`.
- Both clearing sites call `genpd_power_off()` directly under the genpd
  lock; they do not call `genpd_queue_power_off_work()`.
- A domain registered on and never passed to
  `of_genpd_add_provider_simple()` or `of_genpd_add_provider_onecell()`:
  `stay_on` is still set by `pm_genpd_init()`, and nothing clears it.
