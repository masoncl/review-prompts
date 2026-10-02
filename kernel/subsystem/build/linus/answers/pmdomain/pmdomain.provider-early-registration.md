- Both functions: return `-ENODEV` while `genpd_bus_registered` is false. The
  test is at the same place in both, right after the NULL-argument test and
  before `genpd_present()`.
- `genpd_bus_init()`: sets the flag only if all its registrations succeed; if
  it fails, both functions return `-ENODEV` for the rest of the boot.
- `core.o` is listed last in `drivers/pmdomain/Makefile`, after every vendor
  directory, so a `core_initcall()` in a vendor directory is linked ahead of
  `genpd_bus_init()`.
- `pm_genpd_init()` and `pm_genpd_add_subdomain()`: do not test
  `genpd_bus_registered`.
- **Potentially unsafe usage**: registering a provider from code that can run
  before `genpd_bus_init()`.
  - Unsafe: from an `early_initcall()` or a `CLK_OF_DECLARE()` init function;
    the call returns `-ENODEV`, not `-EPROBE_DEFER`, and nothing retries it.
  - Safe: initialise and link early, register from a later initcall, as
    `rcar_sysc_pd_init()` and `rcar_sysc_pd_init_provider()` in
    `drivers/pmdomain/renesas/rcar-sysc.c` do; `cpg_mstp_pd_init_provider()` in
    `drivers/clk/renesas/clk-mstp.c` is the same split.
  - Safe: a `core_initcall()` that only registers a platform driver, for
    example `exynos4_pm_init_power_domain()`, when the device is probed after
    `genpd_bus_init()` has run.
