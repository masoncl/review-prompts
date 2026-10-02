- NULL `fwnode`: both functions return `-EPROBE_DEFER`, from the first test in
  `__v4l2_fwnode_endpoint_parse()`; NULL is an accepted argument.
- `-ENXIO`: only when firmware has a non-zero `bus-type` that maps to a type
  other than a non-`V4L2_MBUS_UNKNOWN` `vep->bus_type`; reported with
  `pr_debug()` only.
- No `bus-type` property (or value 0) with an explicit `vep->bus_type`: no
  mismatch test runs; the call returns 0 even when no property of that bus is
  present, so the caller validates the result, as `imx219_check_hwcfg()` does
  for `num_data_lanes`.
- `-EINVAL` for the bus type: a `bus-type` value absent from the `buses` table
  in `drivers/media/v4l2-core/v4l2-fwnode.c`, and also `V4L2_MBUS_DPI`, which
  is in the table but has no case in the switch.
- Guessing (`V4L2_MBUS_UNKNOWN`, no `bus-type`): `vep->bus_type` is never
  `V4L2_MBUS_UNKNOWN` on a return of 0.

| Endpoint has | Guessed type |
|---|---|
| non-empty `data-lanes`, or `clock-lanes`, or `clock-noncontinuous` | `V4L2_MBUS_CSI2_DPHY` |
| else `hsync-active`, `vsync-active` or `field-even-active` | `V4L2_MBUS_PARALLEL` |
| none of these, including no properties at all | `V4L2_MBUS_BT656` |

- `vep->link_frequencies` and `vep->nr_of_link_frequencies`:
  `v4l2_fwnode_endpoint_parse()` never writes them;
  `v4l2_fwnode_endpoint_alloc_parse()` writes them only when
  `link-frequencies` has entries.
- `v4l2_fwnode_endpoint_free()`: calls `kfree()` on `vep->link_frequencies`
  whatever it holds, so `vep` must be zero-initialised before the parse for the
  free to be safe after a failed parse or an absent property.
- Defaults preset in `vep->bus`: the CSI-2 lane count and lane mapping and the
  parallel flags are taken from them only when the bus type is not guessed; in
  guess mode the CSI-2 lane count and the parallel flags start from 0.
- `bus.mipi_csi2.flags`: always overwritten; an absent `clock-noncontinuous`
  clears a preset `V4L2_MBUS_CSI2_NONCONTINUOUS_CLOCK`.
- Parallel `V4L2_MBUS_MASTER` and `V4L2_MBUS_SLAVE`: always rewritten from
  `slave-mode`; an absent property forces `V4L2_MBUS_MASTER`.
