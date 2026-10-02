- `genpd_sync_power_off()`: does not read `genpd->stay_on`; a domain still
  under boot protection is powered off at system suspend like any other.
- `GENPD_FLAG_ALWAYS_ON`: the only keep-on setting that
  `genpd_sync_power_off()` honours.
- `stay_on` domain with no devices attached: reached as the parent of a
  subdomain that powers off, and passes the count test as 0 == 0.
- `genpd_power_off_unused()`: does not clear `stay_on`; it only queues
  `power_off_work`, and `genpd_power_off()` then returns for a `stay_on`
  domain.
