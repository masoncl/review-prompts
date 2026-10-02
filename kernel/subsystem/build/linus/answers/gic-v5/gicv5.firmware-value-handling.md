- Scope of a fatal fault: it ends the probe of that one IRS;
  `gicv5_irs_of_init()` unwinds it and `gicv5_irs_of_probe()` goes on to the
  next node.
- `gicv5_irs_of_probe()`: returns `-ENODEV` only when no IRS is left on
  `irs_nodes`.
- Fatal faults: all are found before the per-CPU loop; the loop itself
  cannot fail.
- Missing `arm,iaffids`: caught as a count that differs from the `cpus`
  count, `-EINVAL`.

| Entry in the loop | Result | Message |
|---|---|---|
| `of_parse_phandle()` returns NULL | skipped | `pr_warn()` with `FW_BUG` |
| `of_cpu_node_to_id()` is negative | skipped | none |
| IAFFID has bits above the IRS width | skipped | `pr_warn()`, no `FW_BUG` |

- Fatal faults: `gicv5_irs_of_init_affinity()` prints nothing; its caller
  `gicv5_irs_of_init()` prints one `pr_err()`.
- Skipped CPU: `gicv5_irs_register_cpu()` returns `-ENODEV` when it comes
  online; for the boot CPU that fails `gicv5_init_common()`.
- `FW_BUG`: used in two messages of the IRS driver, the phandle one and
  `gic_request_region()`; other firmware faults are reported without it.
- `WARN()`: the driver uses it for conditions that hardware or firmware
  determine, for example a clear `GICV5_IRS_IDR2_LPI` in `gicv5_irs_init()`
  and an ITS found enabled in `gicv5_its_init_bases()`.
- **Unsafe usage**: storing an IAFFID from firmware and setting `valid`
  without testing it against the IAFFID width of the IRS.
  - Unsafe: the value is later placed in `GICV5_IRS_PE_SELR_IAFFID` and
    `GICV5_GIC_CDAFF_IAFFID_MASK` with no further test.
  - Safe: test against `GICV5_IRS_IDR1_IAFFID_BITS` + 1 bits of that IRS and
    skip the entry, as `gicv5_irs_of_init_affinity()` and
    `gic_acpi_parse_iaffid()` do.
