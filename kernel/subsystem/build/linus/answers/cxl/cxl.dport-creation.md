- `cxl_switch_port_probe()`: sets `port->nr_dports` to 0 and calls
  `read_cdat_data()`; it adds no dport, maps no register and creates no
  decoder.
- Callback: the `add_dport` member of `struct cxl_driver`; the port driver
  sets it to `cxl_port_add_dport()`.
- `probe_dport()` in `drivers/cxl/core/port.c`: the only caller of
  `add_dport`; reached only from the memdev walk, so a non-root port has only
  the dports that lie on some memdev's path.
- `probe_dport()`: asserts `device_lock(&port->dev)`; returns `-ENXIO` when no
  driver is bound, `-EBUSY` when `dport_dev` is already in `port->dports`.
- Order in `cxl_port_add_dport()`:
  1. Only when `port->nr_dports == 0`: `cxl_port_setup_regs()`, then
     `devm_cxl_switch_port_decoders_setup()`, then
     `devm_cxl_port_ras_setup()`.
  2. `devm_cxl_add_dport_by_dev()`; inside it `__devm_cxl_add_dport()` calls
     `devm_cxl_dport_ras_setup()` for a dport that is not `rch`.
  3. `cxl_switch_parse_cdat()`, then `cxl_port_update_decoder_targets()`.
- Port registers, decoders and port RAS: all set up before the first dport is
  in `port->dports`.
- `decoder_populate_targets()`: returns at `xa_empty(&port->dports)`, so
  decoders created in step 1 start with no targets filled.
- `cxl_port_update_decoder_targets()`: for each switch decoder child, takes
  `cxl_rwsem.region` for write and sets `cxlsd->target[i]` for the first
  `i < cxld->interleave_ways` where `cxld->target_map[i] == dport->port_id`.
- `devm_cxl_port_ras_setup()` and `devm_cxl_dport_ras_setup()`: return void, a
  mapping failure does not fail the dport; both are empty stubs without
  `CONFIG_CXL_RAS`.
