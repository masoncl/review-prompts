| Helper | Register polled | Valid test | Poll |
|---|---|---|---|
| `gicv5_irs_wait_for_spi_op()` | `GICV5_IRS_SPI_STATUSR` | always | atomic |
| `gicv5_irs_wait_for_pe_selr()` | `GICV5_IRS_PE_STATUSR` | yes | atomic |
| `gicv5_irs_wait_for_pe_cr0()` | `GICV5_IRS_PE_STATUSR` | no | atomic |
| `gicv5_irs_wait_for_idle()` | `GICV5_IRS_CR0` | no | atomic |
| `gicv5_irs_ist_synchronise()` | `GICV5_IRS_IST_STATUSR` | no | atomic |
| `gicv5_irs_syncr()` | `GICV5_IRS_SYNC_STATUSR` | no | sleeping |

- Failed valid test: `-EIO`, not `-EINVAL`.
- `gicv5_irs_wait_for_irs_pe()`: tests `GICV5_IRS_PE_STATUSR_V` only when
  its `selr` argument is true; the two wrappers in the table fix it.
- `gicv5_irs_wait_for_spi_op()`: tests `GICV5_IRS_SPI_STATUSR_V` after the
  select write and again after the `GICV5_IRS_SPI_CFGR` write.
- Timeout: returned as `-ETIMEDOUT` before the valid bit is looked at.
