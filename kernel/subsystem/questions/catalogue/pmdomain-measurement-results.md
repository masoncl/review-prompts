# What the pmdomain measurement found

Three models were asked the 36 questions in `pmdomain-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels up to 6.19), reader A a little behind it (up to 6.17), and
reader B older again (6.6 to 6.12), which is before the core learnt to keep
domains on until sync_state. The hand-written guide was never checked against
current sources, so differences between it and the built guide are expected and
are noted near the end.

All three know what a generic PM domain is, how runtime PM reaches it, how a
parent is powered before its child and how a device with several domains gets
virtual devices. What they get wrong is what moved in the last few releases
(the provider bus and the sync_state wiring, the attach flags, the newer domain
flags and helpers), a handful of facts they all state the same wrong way, and
which in-tree drivers show a given pattern.

## What all three readers got wrong

- **The always-on governor.** Readers A and C both gave it a `power_down_ok`
  callback called always_on_power_down_ok(), which does not exist; reader B's
  callback lists were wrong throughout. `pm_domain_always_on_gov` sets only
  `suspend_ok`, and `pm_genpd_init()` sets `GENPD_FLAG_RPM_ALWAYS_ON` on a
  domain that is given it.
- **The governor at system suspend.** All three said the governor is skipped
  and the deepest state is always used. `genpd_sync_power_off()` calls
  `system_power_down_ok()` when the governor has one, which
  `pm_domain_cpu_gov` does, and takes the deepest state only otherwise.
- **`genpd_power_off()` returns nothing.** Reader A gave it error codes,
  reader B had a notifier rejection come back through it, reader C had it
  return 0. It is void: a declined power-off just returns, and one the
  provider's callback refuses counts `rejected` and leaves the domain on.
- **The power callbacks and the notifiers are not always called with the
  domain lock held.** `genpd_switch_state()`, behind `dev_pm_genpd_suspend()`
  and `dev_pm_genpd_resume()`, takes the lock only for an IRQ-safe domain.
- **Re-measured latencies.** `_genpd_power_on()` and `_genpd_power_off()`
  update a state's latency only on the runtime path, only when the domain has
  governor data, and only when the state has no `fwnode`, so a state parsed
  from the device tree is never updated. Every reader said "whenever measured".
- **Which drivers show what.** Each reader named drivers for the boot-state
  patterns and the opt-out flags and each was partly wrong: `gpc.c` powers its
  domains on and passes false, `gpcv2.c` passes true, `rpmhpd.c` passes true,
  `ti_sci_pm_domains.c` reads the hardware; the only user of
  `GENPD_FLAG_NO_SYNC_STATE` is `drivers/soc/tegra/pmc.c`; and
  `GENPD_FLAG_NO_STAY_ON` is set by three Renesas drivers, Rockchip and the
  Tegra BPMP driver. One reader offered `imx8m-blk-ctrl.c` as the example of a
  complete probe error path; it leaves its power notifier registered when the
  last step of probe fails.
- **Providers outside `drivers/pmdomain/`.** Every reader wrote a wildcard for
  `drivers/soc/` and `arch/arm/` and none named the largest group, the clock
  drivers (`drivers/clk/qcom/gdsc.c`, `drivers/clk/renesas/`).
- The debugfs file `idle_states_desc`, and that `perf_state` exists only for a
  domain with a `set_performance_state` callback.

## What only some readers got wrong

Readers A and B:

- **The lock of a CPU domain.** `genpd_lock_init()` gives every domain with
  `GENPD_FLAG_CPU_DOMAIN` a raw spinlock, tested before `GENPD_FLAG_IRQ_SAFE`,
  on every configuration. Reader A said only on PREEMPT_RT and only with the
  IRQ-safe flag as well; reader B knew two lock kinds.
- **The newer flags.** Reader A's table lacked `GENPD_FLAG_NO_SYNC_STATE` and
  `GENPD_FLAG_NO_STAY_ON`; reader B's lacked those and
  `GENPD_FLAG_DEV_NAME_FW`.
- **Attaching one domain.** `dev_pm_domain_attach()` takes a flags word, not a
  bool. `PD_FLAG_ATTACH_POWER_ON` goes only to the ACPI attach;
  `genpd_dev_pm_attach()` always powers the domain on.
  `PD_FLAG_DETACH_POWER_OFF` is parked in `dev->power.detach_power_off` for
  `device_unbind_cleanup()`. A missing provider returns whatever
  `driver_deferred_probe_check_state()` says, which can be `-ENODEV` or
  `-ETIMEDOUT` as well as `-EPROBE_DEFER`.
- **Attaching several.** `dev_pm_domain_attach_list()` adds a stateless
  runtime-PM device link for every domain unless told not to;
  `PD_FLAG_DEV_LINK_ON` only adds `DL_FLAG_RPM_ACTIVE` (reader A thought no
  link is made without it). `dev_pm_domain_start()` does not walk the list or power
  anything on (reader B).
- **Registering early.** Both registration functions return `-ENODEV` until
  `genpd_bus_init()`, a `core_initcall`, has run. The domain's own device is on
  `genpd_provider_bus_type`, is added at registration and deleted by
  `of_genpd_del_provider()`. Reader A was unsure of all of this and reader B
  put the device on the wrong bus and registered it in `pm_genpd_init()`.
- **sync_state in strict mode.** Nothing is forced; `fw_devlink_dev_sync_state()`
  prints one `dev_info()` line per pending consumer. Calls are also held back
  until `sync_state_resume_initcall()`.
- The device tree property for a provider's parents is
  `power-domains-child-ids` (reader A offered power-domain-map, reader B none;
  reader C doubted `of_genpd_add_child_ids()` exists).
- Consumer helpers: reader A lacked `dev_pm_genpd_is_on()` and had three
  preconditions wrong; reader B knew only the performance state and notifier
  ones.

Reader B alone:

- **Nothing about staying on.** It said `GENPD_FLAG_ALWAYS_ON` is the only
  protection for a domain the bootloader left on and that such a domain races
  with slow probers. It also said a provider node with no device gets no
  sync_state at all, that the end-of-boot power-off is synchronous, and that a
  constant `is_off` of true lets the core cut live hardware (it is false for a
  domain that is off that skips the power-on sequence).
- With no governor the runtime power-off picks the deepest state (it is state
  0). A powered-off subdomain does not vote and a suspended device keeps its
  vote (both reversed). `GENPD_FLAG_ACTIVE_WAKEUP` alone keeps a domain on at
  suspend (it also needs the device on the wakeup path and no out-of-band
  wakeup). The power-off argument of detach powers the domain off (it is
  ignored).
- Invented names: pm_genpd_default_suspend_ops, device_list, slock_lock,
  child_count, __genpd_dev_pm_qos_notifier(), dev_pm_opp_get_required_pstate().

Reader A alone: `genpd_runtime_suspend()` drops the device's performance state
before it tries the power-off (it is after); `genpd_freeze_noirq()` only stops
the device (it goes through `genpd_finish_suspend()` and can power the domain
off); `GENPD_FLAG_RPM_ALWAYS_ON` applies "while runtime PM is in use" (it is
unconditional in `genpd_power_off()`).

Reader C alone: in its checklist answer `stay_on` lasts until
`genpd_power_off_unused()`, contradicting its own correct answer elsewhere;
Rockchip sets `GENPD_FLAG_NO_STAY_ON` because of the regulator delay, which
nothing in the driver says; the Exynos forced power-off is limited to a display
domain (it is gated on `CONFIG_ARM` and one compatible); and a missing domain
always fails onecell registration with `-EINVAL`. The checker found that a slot
that is not initialised, after one that was added, unwinds and returns 0,
because `ret` still holds the last `device_add()` result.

## What the readers already knew

Readers A and C needed nothing on the entry points or the power-on path and
next to nothing on the structure's fields, the lock order, subdomain counting,
the end-of-boot power-off and what a driver's own sync_state callback has to
call. Reader C was also right about the sync_state wiring, the flags, the
attach paths, detach and the wakeup path. These are dropped from the build set
or kept only where the third reader was wrong about something a reviewer needs.

## Where the hand-written guide is stale

`pmdomain.md` is recent and nearly all of it is about one mechanism, `stay_on`
and sync_state. What it says about that mechanism is correct: where the flag is
set and cleared, that `genpd_power_off()` tests it, that without
`CONFIG_PM_GENERIC_DOMAINS_OF` it is always false, the initcall level of
`genpd_power_off_unused()` and the regulator core's thirty second delayed
work. The gaps and the unsupported parts:

- It says the provider's sync_state "is handled by"
  `genpd_provider_sync_state()` or `of_genpd_sync_state()` and leaves out the
  case that matters in review: a provider driver with its own sync_state
  callback keeps it, because `dev_set_drv_sync_state()` refuses with `-EBUSY`
  and the registration functions ignore that, so the driver has to call
  `of_genpd_sync_state()` itself. It does not mention
  `GENPD_FLAG_NO_SYNC_STATE`.
- Its list of `GENPD_FLAG_NO_STAY_ON` users lacks
  `drivers/pmdomain/renesas/rcar-gen4-sysc.c`.
- It says Rockchip sets the flag "specifically to avoid" the regulator
  scenario. The driver gives no reason; what it does say is that a domain
  needing a regulator is forced off in probe because the regulator's state is
  unknown.
- It prefers `exynos_pd_power_off()` to `of_genpd_sync_state()` for a targeted
  reset. No in-tree driver uses `of_genpd_sync_state()` for that, and the
  Exynos function is a static callback; this is one review written as a rule.
- "Drivers ... should set this flag" and "must provide a `GENPD_FLAG_*`
  opt-out" tell a reviewer what to ask for, not how the code works.
- It does not say that system suspend ignores `stay_on`, nor mention
  `pd_ignore_unused`.
- It has nothing on the rest of genpd: the flags, the lock kinds, the
  conditions for a power-off, registration and removal, attach, governors,
  performance states, system sleep.

## Left out of the build set

The hand-written guide is 735 words, so the build set holds 14 of the 36
questions. The guide loads for patches under `drivers/pmdomain/` and for callers
of the provider interface, so the choice is weighted towards what a provider
driver and the core must get right, and towards what the old guide was about.
Left out although a reader got them wrong: both attach questions, detach and
the consumer helpers (consumer drivers do not load this guide); performance
states, OPP tables, idle states and CPU domains (each confined to a few
functions or to cpuidle); system sleep, the wakeup path and the checks skipped
at sleep (the flags table and the governors question carry the two facts a
provider needs); the domain's own device and the provider callbacks (their main
facts are in the sync_state wiring, registration and lock questions); runtime
PM order, notifiers and subdomains; and provider pitfalls, which overlaps
registration, removal and the boot-state question. Left out because readers A
and C already knew them: entry points, structure fields, lock order, the
power-on path. Documentation and debugfs is left out as low value.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 89 corrections, 33% rewritten on average
reader B: 90 corrections, 77% rewritten on average
reader C: 70 corrections, 17% rewritten on average

question                            reader A      reader B      reader C
pmdomain.core-files                 19% ( 3)      30% ( 2)      24% ( 3)
pmdomain.entry-points                0% ( 0)      21% ( 3)       0% ( 0)
pmdomain.docs-and-debug             53% ( 2)      64% ( 1)      57% ( 3)
pmdomain.struct-fields               9% ( 1)      80% ( 7)      11% ( 2)
pmdomain.flags                      24% ( 2)      62% ( 3)       4% ( 2)
pmdomain.locks                      18% ( 3)      75% ( 2)       8% ( 2)
pmdomain.lock-order                 14% ( 1)      81% ( 1)      10% ( 1)
pmdomain.subdomains                 17% ( 2)      82% ( 2)      21% ( 2)
pmdomain.power-off-conditions       36% ( 4)      84% ( 2)      22% ( 3)
pmdomain.power-on-path               0% ( 0)      81% ( 1)       0% ( 0)
pmdomain.runtime-pm-callbacks       12% ( 2)      95% ( 1)      28% ( 2)
pmdomain.notifiers                  21% ( 1)      63% ( 1)      37% ( 1)
pmdomain.stay-on                    43% ( 3)      88% ( 3)       5% ( 4)
pmdomain.sync-state-wiring          60% ( 2)      80% ( 1)       3% ( 1)
pmdomain.sync-state-usage           65% ( 1)      86% ( 1)       0% ( 0)
pmdomain.sync-state-timing          59% ( 2)      90% ( 1)       9% ( 1)
pmdomain.unused-power-off           16% ( 0)      89% ( 1)      13% ( 1)
pmdomain.boot-state-usage           74% ( 4)      82% ( 1)      27% ( 4)
pmdomain.provider-registration      38% ( 3)      86% ( 6)      22% ( 2)
pmdomain.provider-removal           33% ( 3)      76% ( 2)      15% ( 1)
pmdomain.provider-device            56% ( 2)      94% ( 1)      13% ( 1)
pmdomain.callbacks                  21% ( 2)      97% ( 2)      11% ( 3)
pmdomain.provider-pitfalls          34% ( 2)      78% ( 3)      18% ( 2)
pmdomain.single-attach              49% ( 4)      76% ( 5)       9% ( 1)
pmdomain.multi-attach               27% ( 2)      85% ( 2)       5% ( 1)
pmdomain.detach                     42% ( 4)      76% ( 1)       0% ( 0)
pmdomain.consumer-helpers           35% ( 6)      81% ( 3)      13% ( 1)
pmdomain.performance-states         36% ( 5)      84% ( 4)      19% ( 3)
pmdomain.opp-tables                 20% ( 2)      80% ( 2)      49% ( 3)
pmdomain.governors                  28% ( 4)      80% ( 4)      22% ( 4)
pmdomain.idle-states                29% ( 2)      71% ( 3)      20% ( 3)
pmdomain.cpu-domains                51% ( 3)      86% ( 3)      38% ( 3)
pmdomain.system-sleep               26% ( 5)      78% ( 4)       7% ( 1)
pmdomain.wakeup-path                29% ( 2)      83% ( 3)       0% ( 0)
pmdomain.sleep-checks               30% ( 2)      83% ( 2)      21% ( 3)
pmdomain.core-change-checklist      79% ( 3)      80% ( 6)      53% ( 6)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `pmdomain.struct-fields`, `pmdomain.subdomains`, `pmdomain.runtime-pm-callbacks`, `pmdomain.callbacks`, `pmdomain.provider-pitfalls`, `pmdomain.single-attach`, `pmdomain.multi-attach`, `pmdomain.consumer-helpers`, `pmdomain.performance-states`, `pmdomain.system-sleep`.

## Questions reorganised

Organised by subject, 26 questions before and 23 after: domains, boot-time state and sync_state
(the two provider hazards beside the mechanism), power transitions, provider and consumer drivers.
Merged: `pmdomain.locks` and `pmdomain.callbacks` into `pmdomain.callback-context`;
`pmdomain.struct-fields` into `pmdomain.provider-pitfalls`, which asks what a provider may still
write in an initialised domain and not which fields there are.
Dropped: `pmdomain.core-change-checklist`, an inventory; its opt-out flags and configurations are
asked by `pmdomain.stay-on` and `pmdomain.flags`. What a probe error path must undo is asked once,
in `pmdomain.provider-pitfalls`.
