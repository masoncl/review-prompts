- **Unsafe usage**: `pm_genpd_remove()` on a domain for which
  `pm_genpd_init()` did not return 0.
  - Safe: a NULL slot; `genpd_remove()` returns `-EINVAL` for it, as the unwind
    loop of `th1520_pd_probe()` relies on for disabled domains.
  - Safe: unwind only the domains whose init succeeded, as `imx93_pd_probe()`
    does by jumping past `pm_genpd_remove()` when init fails.
- **Potentially unsafe usage**: freeing a domain after `pm_genpd_remove()`
  without looking at the result.
  - Unsafe: when `has_provider` is set, `device_count` is not 0 or
    `parent_links` is not empty; the call returns `-EBUSY` and the domain stays
    on `gpd_list`.
  - Safe: in a probe error path where provider registration failed and the
    driver linked no subdomain under this domain, as `imx93_pd_probe()`;
    none of the three conditions in `genpd_remove()` can hold.
  - Safe: free only on success, as `psci_pd_remove()` in
    `drivers/cpuidle/cpuidle-psci-domain.c` does with the result of
    `of_genpd_remove_last()`.
- Writes after `pm_genpd_init()`: the core checks none. What matters is when
  each member is read.
- Consumed inside `pm_genpd_init()`, so a later write does not redo the step:
  `GENPD_FLAG_IRQ_SAFE` and `GENPD_FLAG_CPU_DOMAIN` for the lock type (in
  `genpd_lock_init()`), `GENPD_FLAG_PM_CLK`, `GENPD_FLAG_DEV_NAME_FW`,
  `GENPD_FLAG_NO_STAY_ON`, `name` for the device name (set by
  `dev_set_name()`), `state_count` of 0 for the default state.
- Overwritten by `pm_genpd_init()`, so a value set before it is lost: for
  example `gov` (replaced by the argument), `status`, and the `domain.ops`
  members it assigns. Other `domain.ops` members survive;
  `ti_sci_pm_domain_probe()` sets `suspend` there before init.
- Read at call time: `power_on`, `power_off`, `attach_dev`, `detach_dev`,
  `set_performance_state`. `set_performance_state` and
  `GENPD_FLAG_OPP_TABLE_FW` are also read at provider registration.
- Post-init write seen in tree: the lock class of `mlock`, with
  `lockdep_set_class()` in `imx93_blk_ctrl_probe()`; it has to follow init,
  which initialises the mutex.
- **Unsafe usage**: `pm_genpd_init()` again on a structure that
  `pm_genpd_remove()` released, without clearing it.
  - Unsafe: `genpd_free_data()` frees the default state but leaves `states`,
    `state_count` and `free_states` set, and `genpd_alloc_data()` allocates a
    new one only when `state_count` is 0. `device_initialize()` then reaches
    `kobject_init()`, which logs an already-initialised object.
  - Safe: a fresh zeroed structure for each probe, as `imx93_pd_probe()` gets
    from `devm_kzalloc()`.
- One domain, complete pair: `imx93_pd_probe()` and `imx93_pd_remove()` in
  `drivers/pmdomain/imx/imx93-pd.c`; `imx_pgc_domain_probe()` and
  `imx_pgc_domain_remove()` in `drivers/pmdomain/imx/gpcv2.c` have the same
  shape.
- Several domains with subdomain links: `imx93_blk_ctrl_probe()` in
  `drivers/pmdomain/imx/imx93-blk-ctrl.c` adds a `devm_add_action_or_reset()`
  after each step and has no `.remove`; devres unwinds provider, links, then
  domains, on probe failure and on unbind.
- `imx8m_blk_ctrl_probe()`: labels `cleanup_provider` and `cleanup_pds` plus
  `imx8m_blk_ctrl_remove()` are also complete for provider and domains.
- `drivers/pmdomain/mediatek/mtk-pm-domains.c`: has no `.remove` and never
  calls `of_genpd_del_provider()`; it is not an example of a remove path.
- None of these remove paths looks at the result of `pm_genpd_remove()`.
