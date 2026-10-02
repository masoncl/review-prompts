- Hosts, from `port_to_host()` and `dport_to_host()` in
  `drivers/cxl/core/core.h`:

| object | devres host |
|---|---|
| root port | `port->uport_dev` |
| port whose parent is the root (host bridge port, RCH endpoint) | `parent->uport_dev` |
| any deeper port | `&parent->dev` |
| dport of the root | `port->uport_dev` |
| dport of any other port | `&port->dev` |
| switch and endpoint decoders | `&port->dev`, in `add_hdm_decoder()` |
| root decoders | the platform device, with `cxl_root_decoder_autoremove()` |

- Dport actions: grouped in a devres group whose id is the dport pointer;
  `free_dport()` is its first action, so `del_dport()` frees the dport.
- `__devm_cxl_add_dport()`: the only one of the port, dport and decoder
  registrations with a context check; `!host->driver` gives the "bad devm
  context" warning and `-ENXIO`.
- There is no cxl_dev_is_bound_to_driver() in this tree.
- `devm_cxl_add_port()`: has no `host->driver` check and does not compare
  `host` with `port_to_host()`; the caller is trusted for both.
- `unregister_port()`: asserts the lock of `port_to_host(port)`, not of the
  `host` that was passed in.
- Result of `devm_cxl_add_port()`: a valid port is returned even when the port
  driver's probe failed; `devm_cxl_add_endpoint()` tests
  `endpoint->dev.driver` afterwards.
- **Unsafe usage**: passing `devm_cxl_add_port()` a `host` other than what
  `port_to_host()` gives for the new port; `delete_endpoint()` and
  `delete_switch_port()` then call `devm_release_action()` on a device that
  does not hold the action.
  - Safe: `add_host_bridge_uport()` passes the root's `uport_dev` for a host
    bridge port.
  - Safe: `devm_cxl_create_port()` passes `&parent_port->dev` for a switch
    port.
  - Safe: `cxl_mem_probe()` passes `parent_port->uport_dev` when `dport->rch`
    is set, `&parent_port->dev` otherwise.
- **Potentially unsafe usage**: calling `devm_cxl_add_port()`, which has no
  `host->driver` test of its own.
  - Unsafe: when nothing shows that `host` is bound and locked; the actions
    stay on an unbound device, and `really_probe()` in `drivers/base/dd.c`
    fails its next probe with `-EBUSY`.
  - Safe: under the host's device lock after testing `host->driver`, as
    `cxl_mem_probe()` does.
  - Safe: from the host's own probe, as `cxl_acpi_probe()` does through
    `devm_cxl_add_root()` and `add_host_bridge_uport()`.
  - Safe: in `devm_cxl_create_port()`, under the parent's lock with a parent
    dport in hand; a non-root port's dports are devres of `&port->dev`, and
    `probe_dport()` returns `-ENXIO` for an unbound port.
- **Unsafe usage**: calling `devm_cxl_add_dport()` on a non-root port without
  `device_lock(&port->dev)`, or with no driver bound to the port;
  `add_dport()` and `find_dport()` assert the lock.
  - Safe: through `probe_dport()`, which asserts the lock and tests
    `port->dev.driver`.
  - Safe: on the root port from the platform driver's probe without the root
    port lock held, as `add_host_bridge_dport()` does;
    `cond_cxl_root_lock()` takes that lock itself.
