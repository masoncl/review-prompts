- Locks: no lock taken in the walk is held from one step of the walk to the
  next; `find_or_add_dport()`, `add_port_attach_ep()` and `add_ep()` each take
  device locks and drop them before returning.
- `goto retry` is taken in two cases: `find_or_add_dport()` returned
  `ERR_PTR(-EAGAIN)`, or `add_port_attach_ep()` returned 0.
- Return codes, by helper:

| helper | return | meaning | walk |
|---|---|---|---|
| `find_or_add_dport()` | `ERR_PTR(-EAGAIN)` | dport was missing on an existing port and has just been added; endpoint not yet attached | restart |
| `add_port_attach_ep()` | `-EAGAIN` | parent port does not exist | `continue` one level up, no restart |
| `add_port_attach_ep()` | 0 | port and dport created and endpoint attached | restart |
| `add_port_attach_ep()` | 0 | `devm_cxl_create_port()` returned `-EAGAIN` (port already exists) or `-EBUSY` (dport already exists); nothing attached | restart |
| `add_port_attach_ep()` | `-ENXIO` | `grandparent(dport_dev)` is NULL or `&platform_bus`, with no port found below it | fail |
| `probe_dport()` | `-ENXIO` | port has no driver bound, or the driver has no `add_dport` | fail |
| `cxl_add_ep()` | `-ENXIO` | `port->dead` is set | fail, no retry |

- `-ENXIO` for an unbound parent or for a new port whose probe failed: comes
  from `probe_dport()`, which every dport creation in the walk goes through.
- `-EEXIST`: not returned by these helpers; "already there" is `-EBUSY`.
- End of walk: `is_cxl_host_bridge(dport_dev)` (NULL or `&platform_bus`)
  returns 0; a `dport_dev` whose `parent` is NULL returns `-ENXIO`.
- Restricted host, parent port: the endpoint's parent is the root port,
  reached through the root's `rch` dport; no host bridge port exists, since
  `add_host_bridge_uport()` in `drivers/cxl/acpi.c` returns before
  `devm_cxl_add_port()` for an `rch` dport.
- Restricted host, skipped: the whole walk, the registration of
  `cxl_detach_ep()`, every `cxl_add_ep()` and `cxl_gpf_port_setup()`.
- Restricted host, `struct cxl_ep`: none exists for the memdev; the loop in
  `devm_cxl_add_endpoint()` that sets `ep->next` runs zero times because the
  parent is the root.
