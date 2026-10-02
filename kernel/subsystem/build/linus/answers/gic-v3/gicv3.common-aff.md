- `GICR_TYPER_COMMON_LPI_AFF` counts the affinity levels kept, from Aff3
  down: 0 keeps none, 1 keeps Aff3, 2 keeps Aff3.Aff2, 3 keeps
  Aff3.Aff2.Aff1.
- Aff0 is never kept; value 0 gives key 0 for every redistributor, which is
  the largest group.
- Comparers, all by equality, all in `drivers/irqchip/irq-gic-v3-its.c`:

| Function | Compares | Reached from |
|---|---|---|
| `find_sibling_its()` | one v4.1 ITS with another | `its_alloc_tables()` |
| `inherit_vpe_l1_table_from_its()` | this CPU's redistributor with each v4.1 ITS | `allocate_vpe_l1_table()` |
| `inherit_vpe_l1_table_from_rd()` | this CPU's redistributor with other CPUs' | `allocate_vpe_l1_table()` |

- `gic_populate_rdist()` does not compare the key.
- `inherit_vpe_l1_table_from_rd()`: returns at the first other CPU with a
  `rd_base` and an equal key, without testing `GICR_VPROPBASER_4_1_VALID`;
  `allocate_vpe_l1_table()` tests the bit on the returned value.
