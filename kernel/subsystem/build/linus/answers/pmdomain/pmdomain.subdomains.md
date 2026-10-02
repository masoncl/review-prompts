- `sd_count` at zero is not enough for the parent to power off:
  `genpd_power_off()` and `genpd_sync_power_off()` also return if any child has
  `state_idx < state_count - 1`. A child that is off in a shallower state keeps
  the parent on.
- Parent off and child on: `genpd_add_subdomain()` returns `-EINVAL`. It does
  not power the parent on.
- Duplicate link: `-EINVAL`.
- Flags read by `genpd_add_subdomain()`: only `GENPD_FLAG_IRQ_SAFE`. It has no
  test of `GENPD_FLAG_ALWAYS_ON`, and none of `GENPD_FLAG_CPU_DOMAIN`, so it
  does not compare lock kinds.
- **Potentially unsafe usage**: `pm_genpd_remove()` on a domain still linked to
  a parent.
  - Unsafe: when the domain is on and the parent stays registered.
    `genpd_remove()` frees the `child_links` without `genpd_sd_counter_dec()`,
    and `genpd_power_off()` of the parent then returns early on `sd_count`.
  - Safe: unlink first with `pm_genpd_remove_subdomain()`, which decrements for
    a child that is on; `scmi_pm_domain_remove()` does this through
    `of_genpd_remove_child_ids()`, which skips a parent whose provider is no
    longer registered.
  - Safe: the parent is removed in the same unwind, after its children, as
    `scpsys_domain_cleanup()` in `drivers/pmdomain/mediatek/mtk-pm-domains.c`
    does; `genpd_remove()` does not read `sd_count`.
- Device tree property: `power-domains-child-ids`, beside `power-domains` in
  the provider node; binding in
  `Documentation/devicetree/bindings/power/power-domain.yaml`.
- Parser: `of_genpd_add_child_ids()` in `drivers/pmdomain/core.c`.
  `of_genpd_add_provider_onecell()` does not call it. The provider calls it
  after registering, as `scmi_pm_domain_probe()` does, and undoes it with
  `of_genpd_remove_child_ids()`.
- Child id: indexes `data->domains[]` directly; the provider's `xlate` is not
  used for the child.
- `of_genpd_add_child_ids()` returns: the number of links on success, 0 when
  either property is absent, `-EINVAL` when the two counts differ. A parent
  that is not registered yet gives `-ENOENT`; `of_genpd_add_subdomain()` maps
  that to `-EPROBE_DEFER`, `of_genpd_add_child_ids()` does not.
- `of_genpd_add_child_ids()` on failure: removes the links it had already
  added.
