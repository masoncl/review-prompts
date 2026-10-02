| Job | File | Easy to miss |
|---|---|---|
| `struct dev_pm_domain` | `include/linux/pm.h` | not in `include/linux/pm_domain.h` |
| DT bindings, generic | `Documentation/devicetree/bindings/power/power-domain.yaml`, `Documentation/devicetree/bindings/power/domain-idle-state.yaml` and `Documentation/devicetree/bindings/power/power_domain.txt` | `power-domain.yaml` is the provider schema; of the three, only `power_domain.txt` describes `power-domain-names` |
| DT bindings, per provider | search `Documentation/devicetree/bindings/` for `#power-domain-cells` | also in other subdirectories, for example `clock/`, `soc/`, `firmware/` and `arm/` |
| cpuidle: shared CPU-domain helpers | `drivers/cpuidle/dt_idle_genpd.c` | built under `CONFIG_DT_IDLE_GENPD` |
| cpuidle: PSCI domains | `drivers/cpuidle/cpuidle-psci-domain.c` | CPUs are attached from `drivers/cpuidle/cpuidle-psci.c` via `dt_idle_attach_cpu()` |
| cpuidle: RISC-V SBI domains | `drivers/cpuidle/cpuidle-riscv-sbi.c` | domains and CPU attach in the one file; see `sbi_pd_init()` |
| Providers inside | directories listed in `drivers/pmdomain/Makefile` | `arm/` holds SCMI and SCPI; `ti/` holds `omap_prm.c` and `ti_sci_pm_domains.c` |
| Providers outside, largest group | `drivers/clk/` | `drivers/clk/qcom/gdsc.c` serves every Qualcomm clock controller that sets `.gdscs` |
| Providers outside, rest | search for `pm_genpd_init(` outside `drivers/pmdomain/` | see below |

- `Documentation/devicetree/bindings/power/` subdirectories: not per-vendor;
  `supply/` and `reset/` hold power-supply and reset bindings, and
  `avs/qcom,cpr.yaml` is the only genpd provider binding in a subdirectory.
- `drivers/firmware/`: no file there calls `pm_genpd_init()`; the SCMI, SCPI,
  TI SCI, i.MX SCU and ZynqMP providers are all under `drivers/pmdomain/`.
- `drivers/soc/`: the only providers there are `drivers/soc/tegra/pmc.c`
  and `drivers/soc/dove/pmu.c`.
- `arch/`: the only caller of `pm_genpd_init()` is
  `arch/arm/mach-s3c/pm-s3c64xx.c`.
- Unexpected providers: `drivers/irqchip/irq-qcom-mpm.c`,
  `drivers/gpu/drm/amd/amdgpu/amdgpu_acp.c` and
  `drivers/gpu/drm/amd/amdgpu/isp_v4_1_1.c`.
- No OF provider: the two amdgpu files and
  `arch/arm/mach-s3c/pm-s3c64xx.c` call neither
  `of_genpd_add_provider_simple()` nor `of_genpd_add_provider_onecell()`;
  they add devices with `pm_genpd_add_device()`,
  `arch/arm/mach-s3c/pm-s3c64xx.c` only under `CONFIG_S3C_DEV_FB`.
