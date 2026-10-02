| Governor | `power_down_ok` (runtime) | `system_power_down_ok` |
|---|---|---|
| `simple_qos_governor` | `default_power_down_ok()` | not set |
| `pm_domain_always_on_gov` | not set | not set |
| `pm_domain_cpu_gov` | `cpu_power_down_ok()` | `cpu_system_power_down_ok()` |

- `pm_domain_always_on_gov`: there is no always_on_power_down_ok() or
  always-on callback here; the governor holds only `.suspend_ok`.
- `suspend_ok`: a per-device runtime-suspend check, called only from
  `genpd_runtime_suspend()`; it is not consulted at system suspend.
- `genpd_sync_power_off()`: calls `system_power_down_ok` when the governor has
  one, and leaves the domain on if it returns false.
- Governor without `system_power_down_ok`, or no governor: system suspend uses
  `genpd->state_count - 1`.
- `cpu_system_power_down_ok()` on a domain without `GENPD_FLAG_CPU_DOMAIN`:
  picks the deepest state and returns true.
- `cpu_system_power_down_ok()` on a CPU domain: picks the deepest state whose
  `power_off_latency_ns + power_on_latency_ns` fits
  `cpu_wakeup_latency_qos_limit()`; returns false if none fits.
- `cpu_power_down_ok()`: does not call `tick_nohz_get_next_hrtimer()`; it reads
  `next_hrtimer` of the `struct cpuidle_device` of each online CPU in
  `genpd->cpus`.
- `cpu_power_down_ok()` latency bound: the minimum of `cpu_latency_qos_limit()`,
  `cpu_wakeup_latency_qos_limit()` and the `dev_pm_qos_raw_resume_latency()`
  of each of those CPUs.
- `cpu_power_down_ok()`: returns false when `cpus_peek_for_pending_ipi()` is
  true for `genpd->cpus`, even if a state fits.
- `default_power_down_ok()`: weighs `residency_ns` only when the domain has
  `GENPD_FLAG_MIN_RESIDENCY` and some next wakeup is set; otherwise only
  off-plus-on latency against the QoS constraints.
- Domain given `pm_domain_always_on_gov`: `pm_genpd_init()` sets
  `GENPD_FLAG_RPM_ALWAYS_ON`, not `GENPD_FLAG_ALWAYS_ON`.
- Same domain at system suspend: `genpd_sync_power_off()` can power it off, to
  the deepest state.
- Same domain at runtime: governor data is still allocated and
  `default_suspend_ok()` still runs for each device runtime suspend.
