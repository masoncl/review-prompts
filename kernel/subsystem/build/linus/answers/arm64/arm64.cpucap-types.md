| Type | Scope | Late CPU may have it, system not | Late CPU may lack it, system has | Conflict |
|---|---|---|---|---|
| `ARM64_CPUCAP_LOCAL_CPU_ERRATUM` | local | no | yes | CPU dies |
| `ARM64_CPUCAP_SYSTEM_FEATURE` | system | yes | no | CPU dies |
| `ARM64_CPUCAP_WEAK_LOCAL_CPU_FEATURE` | local | yes | yes | none |
| `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE` | local, all early CPUs | yes | no | CPU dies |
| `ARM64_CPUCAP_BOOT_RESTRICTED_CPU_LOCAL_FEATURE` | local | no | yes | CPU dies |
| `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE` | boot | no | no | panic |
| `ARM64_CPUCAP_BOOT_CPU_FEATURE` | boot | yes | no | CPU dies |

- `ARM64_CPUCAP_BOOT_RESTRICTED_CPU_LOCAL_FEATURE`: same bits as
  `ARM64_CPUCAP_LOCAL_CPU_ERRATUM`.
- `ARM64_CPUCAP_PANIC_ON_CONFLICT`: set only by
  `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE`.
- `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE`: adds
  `ARM64_CPUCAP_MATCH_ALL_EARLY_CPUS`; `update_cpu_capabilities()` sets the
  cap only while probing the boot CPU and clears it when an early secondary
  does not match, so `cpus_have_cap()` can go from true to false before
  finalisation.
- There is no ARM64_CPUCAP_BOOT_CPU_ERRATUM; `arm64_errata` entries use
  `ARM64_CPUCAP_LOCAL_CPU_ERRATUM` (set by the `ERRATA_MIDR_RANGE()` family),
  and a few use `ARM64_CPUCAP_WEAK_LOCAL_CPU_FEATURE` or
  `ARM64_CPUCAP_SYSTEM_FEATURE`.
- Which CPU is late: see `check_local_cpu_capabilities()`; every secondary is
  verified against boot-scope caps, and against the other scopes only once
  `system_capabilities_finalized()` is true.
- Secondary before finalisation: not verified for local-scope caps; it runs
  `update_cpu_capabilities(SCOPE_LOCAL_CPU)` and can set them.
- Conflict: `verify_local_cpu_caps()` prints "Detected conflict for
  capability", then calls `cpu_panic_kernel()` or `cpu_die_early()`.
- `cpu_die_early()`: marks the CPU not present; under `CONFIG_HOTPLUG_CPU` it
  sets `CPU_KILL_ME` and calls `__cpu_try_die()`; if that returns, or without
  the option, it sets `CPU_STUCK_IN_KERNEL` and parks; the cap is unchanged.
- `cpu_panic_kernel()`: the secondary sets `CPU_PANIC_KERNEL` and parks; the
  CPU in `__cpu_up()` calls `panic()`.
- No conflict and the system has the cap: `.cpu_enable` runs on the new CPU
  whether or not that CPU matches.
