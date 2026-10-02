- Unknown encoding, all three functions: log, store the smallest known width,
  return `void`; the probe continues.

| Function | Log | Stored |
|---|---|---|
| `gicv5_set_cpuif_pribits()` | `pr_err()` | `cpuif_pri_bits` = 4 |
| `gicv5_set_cpuif_idbits()` | `pr_err()` | `cpuif_id_bits` = 16 |
| `irs_setup_pri_bits()` | `pr_warn()` | `irs_pri_bits` = 1 |

- `irs_pri_bits` of 1 makes `pri_bits` 1 in `gicv5_init_common()`, so
  `GICV5_IRQ_PRI_MI` becomes 0x10.
- The two CPU interface decoders run once, on the boot CPU, from
  `gicv5_init_common()`; `gicv5_starting_cpu()` decodes nothing on a
  secondary CPU.
- `irs_setup_pri_bits()` runs only for the first IRS, under
  `list_empty(&irs_nodes)` in `gicv5_irs_init()`.
- **Unsafe usage**: using the raw value of `ICC_IDR0_EL1_PRI_BITS`,
  `ICC_IDR0_EL1_ID_BITS` or `GICV5_IRS_IDR1_PRIORITY_BITS` as a bit count;
  the values are encodings, for example `ICC_IDR0_EL1_PRI_BITS_4BITS` is
  0b0011 and `GICV5_IRS_IDR1_PRIORITY_BITS_1BITS` is 0b000.
  - Safe: a `switch` over the named encodings with a `default`, as in
    `gicv5_set_cpuif_pribits()`; the encodings are defined in
    `arch/arm64/tools/sysreg` and `include/linux/irqchip/arm-gic-v5.h`.
- Numeric ID fields are not decoded with a `switch`:
  `gicv5_irs_init_ist()` uses `GICV5_IRS_IDR2_ID_BITS` as read, and
  `gicv5_irs_of_init()` uses `GICV5_IRS_IDR1_IAFFID_BITS` plus 1.
