- `gic_enable_quirks()`: IIDR only; it skips every entry that has
  `compatible` or `property`.
- `gic_enable_of_quirks()`: handles only entries with `compatible` or
  `property`; an entry with both needs both to match.
- Both functions run every matching entry, and log only when `init` returns
  true.
- ITS: `its_enable_quirks()` runs the IIDR pass, then the devicetree pass
  only when `is_of_node()`; there is no ACPI-keyed quirk matching.
- `gic_quirks` on ACPI: in `drivers/irqchip/irq-gic-v3.c`
  `gic_enable_of_quirks()` is called from `gic_of_init()` only, so the
  `compatible` and `property` entries never apply.
- `gic_of_init()` runs the devicetree quirks before `gic_init_bases()` fills
  `gic_data.dist_base` and `rdists.gicd_typer`.
- `gic_quirks`, in `drivers/irqchip/irq-gic-v3.c`:

| `init` | Sets | Effect where tested |
|---|---|---|
| `gic_enable_quirk_msm8996()` | `FLAGS_WORKAROUND_GICR_WAKER_MSM8996` | `gic_enable_redist()` returns at once |
| `gic_enable_quirk_asr8601()` | `FLAGS_WORKAROUND_ASR_ERRATUM_8601001` | `gic_cpu_to_affinity()` moves Aff1 to Aff0 and Aff2 to Aff1, for every user |
| `gic_enable_quirk_hip06_07()` | clears bits 9:8 of `rdists.gicd_typer` | `GIC_ESPI_NR` is 0; returns false if ESPI bit was clear |
| `gic_enable_quirk_cavium_38539()` | `FLAGS_WORKAROUND_CAVIUM_ERRATUM_38539` | `gic_init_bases()` does not read `GICD_TYPER2` |
| `gic_enable_quirk_nvidia_t241()` | `gic_nvidia_t241_erratum` | `gic_dist_base_alias()`; GICv4 flags stay false |
| `gic_enable_quirk_arm64_2941627()` | `gic_arm64_2941627_erratum` | `gic_arm64_erratum_2941627_needed()` |
| `rd_set_non_coherent()` | `RDIST_FLAGS_FORCE_NON_SHAREABLE` | `rdists_support_shareable()` in the ITS driver |
| `gic_enable_quirk_rk3399()` | `FLAGS_WORKAROUND_INSECURE`, only on machine `rockchip,rk3399`, else returns false | `gic_prio_init()` |

- `gic_enable_quirk_nvidia_t241()`: also needs
  `arm_smccc_get_soc_id_version()` to match and at least three chips in the
  redistributor addresses, else returns false.
- Erratum 2941627 with `gic_chip`: `gic_eoi_irq()` still writes
  `ICC_EOIR1_EL1`, then also `GICD_ICACTIVER`; only
  `gic_eoimode1_eoi_irq()` replaces `gic_write_dir()` with
  `GICD_ICACTIVER`.
- `its_quirks`, in `drivers/irqchip/irq-gic-v3-its.c`:

| `init` | Sets | Effect where tested |
|---|---|---|
| `its_enable_quirk_cavium_22375()` | `ITS_FLAGS_WORKAROUND_CAVIUM_22375`, DEVBITS in `its->typer` | `its_alloc_tables()` uses `GITS_BASER_nCnB` |
| `its_enable_quirk_cavium_23144()` | `ITS_FLAGS_WORKAROUND_CAVIUM_23144` | `its_select_cpu()`, `its_cpu_init_collection()` stay on the ITS node |
| `its_enable_quirk_qdf2400_e0065()` | ITT entry size in `its->typer`, no flag | — |
| `its_enable_quirk_socionext_synquacer()` | `pre_its_base`, `get_msi_base`, no flag | clears `IRQ_DOMAIN_FLAG_ISOLATED_MSI` |
| `its_enable_quirk_hip07_161600802()` | `vlpi_redist_offset`, no flag | added to the VMAPP and VMOVP target |
| `its_enable_quirk_hip09_162100801()` | `ITS_FLAGS_WORKAROUND_HISILICON_162100801` | `its_vpe_set_affinity()` invalidates after `its_send_vmovp()` |
| `its_enable_rk3588001()` | `ITS_FLAGS_FORCE_NON_SHAREABLE` and `RDIST_FLAGS_FORCE_NON_SHAREABLE`, only on machine `rockchip,rk3588` or `rockchip,rk3588s`, else returns false | `its_alloc_tables()`, `its_probe_one()` |
| `its_set_non_coherent()` | `ITS_FLAGS_FORCE_NON_SHAREABLE` only | `its_alloc_tables()`, `its_probe_one()` |
| `its_enable_dma32()` | `GFP_DMA32` in `gfp_flags_quirk`, only on a machine in `dma_32bit_impaired_platforms`, else returns false | `its_alloc_pages_node()` |

- `its_enable_quirk_socionext_synquacer()`: returns false without the
  `socionext,synquacer-pre-its` property.
- `its_enable_dma32()`: its table entry has no `#ifdef`; the platforms in
  `dma_32bit_impaired_platforms` are under
  `CONFIG_RENESAS_ERRATUM_GEN4GICITS1` and
  `CONFIG_ROCKCHIP_ERRATUM_3568002`.
