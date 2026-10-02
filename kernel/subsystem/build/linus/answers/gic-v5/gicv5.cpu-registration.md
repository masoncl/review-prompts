- `GICV5_IRS_PE_SELR`: gets the IAFFID; `GICV5_IRS_PE_CR0`: gets only
  `GICV5_IRS_PE_CR0_DPS` set to 1.

| Condition in `gicv5_irs_register_cpu()` | Return |
|---|---|
| no valid IAFFID | `-ENODEV` |
| `per_cpu_irs_data` is NULL | `-ENXIO` |
| wait after `GICV5_IRS_PE_SELR` fails, by timeout or V clear | `-ENXIO` |
| wait after `GICV5_IRS_PE_CR0` times out | `-ETIMEDOUT` |

- `-EIO` and `-EINVAL`: never returned by `gicv5_irs_register_cpu()`.
- `gicv5_starting_cpu()`: returns `-ENODEV` with a `WARN()` before
  registration when the CPU lacks `ARM64_HAS_GICV5_CPUIF`.
- Hotplug state: `CPUHP_AP_IRQ_GIC_STARTING`, installed by
  `cpuhp_setup_state_nocalls()` in `gicv5_smp_init()` with a NULL teardown.
