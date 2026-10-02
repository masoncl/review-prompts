- `gicv5_ppi_irq_chip`: has `irq_set_vcpu_affinity`; it marks the PPI
  forwarded, and `gicv5_ppi_irq_eoi()` then skips the `GIC CDDI`.
- `gicv5_spi_irq_set_type()`: defined in `drivers/irqchip/irq-gic-v5-irs.c`;
  writes `GICV5_IRS_SPI_SELR` then `GICV5_IRS_SPI_CFGR` by MMIO under
  `spi_config_lock`; it does not issue `GIC CDHM`.
- `gicv5_spi_irq_set_type()`: treats high/low and rising/falling as the same;
  any other value, such as `IRQ_TYPE_EDGE_BOTH`, returns `-EINVAL`.
- SPI flow handler: `handle_fasteoi_irq()` for edge and level alike.
- `gicv5_its_irq_chip`: no `irq_retrigger`, no `irq_set_type`, no `flags`.
- Resend of an ITS interrupt: `try_retrigger()` in `kernel/irq/resend.c` falls
  back to `irq_chip_retrigger_hierarchy()`, which reaches
  `gicv5_lpi_irq_retrigger()`.
- SPI and LPI `irq_set_irqchip_state`: accepts `IRQCHIP_STATE_PENDING` only,
  anything else returns `-EINVAL`; `irq_get_irqchip_state` handles pending and
  active.
- PPI `irq_set_irqchip_state`: accepts pending and active.
- Software pending for SPI and LPI: `gicv5_iri_irq_write_pending_state()`;
  there is no gicv5_iri_irq_set_irqchip_state() here.
- IWB chip: its type callback is `gicv5_iwb_set_type()`, in `iwb_msi_template`.
