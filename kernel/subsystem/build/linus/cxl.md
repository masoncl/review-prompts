# CXL Subsystem

## Main structures

### Objects and how they relate

- Scope: besides class-code Type-3 expanders bound by `drivers/cxl/pci.c`,
  the core serves Type-2 (accelerator) drivers outside `drivers/cxl/`, for
  example `drivers/net/ethernet/sfc/efx_cxl.c`, through `include/cxl/cxl.h`.
- `struct cxl_memdev`: not Type-3 only. `devm_cxl_add_classdev()` and
  `devm_cxl_probe_mem()`, both in `drivers/cxl/mem.c`, create it; its parent is
  `cxlds->dev`, whichever driver owns that device.
- `is_cxl_memdev()`: matches two device types, `cxl_class_memdev_type` and
  `cxl_memdev_type`; only the first carries the memdev sysfs groups.
- `struct cxl_dev_state`: allocated devm on the parent device by
  `_devm_cxl_dev_state_create()`; the memdev only points at it, and
  `cxl_memdev_shutdown()` clears `cxlmd->cxlds`.
- `struct cxl_mailbox`: embedded in `struct cxl_dev_state` as `cxl_mbox`, not in
  `struct cxl_memdev_state`.
- `struct cxl_memdev_attach`: set by the memdev creator to say it cannot work
  without the CXL link. With `cxlmd->attach` set:
  - `cxl_mem_probe()` calls `attach->probe()` after the endpoint is added.
- Endpoint `struct cxl_port`: device child of the port that owns
  `parent_dport` (`cxl_port_alloc()` in `drivers/cxl/core/port.c`); the memdev
  is its `uport_dev`, never its parent.
- `struct cxl_dport` of the root port: created up front by
  `add_host_bridge_dport()` in `drivers/cxl/acpi.c`.
- Switch port right after probe: has no dports, no decoders, and no
  `struct cxl_hdm` drvdata; `cxl_port_add_dport()` sets those up when the first
  dport arrives.
- `struct cxl_region_ref`: one per region on every port from the endpoint port
  up to, not including, the root; the decoder it names also gets
  `cxld->region` set, switch decoders included (`cxl_rr_ep_add()` in
  `drivers/cxl/core/region.c`).
- Port reaping: `cxl_detach_ep()` removes a port that lost its last
  `struct cxl_ep` only if its parent is not the root; host-bridge ports stay.
- Partitions: ram or pmem is `enum cxl_partition_mode`; there is no
  enum cxl_decoder_mode. An endpoint decoder names its partition by index
  `part` into `cxlds->part[]` (`struct cxl_dpa_partition`).
- Locks: there is no cxl_region_rwsem or cxl_dpa_rwsem object; the region and
  DPA rwsems are `cxl_rwsem.region` and `cxl_rwsem.dpa` (`struct cxl_rwsem` in
  `drivers/cxl/core/core.h`).
- `port->regions`: changed under `cxl_rwsem.region` held for write, asserted
  in `cxl_port_attach_region()`; an entry is added to `dports` or `endpoints`
  under the port device lock, which `add_dport()` asserts and `add_ep()`
  takes.

## Where to look

### Core files

| Topic | File | Built under | Not here |
|---|---|---|---|
| pmem device a region spawns: `devm_cxl_add_pmem_region()`, `cxl_pmem_region_type` | `drivers/cxl/core/region_pmem.c` | `CONFIG_CXL_REGION` | `drivers/cxl/core/region.c` only calls it, from `cxl_region_probe()`. `struct cxl_pmem_region` is defined in `drivers/cxl/cxl.h`. |
| dax device a region spawns: `devm_cxl_add_dax_region()`, `cxl_dax_region_type` | `drivers/cxl/core/region_dax.c` | `CONFIG_CXL_REGION` | `drivers/cxl/core/region.c` only calls it, from `cxl_region_probe()`. `struct cxl_dax_region` is defined in `drivers/cxl/cxl.h`. |
| Restricted host (RCH) protocol errors: `cxl_handle_rdport_errors()`, `cxl_dport_map_rch_aer()`, `cxl_disable_rch_root_ints()` | `drivers/cxl/core/ras_rch.c` | `CONFIG_CXL_RAS`, the same symbol as `ras.o`; there is no CXL_RCH_RAS or PCIEAER_CXL symbol in this tree | `drivers/cxl/core/pci.c` holds none of it. The callers `devm_cxl_dport_rch_ras_setup()`, `cxl_error_detected()` and `cxl_cor_error_detected()` are in `drivers/cxl/core/ras.c`. The PCI side is `drivers/pci/pcie/aer_cxl_rch.c`, also built under `CONFIG_CXL_RAS`. |
| Platform address translation (ACPI PRM, DPA to SPA): `cxl_setup_prm_address_translation()` | `drivers/cxl/core/atl.c` | `CONFIG_CXL_ATL` (`def_bool y`, needs `CXL_REGION`, `ACPI_PRMT` and `AMD_NB`) | XOR interleave math is not here: `cxl_apply_xor_maps()` and `cxl_do_xormap_calc()` are in `drivers/cxl/acpi.c`. `drivers/cxl/core/region.c` only calls the installed `translation_setup_root` op. |
| Global region and address locks: definition of `cxl_rwsem` (members `region`, `dpa`) | `drivers/cxl/core/hdm.c` | `cxl_core-y` (always) | Not defined in `drivers/cxl/core/port.c` or `drivers/cxl/core/region.c`. `struct cxl_rwsem` and the extern are in `drivers/cxl/core/core.h`, not `drivers/cxl/cxl.h`. |
| `struct cxl_dev_state` | `include/cxl/cxl.h` | header | Not in `drivers/cxl/cxlmem.h`, which still defines `struct cxl_memdev_state` (embeds it as `cxlds`) and reaches the definition through `drivers/cxl/cxl.h`. |

## Locks

**Core locks**

- Root decoder's regions: the lock is `regions_lock`, a `struct mutex` in
  `struct cxl_root_decoder` (`drivers/cxl/cxl.h`). There is no range_lock in
  `drivers/cxl`.
- `regions_lock` protects: the `regions` xarray (regions by id) and the `dead`
  flag of the root decoder, and serializes region creation, deletion,
  auto-discovery and `kill_regions()`; it is taken only in
  `drivers/cxl/core/region.c`.
- `cxlmd->cxlds`: protected by `cxl_memdev_rwsem`, a static rwsem in
  `drivers/cxl/core/memdev.c`, not by `cxl_rwsem.region`.
- `cxl_memdev_rwsem` read side: `cxl_memdev_ioctl()` is the only holder; other
  code that dereferences `cxlmd->cxlds` does not take it.
- `cxl_memdev_rwsem` write side: also covers the `exclusive_cmds` bitmap of
  `struct cxl_mailbox`, see `set_exclusive_cxl_commands()`.
- `cxl_rwsem`: the object is defined in `drivers/cxl/core/hdm.c`, which is
  built without `CONFIG_CXL_REGION`; `drivers/cxl/core/region.c` is not.
- `mbox_mutex`: `cxl_pci_mbox_send()` in `drivers/cxl/pci.c` takes it with
  `mutex_lock()`; nothing in `drivers/cxl` calls `mutex_lock_io()`.
- `feat_mutex`: a second mutex in `struct cxl_mailbox`; `cxl_get_feature()`
  and `cxl_set_feature()` hold it across a multi-part transfer, so it nests
  outside `mbox_mutex`.
- `cxl_region_attach()`: has no lockdep assertion of its own;
  `cxl_port_attach_region()` asserts `cxl_rwsem.region` for write and
  `cxl_region_perf_data_calculate()` asserts `cxl_rwsem.dpa`.

**Lock ordering**

- Order, outermost first: memdev or port device lock, `cxlrd->regions_lock`,
  the region's own device lock, `cxl_rwsem.region`, `cxl_rwsem.dpa`.
- Region device lock inside `regions_lock`: `device_attach()` in
  `cxl_add_to_region()` and `device_del()` in `unregister_region()` both run
  with `regions_lock` held.
- Region device lock outside `cxl_rwsem.region`: `cxl_region_can_probe()` takes
  `cxl_rwsem.region` for read from `cxl_region_probe()`.
- `cxl_add_to_region()`: `regions_lock` is a `guard(mutex)` held to the end of
  the function, so everything from `cxl_find_region_by_range()` on runs under
  it.
- Calls under `regions_lock`, in order:
  - `cxl_find_region_by_range()`; its callback `match_region_by_range()` takes
    `cxl_rwsem.region` for read per child.
  - `construct_region()` when no region matched: `__create_region()` adds the
    region device without `cxl_rwsem.region`, then `__construct_region()` takes
    it for write.
  - `attach_target()` with `TASK_UNINTERRUPTIBLE`: `cxl_rwsem.region` write,
    then `cxl_rwsem.dpa` read; the return value is ignored.
  - `scoped_guard(rwsem_read, &cxl_rwsem.region)` to read `p->state`.
  - `device_attach()` on the region when the state is `CXL_CONFIG_COMMIT`, with
    no `cxl_rwsem` member held.
  - the `put_device()` from `__free(put_cxl_region)`, which runs before the
    mutex is released.

**Interruptible lock acquisition**

- Write side: `rwsem_write_kill` is `down_write_killable()`, so only a fatal
  signal ends the wait; the read side `rwsem_read_intr` and `mutex_intr` end on
  any signal.
- `TASK_INTERRUPTIBLE` passed to `attach_target()`: selects `rwsem_write_kill`
  in `__attach_target()`, a killable wait, not an interruptible one.
- `__attach_target()` killable branch: `cxl_rwsem.dpa` is still taken with an
  unconditional `guard(rwsem_read)` after the conditional region lock.
- `cxl_rwsem.dpa` for write: never taken conditionally; `__cxl_dpa_alloc()`,
  `cxl_dpa_free()` and `cxl_dpa_set_part()` in `drivers/cxl/core/hdm.c` use
  `guard(rwsem_write)` even when reached from `dpa_size_store()` and
  `mode_store()`.
- `cxl_rwsem.dpa` conditional holds: all are `rwsem_read_intr`, taken after
  `cxl_rwsem.region` with the same class, for example `cxl_inject_poison()`.
- Sysfs show handlers with an unconditional `guard(rwsem_read)`: for example
  `target_list_show()`, `decoders_committed_show()` and `dpa_resource_show()`
  in `drivers/cxl/core/port.c`.
- `regions_lock` in sysfs: `create_region_store()` and `delete_region_store()`
  take it with `ACQUIRE(mutex_intr, ...)`.
- `DETACH_INVALIDATE`: the only mode that makes `cxl_decoder_detach()` lock
  unconditionally, and `cxld_unregister()` in `drivers/cxl/core/port.c` is its
  only caller; `detach_target()` passes `DETACH_ONLY` and can return `-EINTR`.
- Other unconditional write holds of `cxl_rwsem.region`, apart from the second
  acquisition in `commit_store()`, are enumeration paths, for example
  `__construct_region()`, `decoder_populate_targets()` and
  `init_hdm_decoder()`; search `guard(rwsem_write)(&cxl_rwsem.region)` for the
  rest.
- **Potentially unsafe usage**: `device_release_driver()`, `device_del()` or
  `device_attach()` on a region while a guard is still in scope.
  - Unsafe: in the scope of `cxl_rwsem.region`, read or write, conditional or
    not; `cxl_region_can_probe()` takes that lock under the region's device
    lock.
  - Safe: after the scope has closed, as `cxl_decoder_detach()` does by putting
    each acquisition in its own braces, and as `commit_store()` does by locking
    inside `queue_reset()`.
  - Safe: in the scope of `regions_lock` alone, as `delete_region_store()` does
    through `unregister_region()`; `cxl_region_can_probe()` does not take
    `regions_lock`.
- **Unsafe usage**: a killable or interruptible acquisition on a path that
  cannot return or retry the error; on failure `cxl_decoder_detach()` returns
  before `__cxl_decoder_detach()` runs and the decoder stays attached.
  - Safe: `DETACH_INVALIDATE`, as `cxld_unregister()` passes.
  - Safe: `TASK_UNINTERRUPTIBLE`, as `cxl_add_to_region()` passes to
    `attach_target()`.
  - Safe: a plain `guard(rwsem_write)` after `queue_reset()` may have set
    `CXL_CONFIG_RESET_PENDING`, as the second acquisition in `commit_store()`.

## Device state and memdevs

**Device state structures**

- `devm_cxl_dev_state_create()` in `include/cxl/cxl.h`: wraps
  `_devm_cxl_dev_state_create()` (one leading underscore) in
  `drivers/cxl/core/memdev.c`.
- Driver structure: both requirements are build-time `static_assert()`s in the
  macro: the named member has type `struct cxl_dev_state`, and it is at
  offset 0.
- `to_cxl_memdev_state()` in `drivers/cxl/cxlmem.h`: tests `cxlds->type` only,
  then does `container_of()`; it cannot tell what structure really surrounds
  `cxlds`.
- **Unsafe usage**: passing `CXL_DEVTYPE_CLASSMEM` to
  `devm_cxl_dev_state_create()` with a driver structure other than
  `struct cxl_memdev_state`; `to_cxl_memdev_state()` then returns a non-NULL
  pointer to the wrong type.
  - Safe: `CXL_DEVTYPE_CLASSMEM` through `cxl_memdev_state_create()` in
    `drivers/cxl/core/mbox.c`.
  - Safe: a driver's own structure with `CXL_DEVTYPE_DEVMEM`, as
    `efx_cxl_init()` does.
- **Potentially unsafe usage**: dereferencing the result of
  `to_cxl_memdev_state()` with no NULL test.
  - Unsafe: on a path a `CXL_DEVTYPE_DEVMEM` memdev reaches, where the result
    is NULL; `cxl_mem_probe()` and endpoint decoder commit in
    `drivers/cxl/core/hdm.c` run for both types.
  - Safe: after a NULL test, as `cxl_memdev_poison_enable()` and
    `cxl_memdev_has_poison_cmd()` do.
  - Safe: in a sysfs attribute of `cxl_memdev_attribute_groups`, as
    `security_state_show()` does; `cxl_memdev_alloc()` gives a
    `CXL_DEVTYPE_DEVMEM` memdev `cxl_memdev_type`, which has no `.groups`.
  - Safe: in `__cxl_memdev_ioctl()`; `cxl_memdev_ioctl()` tests
    `cxlds->type == CXL_DEVTYPE_CLASSMEM` first and returns `-ENXIO`
    otherwise.
  - Safe: in `cxl_mem_get_poison()`; its only entry is
    `trigger_poison_list_store()`, and `cxl_poison_attr_visible()` hides that
    attribute when the result is NULL.
  - Safe: in `drivers/cxl/pci.c`, where the state came from
    `cxl_memdev_state_create()` in `cxl_pci_probe()`.
- `cxl_memdev_visible()`: hides only `numa_node`, and only without
  `CONFIG_NUMA`; it does not filter by device type.
- `to_cxl_memdev_state()` dereferences its argument: `cxlmd->cxlds` is NULL
  after `cxl_memdev_shutdown()`, so a path that can run after the parent
  unbinds must read `cxlmd->cxlds` under `cxl_memdev_rwsem` and test it first,
  as `cxl_memdev_ioctl()` does.

**Memdev creation**

- There is no devm_cxl_add_memdev() in this tree; a comment in
  `drivers/cxl/core/memdev.c` still names it.
- `__devm_cxl_add_memdev()` in `drivers/cxl/core/memdev.c`: the common helper;
  exported with `EXPORT_SYMBOL_FOR_MODULES()` to `cxl_mem` only, so another
  module cannot call it or pass its own `struct cxl_memdev_attach`.

| Device | Create state | Before registering | Register memdev | In-tree callers |
|---|---|---|---|---|
| class memory | `cxl_memdev_state_create()`; fails with `ERR_PTR(-ENOMEM)` | mailbox, identify, `cxl_dpa_setup()` | `devm_cxl_add_classdev()` (no descriptor) | `cxl_pci_probe()`, `cxl_mock_mem_probe()` |
| accelerator | `devm_cxl_dev_state_create()` with `CXL_DEVTYPE_DEVMEM`; fails with NULL | set `cxlds->media_ready`, `cxl_set_capacity()` | `devm_cxl_probe_mem()` (always a descriptor) | `efx_cxl_init()` in `drivers/net/ethernet/sfc/efx_cxl.c`, `cxl_mock_accel_probe()` in `tools/testing/cxl/test/accel.c` |

- `devm_cxl_add_classdev()` and `devm_cxl_probe_mem()`: both defined in
  `drivers/cxl/mem.c`; both return `ERR_PTR()` on failure, never NULL.
- `cxlds->media_ready`: nothing under `drivers/cxl/core` sets it, so an
  accelerator driver sets it itself; `cxl_mem_probe()` returns `-EBUSY` when
  it is false, which fails `devm_cxl_probe_mem()`.
- `devm_cxl_probe_mem()`: allocates a `struct cxl_attach_region` whose
  `.probe` is `cxl_memdev_attach_region()` in `drivers/cxl/core/region.c`;
  that is the only `struct cxl_memdev_attach` in the tree.
- `cxl_memdev_attach_region()`: creates no region; it fails with `-ENXIO`
  unless an endpoint decoder is already mapped to a committed region with one
  target.
- Without `CONFIG_CXL_REGION`: `cxl_memdev_attach_region()` is a stub that
  returns `-EOPNOTSUPP`, so `devm_cxl_probe_mem()` cannot succeed.
- Bind failure with a descriptor: `cxl_memdev_autoremove()` calls
  `cxl_memdev_unregister()` and returns `ERR_PTR(-ENXIO)` whatever
  `cxl_mem_probe()` returned; the test is `cxl_memdev_attach_failed()`, under
  the memdev device lock.
- `*hpa_range` from `devm_cxl_probe_mem()`: also written when
  `__devm_cxl_add_memdev()` fails, as `{ 0, -1 }` unless the callback reached
  its end; test the returned pointer, not the range.
- Detach with a descriptor: `detach_memdev()` calls
  `device_release_driver(cxlmd->dev.parent)`, which unbinds the accelerator's
  own driver; the memdev is then unregistered by the parent's devm action
  `cxl_memdev_unregister()`.
- Detach trigger: `schedule_detach()` in `drivers/cxl/port.c` is a devm action
  of the endpoint port, added by `cxl_endpoint_port_probe()`; it queues
  `detach_work` on `cxl_bus_wq` whenever that port is unbound, so the parent
  is unbound asynchronously.
- Region on detach: `endpoint_unregister_region()` is a devm action on the
  same endpoint port, so the region behind `hpa_range` is unregistered when
  the port unbinds and does not wait for the parent driver's remove callback.

## Ports and dports

**Port xarrays and port kinds**

- `port->dports`: keyed by `(unsigned long)dport->dport_dev`; look up with
  `cxl_find_dport_by_dev()`.
- `port_id`: not a key; `find_dport()` scans every dport, and `add_dport()`
  returns `-EBUSY` when the `port_id` is already in use.
- `port->endpoints`: keyed by `(unsigned long)ep->ep`, which is `&cxlmd->dev`;
  look up with `cxl_ep_load()` in `drivers/cxl/cxlmem.h`.
- `struct cxl_ep` entries for a memdev: held by the switch and host bridge
  ports above it, not by its endpoint port; `cxl_add_ep()` is called only from
  the enumeration walk.
- `port->regions`: holds `struct cxl_region_ref`, keyed by the
  `struct cxl_region` pointer; see `cxl_rr_load()` in
  `drivers/cxl/core/region.c`.
- `is_cxl_root()`: tests `port->uport_dev == port->dev.parent`; it does not
  look at what kind of device `uport_dev` is.
- `cxl_device_id()` in `drivers/cxl/core/port.c`: gives the root
  `CXL_DEVICE_ROOT` and every other port `CXL_DEVICE_PORT`.
- Root port: no driver in this tree registers with `CXL_DEVICE_ROOT`, so its
  `dev.driver` stays NULL.

**Port enumeration**

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

**Downstream port creation**

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

**Port removal**

- `delete_endpoint()` and `cxl_detach_ep()`: separate devres actions on
  `&cxlmd->dev`; neither calls the other.
- Order on memdev unbind: `delete_endpoint()` is registered later, so it runs
  first; the endpoint port is gone before the memdev is detached from the
  ports above.
- `cxl_detach_ep()`: visits depths `cxlmd->depth - 1` down to 1;
  `cxlmd->depth` is -1 from `cxl_memdev_alloc()` until
  `cxl_endpoint_autoremove()` writes it, and until then the action visits no
  port.
- `unregister_port()`: sets `port->dead` under the lock of
  `port_to_host(port)`, which it asserts; it does not hold the port's own
  lock.
- `port->dead` is read in three places: `add_ep()` (returns `-ENXIO`),
  `cxl_detach_ep()` (no second reap) and `delete_endpoint()` (skips the
  release actions).
- `cxl_port_add_dport()` and `probe_dport()`: do not test `port->dead`;
  `probe_dport()` tests `port->dev.driver`.
- Locks in `cxl_detach_ep()`: `device_lock(&parent_port->dev)`, then
  `device_lock(&port->dev)`; the parent lock is the parent port's own device
  even when the parent is the root.
- `cxl_detach_ep()`: takes no `cxl_rwsem` lock itself.
- Port lock: dropped before `delete_switch_port()`; the parent lock is held
  through it, as `unregister_port()` asserts.
- There is no reap_dports() here; `del_dports()` in
  `drivers/cxl/core/port.c` releases each dport's devres group with
  `del_dport()`, under the port lock, before `delete_switch_port()`.
- `delete_switch_port()`: calls `devm_release_action()` on `port->dev.parent`;
  that equals `port_to_host(port)` only because `cxl_detach_ep()` tests
  `!is_cxl_root(parent_port)` first.
- `devm_release_action()`: warns when the action is not on that device; the
  `->driver` and `!dead` tests are what keep it from being called after the
  host's devres already ran.
- `detach_memdev()`: unbinds the memdev, or the memdev's parent when
  `cxlmd->attach` is set.
- `cxl_mem_probe()`: returns `-EBUSY` while `cxlmd->detach_work` is pending.

**Devres host choice**

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

## Decoders and device addresses

**Decoder kinds**

- `struct cxl_endpoint_decoder`: has no mode or size field; the partition is
  the index `part`, the size comes from `cxl_dpa_size()`.
- `struct cxl_root_decoder`: embeds `struct cxl_switch_decoder` as its member
  `cxlsd`.
- `is_switch_decoder()`: also true for a root decoder, so
  `to_cxl_switch_decoder()` accepts one; code that must exclude root decoders
  tests `is_root_decoder()` as well.
- `reset` in `struct cxl_decoder`: returns `void`; only `commit` returns `int`.
- `cxl_decoder_commit()` and `cxl_decoder_reset()`: `static` in
  `drivers/cxl/core/hdm.c`, reachable only through the pointers.
- `init_hdm_decoder()`: the only core code that sets both callbacks to
  functions; `cxl_decoder_init()` in `drivers/cxl/core/port.c` leaves them
  NULL.
- Callbacks stay NULL on: root decoders, the passthrough decoder from
  `devm_cxl_add_passthrough_decoder()`, and DVSEC-emulated endpoint decoders,
  where `cxl_setup_hdm_decoder_from_dvsec()` sets NULL and marks the decoder
  `CXL_DECODER_F_ENABLE | CXL_DECODER_F_LOCK`.
- **Unsafe usage**: calling `cxld->commit` or `cxld->reset` without a NULL
  test on a decoder that may be root, passthrough or DVSEC-emulated.
  - Safe: test first, as `commit_decoder()` in `drivers/cxl/core/region.c`
    does; it accepts a NULL `commit` only for a switch decoder with
    `nr_targets` of at most 1, anything else is a warning and `-ENXIO`.
- Root decoder callbacks: `struct cxl_rd_ops ops`, embedded by value, with
  `hpa_to_spa` and `spa_to_hpa`.
- `__cxl_parse_cfmws()` in `drivers/cxl/acpi.c`: sets both members to
  `cxl_apply_xor_maps()` after `cxl_root_decoder_alloc()`, only for
  `ACPI_CEDT_CFMWS_ARITHMETIC_XOR`; otherwise both stay NULL.
- Callers of the root ops: `cxl_dpa_to_hpa()` and
  `region_offset_to_dpa_result()` in `drivers/cxl/core/region.c`; each tests
  the member for NULL and treats NULL as HPA equal to SPA.
- `qos_class` in `struct cxl_root_decoder`: an `int` copied from the CFMWS,
  not a callback; the `qos_class` callback is in `struct cxl_root_ops` on
  `struct cxl_root`, next to `translation_setup_root`.

**Device address partitions**

- `struct cxl_dev_state` and `struct cxl_dpa_partition`: defined in
  `include/cxl/cxl.h`; `struct cxl_dpa_info` with its inner
  `struct cxl_dpa_part_info` is in `drivers/cxl/cxlmem.h`.
- There is no to_ram_res() or to_pmem_res() here; code reads
  `cxlds->part[i].res` directly.
- `cxl_ram_size()`, `to_ram_perf()` and `to_pmem_perf()`: `static` in
  `drivers/cxl/core/memdev.c`; only `cxl_pmem_size()` is shared, in
  `drivers/cxl/cxlmem.h`.
- RAM helpers `cxl_ram_size()` and `to_ram_perf()`: look only at `part[0]`;
  the pmem helpers search every index by mode.
- `add_part()` in `drivers/cxl/core/memdev.c`: drops a zero-size partition, so
  a pmem-only device has pmem at index 0.
- `cxl_mem_dpa_fetch()`: defined in `drivers/cxl/core/memdev.c`.
- `cxl_set_capacity()`: the entry for a device without a mailbox; it builds
  one RAM partition and calls `cxl_dpa_setup()`.
- `cxl_dpa_setup()`: requires each partition to start at the previous end
  plus one, else `-EINVAL`; a gap fails as well as an overlap.
- `cxl_dpa_setup()` called when `cxlds->nr_partitions` is already non-zero:
  returns `-EBUSY`.
- `cxl_dpa_set_part()`: its only busy test is `CXL_DECODER_F_ENABLE`; it does
  not look at `cxled->dpa_res` or `cxled->cxld.region`.
- `cxl_dpa_set_part()` errors: `-EBUSY` enabled, `-EINVAL` no partition of
  that mode, `-ENXIO` partition of zero size.
- `cxled->part` is `-1`: after `cxl_endpoint_decoder_alloc()`, after
  `__cxl_decoder_detach()` with `DETACH_INVALIDATE` on a decoder that had a
  region, and after `__cxl_dpa_reserve()` when no partition contains the
  reserved range.
- **Unsafe usage**: indexing `cxlds->part[cxled->part]` without testing
  `cxled->part >= 0`, including on a decoder that has `dpa_res`.
  - Safe: test first, as `cxl_region_attach()` (`-ENODEV`),
    `construct_region()` (`-EBUSY`), `cxled_get_dpa_perf()` and `mode_show()`
    do; the last reads `part` once with `READ_ONCE()` because it does not
    hold `cxl_rwsem.dpa`.

**Device address allocation order**

- There is no cxled_dpa_next() here; `__cxl_dpa_alloc()` in
  `drivers/cxl/core/hdm.c` places the allocation after the last child of the
  partition resource.
- `port->hdm_end`: set to -1 in `cxl_port_alloc()`, then changed only in
  `__cxl_dpa_reserve()` and `__cxl_dpa_release()`, both of which assert
  `cxl_rwsem.dpa` held for write.
- Order test: on the decoder id only; `__cxl_dpa_reserve()` and
  `cxl_dpa_free()` do not look at HPA.
- Skip in `__cxl_dpa_alloc()`: non-zero only for a partition index above 0;
  it runs from the end of the last allocation in the nearest lower partition
  that has one (or from the start of partition 0) to the start of the chosen
  partition.
- Within one partition `__cxl_dpa_alloc()` never produces a skip.
- Skip at enumeration: `init_hdm_decoder()` reads it from the skip registers
  and reserves at a running base that sums the size and skip of the lower
  decoders; no DPA base is read from hardware.
- Skip resource: requested under the decoder's own name and split at
  partition boundaries by `__adjust_skip()`; it lies below `dpa_res->start`.
- Capacity under a skip: a later allocation in that lower partition gets
  `-ENOSPC` until the skipping decoder is freed.
- `-EBUSY` from `__cxl_dpa_alloc()`: `cxled->cxld.region` set,
  `CXL_DECODER_F_ENABLE` set, or `cxled->part` negative.
- `-EBUSY` from `__cxl_dpa_reserve()`: `dpa_res` already set, id not
  `hdm_end + 1`, or the skip or the range conflicts in `cxlds->dpa_res`.
- `__cxl_dpa_reserve()` with zero length: `-EINVAL`.
- `dpa_size_store()` in `drivers/cxl/core/port.c`: rejects a size not aligned
  to `SZ_256M`, then calls `cxl_dpa_free()` before `cxl_dpa_alloc()`, so a
  resize fails with `-EBUSY` on any decoder that is not `hdm_end`.

**Decoder commit order**

- `port->commit_end` and `CXL_DECODER_F_ENABLE` in `cxl_decoder_commit()`:
  changed only after `cxld_await_commit()` returns 0; a failed commit leaves
  both as they were and there is no decrement.
- `cxld_await_commit()`: clears `CXL_HDM_DECODER0_CTRL_COMMIT` only when the
  hardware reports `CXL_HDM_DECODER0_CTRL_COMMIT_ERROR` (`-EIO`); on
  `-ETIMEDOUT` it clears nothing.
- `cxl_decoder_reset()` on a decoder with `CXL_DECODER_F_LOCK`: returns before
  touching hardware, flags or `commit_end`.
- `cxl_decoder_reset()` with `id != commit_end`: logs with `dev_dbg()`, clears
  the registers and `CXL_DECODER_F_ENABLE`, leaves `commit_end` unchanged.
- Out-of-order reset record: there is no mask; the hole is a decoder with id
  at or below `commit_end` and `CXL_DECODER_F_ENABLE` clear.
- While a hole exists: `match_free_decoder()` in `drivers/cxl/core/region.c`
  returns no switch decoder for that port, so a region without
  `CXL_REGION_F_AUTO` cannot route through it.
- `cxl_port_commit_reap()`: defined in `drivers/cxl/core/hdm.c`; called
  before the caller clears `CXL_DECODER_F_ENABLE` on the top decoder.
- Lock: `cxl_num_decoders_committed()` asserts `cxl_rwsem.region` held in any
  mode; `cxl_port_commit_reap()` asserts it held for write.
- `cxl_region_decode_reset()`: takes targets last to first; for each target it
  resets from the port below the root down, the endpoint decoder last.
- `cxl_region_decode_commit()`: the opposite, endpoint decoder first.
- `init_hdm_decoder()`: a firmware-committed decoder whose id is not
  `commit_end + 1` fails enumeration with `-ENXIO`.
- Sanitize test in `cxl_decoder_commit()`: skipped when
  `to_cxl_memdev_state()` returns NULL, which is any device that is not
  `CXL_DEVTYPE_CLASSMEM`.
- `cxl_mem_sanitize()` in `drivers/cxl/core/mbox.c`: holds `cxl_rwsem.region`
  for read and returns `-EBUSY` if the endpoint has a committed decoder or
  the memdev has no driver bound.

## Regions

**Region configuration states**

- `size` write (`alloc_hpa()`): the only store that moves `CXL_CONFIG_IDLE` to
  `CXL_CONFIG_INTERLEAVE_ACTIVE`; `set_interleave_ways()` and
  `set_interleave_granularity()` never write `p->state`.
- `alloc_hpa()`: returns `-ENXIO` unless ways, granularity and (for
  `CXL_PARTMODE_PMEM`) the uuid are already set.
- `uuid_store()` and `free_hpa()` (size 0): the state test is
  `p->state >= CXL_CONFIG_ACTIVE` (`-EBUSY`), so both work in
  `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `uuid_store()`: writing the uuid already set returns success before the
  state test.
- `store_targetN()` with an empty write: `__cxl_decoder_detach()` moves any
  state `> CXL_CONFIG_ACTIVE` (`CXL_CONFIG_COMMIT` or
  `CXL_CONFIG_RESET_PENDING`) to `CXL_CONFIG_ACTIVE`, then
  `CXL_CONFIG_ACTIVE` to `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `commit_store()` with 0: the first test is `CXL_REGION_F_LOCK`, read with no
  lock held; set returns `-EPERM` before `queue_reset()`.
- `queue_reset()` on a region below `CXL_CONFIG_COMMIT`: returns 0 and leaves
  the state alone; `device_release_driver()` still runs and the write succeeds.
- `commit_store()` locks: `queue_reset()` takes `cxl_rwsem.region` killable;
  after the release it is taken with `guard(rwsem_write)`, which cannot fail.
- After the release nothing can fail: `cxl_region_decode_reset()` returns void
  and the state becomes `CXL_CONFIG_ACTIVE` whenever it is still
  `CXL_CONFIG_RESET_PENDING`.
- **Unsafe usage**: moving `p->state` below `CXL_CONFIG_COMMIT` and leaving
  the region driver bound.
  - Unsafe: `cxl_region_perf_attrs_callback()` and
    `cxl_region_calculate_adistance()` read `cxlr->params.res` with no lock
    while the driver is bound.
  - Safe: change the state under the write lock, drop the lock, then call
    `device_release_driver()`, as `commit_store()` does, and as
    `cxl_decoder_detach()` does when `__cxl_decoder_detach()` returns the
    region; `cxl_region_can_probe()` refuses a rebind below
    `CXL_CONFIG_COMMIT`.

**Region flags**

- There is no CXL_REGION_F_INCOHERENT in this tree; `__commit()` and
  `cxl_region_decode_reset()` call `cxl_region_invalidate_memregion()` with no
  flag test other than `CXL_REGION_F_LOCK` in the latter.

| Flag | Stops | Set by | Cleared by |
|---|---|---|---|
| `CXL_REGION_F_AUTO` | attach with an explicit position or a decoder not in `CXL_DECODER_STATE_AUTO` (`-EINVAL`); `cxl_region_teardown_targets()` | `__construct_region()` | nothing |
| `CXL_REGION_F_NEEDS_RESET` | `cxl_region_can_probe()` (`-ENXIO`) | `cxl_region_decode_reset()`, after each decoder | end of the same function; `cxl_region_setup_flags()` for a locked decoder |
| `CXL_REGION_F_LOCK` | write of 0 to `commit`; all of `cxl_region_decode_reset()` | `cxl_region_setup_flags()` | nothing |
| `CXL_REGION_F_NORMALIZED_ADDRESSING` | `cxl_dpa_to_hpa()` (returns `ULLONG_MAX`); `cxl_region_setup_poison()` debugfs files | `cxl_region_setup_flags()` | nothing |

- `cxl_region_setup_flags()`: called from `cxl_region_alloc()` with the root
  decoder, and from `cxl_port_attach_region()` with each port's decoder.
- `CXL_REGION_F_LOCK` sources: `CXL_DECODER_F_LOCK` on any of those decoders,
  or `cxlmd->attach` set on the endpoint decoder's memdev.
- Root decoder with `CXL_DECODER_F_LOCK` (`ACPI_CEDT_CFMWS_RESTRICT_FIXED`):
  every region under it is locked from allocation, user-created ones too.
- `CXL_REGION_F_NORMALIZED_ADDRESSING` source:
  `CXL_DECODER_F_NORMALIZED_ADDRESSING`, which `cxl_prm_setup_root()` in
  `drivers/cxl/core/atl.c` sets on the endpoint decoder together with
  `CXL_DECODER_F_LOCK`.
- Auto region: flags from the endpoint and switch decoders appear only when
  the last target arrives, because `cxl_port_attach_region()` first runs then.
- `CXL_REGION_F_LOCK` does not stop a write of 1 to `commit` or a detach; a
  detach still lowers `p->state` while the hardware stays programmed.
- `CXL_REGION_F_AUTO` stays set after userspace resets the region; `__commit()`
  does not test it and programs the decoders normally.
- `CXL_REGION_F_NEEDS_RESET`: the loop in `cxl_region_decode_reset()` has no
  early exit, and all three callers hold `cxl_rwsem.region` for write, so
  `cxl_region_can_probe()` (read lock) does not see it set.

**Attaching and detaching targets**

- `check_interleave_cap()` on the endpoint decoder: the first test in
  `cxl_region_attach()`, for auto regions too.
- `cxled->part < 0`: `-ENODEV`, before the mode comparison.
- Size test: `resource_size(cxled->dpa_res) * p->interleave_ways +
  p->cache_size` must equal `resource_size(p->res)`.
- `cxl_region_attach()` does not compare the endpoint decoder's `hpa_range`
  with the region; the user path overwrites it from `p->res`.
- `cxl_region_attach_position()`: the endpoint's host-bridge dport must equal
  `cxlrd->cxlsd.target[pos % iw]`, `iw` being the root decoder's ways.
- Walk in `cxl_region_attach_position()`: starts at the endpoint port itself,
  where `cxl_port_pick_region_decoder()` returns the endpoint decoder.
- `cxl_rr_ep_add()`: sets `cxld->region` and takes a region device reference
  per decoder; `cxl_rr_free_decoder()` drops both when the ref is freed.
- Detach walk: `cxl_port_detach_region()` from the endpoint port up to the
  root.
- Detach from `> CXL_CONFIG_ACTIVE`: resets the decoders of all
  `p->interleave_ways` targets, not only the one leaving.
- Detach with `CXL_REGION_F_LOCK`: no hardware reset; with
  `CXL_REGION_F_AUTO`: `cxl_region_teardown_targets()` does nothing.
- Detach leaves `p->res`, ways, granularity and `cxled->pos` as they were.
- `device_release_driver()`: called whenever `__cxl_decoder_detach()` returns
  a region, whatever the state was.
- Rebind: `__commit()` does not bind the region driver; the only
  `device_attach()` in `drivers/cxl/core/region.c` is in
  `cxl_add_to_region()`, and `cxl_bus_rescan()` in `drivers/cxl/core/port.c`
  calls `device_attach()` on every device on the bus.

**Detach modes**

- There is no cxl_decoder_kill_region() here; `cxld_unregister()` in
  `drivers/cxl/core/port.c` is the `DETACH_INVALIDATE` caller, for endpoint
  decoders.
- `cxl_endpoint_decoder_release()`: the device release callback; it does not
  detach.
- Lock: `cxl_decoder_detach()` takes `cxl_rwsem.region` itself in both modes;
  no caller holds it.
- `DETACH_INVALIDATE` invalidates the decoder, not the region: it sets
  `cxled->part = -1` and, apart from the locking, nothing else differs.
- Lookup by decoder with `cxled->cxld.region` NULL: calls
  `cxl_cancel_auto_attach()`, which removes a staged decoder from
  `p->targets[]`; no driver release.
- Return value: 0 also when no target was found.
- Root decoder teardown: `kill_regions()` calls `unregister_region()`, which
  detaches each position through `detach_target()`, so with `DETACH_ONLY`.

**Firmware-programmed regions**

- `enum cxl_decoder_state` has three values; `CXL_DECODER_STATE_AUTO_STAGED`
  is the third.

| Transition | Where | When |
|---|---|---|
| to `CXL_DECODER_STATE_AUTO` | `init_hdm_decoder()`, `cxl_setup_hdm_decoder_from_dvsec()` | committed endpoint decoder, after DPA is reserved |
| `CXL_DECODER_STATE_AUTO` to `CXL_DECODER_STATE_AUTO_STAGED` | `cxl_region_attach_auto()` | decoder put in the first free `p->targets[]` slot |
| `CXL_DECODER_STATE_AUTO_STAGED` to `CXL_DECODER_STATE_AUTO` | `cxl_rr_ep_add()` | the endpoint decoder's `cxld->region` is set |
| `CXL_DECODER_STATE_AUTO_STAGED` to `CXL_DECODER_STATE_AUTO` | `cxl_region_remove_target()` | staged decoder unregistered with no `cxld->region` |
| to `CXL_DECODER_STATE_MANUAL` | `cxl_decoder_reset()` | after the hardware reset |

- `cxl_region_sort_targets()`: writes `cxled->pos` and reorders
  `p->targets[]`, never the state.
- `cxl_decoder_reset()`: returns early without `CXL_DECODER_F_ENABLE` or with
  `CXL_DECODER_F_LOCK`, and then leaves the state alone.
- Failed assembly on the last target: `cxl_region_attach()` returns the error,
  targets stay in `p->targets[]`, the region stays
  `CXL_CONFIG_INTERLEAVE_ACTIVE`.
- `discover_region()`: skips decoders without `CXL_DECODER_F_ENABLE` or not in
  `CXL_DECODER_STATE_AUTO`; it has no DPA test.
- Lookup: `cxl_find_region_by_range()`; there is no cxl_region_find() here.
- `match_region_by_range()`: matches through `spa_maps_hpa()`, which adds
  `p->cache_size` to the region start.
- Range, ways and granularity: taken from `struct cxl_region_context`, which
  the root's `translation_setup_root` op may rewrite in
  `get_cxl_root_decoder()`.
- `attach_target()` result in `cxl_add_to_region()`: ignored; the function
  returns 0 when the attach failed.

**Extended linear cache size**

- There is no cxl_acpi_set_cache_size() here;
  `cxl_setup_extended_linear_cache()` in `drivers/cxl/acpi.c` is the caller.
- `resource_contains()` in the helper: applied to `target->memregions` itself,
  which `alloc_target()` sets to span 0 to -1; its children are not walked.
- Match: decided by `nid` (through `node_to_pxm()` and `find_mem_target()`),
  the cache address mode and the resource type, not by `start` and `end`.
- **Unsafe usage**: passing a resource with no type flags or with
  `IORESOURCE_UNSET`.
  - Unsafe: `resource_contains()` is false for every cache, the helper returns
    0 with a size of 0, and the cache is lost silently.
  - Safe: `DEFINE_RES_MEM(start, size)`, as
    `cxl_setup_extended_linear_cache()` does; `alloc_target()` gives
    `target->memregions` the type `IORESOURCE_MEM`.
- **Unsafe usage**: reading the `cache_size` output after a non-zero return.
  - Unsafe: on `-ENOENT`, and in the `-EOPNOTSUPP` stub without
    `CONFIG_ACPI_HMAT`, the helper never writes `*cache_size`.
  - Safe: return on a non-zero result before reading the output, as
    `cxl_setup_extended_linear_cache()` does; it presets
    `cxlrd->cache_size = 0`, not the local it passes.
- Any non-zero return: `cxlrd->cache_size` stays 0 with no message.
- Non-zero size: must equal half of the root decoder's range; a mismatch
  warns and stores 0.
- `cxl_setup_extended_linear_cache()` returns void; the root decoder is added
  either way.
- `p->cache_size`: written only by `cxl_extended_linear_cache_resize()`, from
  `__construct_region()`; regions sized through `alloc_hpa()` keep 0.
- `cxl_extended_linear_cache_resize()` failure: `__construct_region()` only
  warns and builds the region with `p->cache_size` 0.
- `extended_linear_cache_size` attribute: hidden by `cxl_region_visible()`
  when `p->cache_size` is 0.
- `cxl_region_probe()`: registers the MCE notifier only when `p->cache_size`
  is non-zero.
- Other users: search `cache_size` under `drivers/cxl/core`; for example
  `spa_maps_hpa()` and `validate_region_offset()`.

## Mailbox

**Sending a mailbox command**

- `cxl_internal_send_cmd()` in `drivers/cxl/core/mbox.c`: has no NULL test of
  `cxl_mbox`; the `-EINVAL` NULL test is in `cxl_mailbox_init()`.
- `-E2BIG`: returned by `cxl_internal_send_cmd()` itself, before `mbox_send` is
  called, when `size_in` or `size_out` exceeds `payload_size`.
- `__cxl_pci_mbox_send_cmd()` in `drivers/cxl/pci.c`: its error returns are
  `-EBUSY`, `-EINVAL` and `-ETIMEDOUT`; it does not return `-ENXIO`.
- Device codes: `CMD_CMD_RC_TABLE` in `drivers/cxl/cxlmem.h` maps every error
  code to `-ENXIO`, including `CXL_MBOX_CMD_RC_BUSY`, except
  `CXL_MBOX_CMD_RC_PADDR` (`-EFAULT`) and `CXL_MBOX_CMD_RC_POISONLMT`
  (`-EBUSY`).
- `-EBUSY` from `cxl_internal_send_cmd()`: either the transport refused the
  command or the device reported `CXL_MBOX_CMD_RC_POISONLMT`.
- `min_out == 0` with a nonzero entry `size_out`: the reply must fill the whole
  entry `size_out`, else `-EIO`.
- Entry `size_out == 0`: the only successful case with no output size check.
- `size_out` on return: meaningful only when the result is 0 or `-EIO`; the PCI
  transport leaves the entry value in place on a transport error and on a
  device error.
- **Unsafe usage**: a `mbox_send` implementation that returns `-EIO`.
  - Unsafe: `cxl_internal_send_cmd()` hits `WARN_ONCE()` and returns `-ENXIO`;
    `cxl_xfer_log()` takes `-EIO` to mean a short log and reads `size_out`.
  - Safe: return 0 and put the device code in `return_code`, or return another
    errno, as `__cxl_pci_mbox_send_cmd()` does.
- `handle_mailbox_cmd_from_user()`: calls `mbox_send` directly, not
  `cxl_internal_send_cmd()`, so the `-E2BIG` test, the `-EIO` translation, the
  `min_out` test and the device-code conversion do not apply; the device code
  goes to user space in `retval`.

**Background commands**

- Background test: `return_code == CXL_MBOX_CMD_RC_BACKGROUND`, read from the
  status register after the doorbell clears; the opcode is not consulted, and
  there is no cxl_is_background_cmd() or mbox_poll_timeout in this tree.
- `mbox_wait`: a `struct rcuwait`, not a completion; the waiter uses
  `rcuwait_wait_event_timeout()` and `cxl_pci_mbox_irq()` uses
  `rcuwait_wake_up()`.
- With or without an interrupt: the same loop runs; the interrupt only ends a
  pass early.
- `cxl_mbox_cmd_ctor()`: sets neither `poll_count` nor `poll_interval_ms`, so a
  command other than `CXL_MBOX_OP_SANITIZE` from the ioctl path that goes to
  the background gets no wait and `-ETIMEDOUT` unless the status register
  already shows 100 percent.

**Sanitize in progress**

- Asynchronous branch: taken only for `CXL_MBOX_OP_SANITIZE`;
  `CXL_MBOX_OP_SECURE_ERASE` takes the synchronous wait like any other opcode.
- `poll_dwork` delay: 1 second for the first run, then `poll_tmo_secs + 10`
  seconds; `CXL_MAILBOX_TIMEOUT_MS` is the doorbell timeout only.
- Mailbox gate: `poll_tmo_secs > 0`, not `sanitize_active`; it lasts until
  `cxl_mbox_sanitize_work()` sets it to 0, and `CXL_MBOX_OP_GET_HEALTH_INFO`
  passes it.
- `cxl_decoder_commit()` in `drivers/cxl/core/hdm.c`: returns `-EBUSY` for an
  endpoint decoder while `sanitize_active` is set; `cxl_mem_probe()` makes no
  such test.
- `cxl_decoder_commit()`: reads `sanitize_active` without `mbox_mutex`; it runs
  under `cxl_rwsem.region` held for write by `__commit()`, and
  `cxl_mem_sanitize()` starts a sanitize under the same rwsem held for read.
- `cxl_pci_mbox_irq()` for a sanitize: only reschedules `poll_dwork` with delay
  0; `cxl_mbox_sanitize_work()` clears the state and notifies, with or without
  an interrupt.
- `sanitize_node` NULL: the interrupt does not reschedule the work and no
  notification is sent; it is NULL when `devm_cxl_sanitize_setup_notifier()`
  found `CXL_SEC_ENABLED_SANITIZE` clear, and after
  `sanitize_teardown_notifier()`.

**Commands from user space**

- `cxl_validate_cmd_from_user()`: takes a `const struct cxl_send_command *`,
  returns `int`, and fills a `struct cxl_mbox_cmd`; there is no
  struct cxl_memdev_command in this tree.
- `flags` in `cxl_to_mem_cmd()`: bits outside `CXL_MEM_COMMAND_FLAG_MASK` give
  `-EINVAL`; bits inside the mask pass.
- `CXL_CMD_FLAG_FORCE_ENABLE`: not looked at during validation, which tests
  only `enabled_cmds`; `cxl_enumerate_cmds()` sets those bits in
  `enabled_cmds`.
- `out.size > payload_size`: `-EINVAL` only in `cxl_to_mem_cmd_raw()`; for
  other commands `cxl_mbox_cmd_ctor()` allocates
  `min(out.size, payload_size)`, for fixed and variable sizes alike.
- `cxl_payload_from_user_allowed()` false: `-EBUSY` from `cxl_mbox_cmd_ctor()`,
  the same errno as an exclusive command.
- `cxl_to_mem_cmd_raw()`: tests none of `flags`, `in.rsvd`, `out.rsvd`,
  `enabled_cmds` or `exclusive_cmds`; an opcode the kernel owns is kept from
  the raw path only by `cxl_mem_raw_command_allowed()`
  (`cxl_disabled_raw_commands[]` and `cxl_is_security_command()`), and
  `cxl_raw_allow_all` bypasses both.
- Raw path: has no `CAP_SYS_RAWIO` test and no `add_taint()` call of its own;
  an accepted raw command triggers `dev_WARN_ONCE()`, whose `TAINT_WARN` is
  the only taint.
- `enabled_cmds` and `exclusive_cmds`: fields of `struct cxl_mailbox` in
  `include/cxl/mailbox.h`.
- `set_exclusive_cxl_commands()` in `drivers/cxl/core/memdev.c`: holds
  `cxl_memdev_rwsem` for write, not `mbox_mutex`; its only caller is
  `cxl_nvdimm_probe()` in `drivers/cxl/pmem.c`, with the bitmap that
  `cxl_pmem_init()` fills.

## The mock build and other builds

**Mock build and wrapped symbols**

- `dax_hmem`: also rebuilt by `tools/testing/cxl/Kbuild`, from
  `drivers/dax/hmem/hmem.c`, and linked with the same `ldflags-y`.
- `--wrap=walk_hmem_resources`, `--wrap=region_intersects`,
  `--wrap=region_intersects_soft_reserve`: their only callers among the
  rebuilt sources are in `drivers/dax/hmem/hmem.c`.
- `cxl_mock_accel` in `tools/testing/cxl/test/accel.c`: a platform driver for
  `"cxl_type2_accel"` devices (`CXL_DEVTYPE_DEVMEM`); it stands in for no
  driver under `drivers/cxl/`.
- There is no mock_pmem.c; `cxl_pmem` is rebuilt from `drivers/cxl/pmem.c`
  and `drivers/cxl/security.c`.
- HDM decoder setup is redirected at `devm_cxl_switch_port_decoders_setup()`
  and `devm_cxl_endpoint_decoders_setup()`; `devm_cxl_setup_hdm()`,
  `devm_cxl_enumerate_decoders()` and `devm_cxl_add_passthrough_decoder()` are
  `static` in `drivers/cxl/core/hdm.c` and are not wrapped.
- Dport enumeration is redirected at `devm_cxl_add_dport_by_dev()`, with a
  plain `--wrap=` line; there is no devm_cxl_port_enumerate_dports() here.
- There is no DECLARE_TESTABLE() in this tree, and no `exports.h` under
  `tools/testing/cxl/` or `drivers/cxl/`; `--wrap` and `__mock` are the only
  two redirection mechanisms.
- `tools/testing/cxl/cxl_core_exports.c`: holds no trampoline; it only adds an
  `EXPORT_SYMBOL_NS_GPL()` for `cxl_num_decoders_committed()`, which
  `drivers/cxl/core/port.c` does not export.
- `CXL_TEST_ENABLE`: defined by Kbuild, tested by no source file.
- `__mock`: `static` by default (`drivers/cxl/cxl.h`), `__weak` in the mock
  build; `to_cxl_host_bridge()` in `drivers/cxl/acpi.c` is the only `__mock`
  function, and `tools/testing/cxl/mock_acpi.c`, linked into the rebuilt
  `cxl_acpi`, supplies the strong copy.
- Fallback: the wrapper calls `<name>()` itself; no `__real_` name is used.
  `mock.c` is built by `tools/testing/cxl/test/Kbuild`, which sets no
  `ldflags-y`.
- Wrapper exports: `EXPORT_SYMBOL_NS_GPL(..., "CXL")` for the CXL core
  symbols, `"ACPI"` for `__wrap_acpi_table_parse_cedt()`, and no namespace for
  the rest; there is no "cxl_test" namespace.
- Where mock-or-real is decided differs per wrapper in `mock.c`:

| Shape | Decided by | For example |
|---|---|---|
| op called whenever ops are registered | the op in `test/cxl.c`, which calls the real function itself for a non-mock device | `__wrap_acpi_table_parse_cedt()`, `__wrap_acpi_pci_find_root()` |
| predicate, then op | `is_mock_port()` or `is_mock_dev()` in the wrapper | `__wrap_devm_cxl_add_dport_by_dev()` |
| predicate, no op | wrapper has the mock behaviour inline | `__wrap_cxl_await_media_ready()`, `__wrap_devm_cxl_add_rch_dport()` |
| real function always called | wrapper only edits an argument first | `__wrap_nvdimm_bus_register()` |
| op return value | op returns negative to ask for the real function | `__wrap_region_intersects()` |
| device name | `"hmem_platform.1"`; real function for any other host | `__wrap_walk_hmem_resources()` |

- Every redirected CXL core function is defined in `cxl_core` and called only
  from another module (for example `drivers/cxl/port.c`,
  `drivers/cxl/acpi.c`); the tree has no example of `--wrap` redirecting a
  call made inside one module.

**Mock build upkeep**

- Nothing in the kernel's own Makefiles or Kconfig builds
  `tools/testing/cxl/`; a break there shows only when that directory is built
  as an external module.
- New core file with per-file flags: `drivers/cxl/core/Makefile` uses
  `CFLAGS_trace.o`, while Kbuild sets `-DTRACE_INCLUDE_PATH` and the include
  paths directory-wide in `ccflags-y`; a per-file flag is not picked up by the
  Kbuild copy unless added there.
- Kbuild's `cxl_core` list equals the Makefile list plus `config_check.o`,
  `cxl_core_test.o` and `cxl_core_exports.o`.
- Core symbol that `cxl_test` needs and the core does not export: add the
  export to `tools/testing/cxl/cxl_core_exports.c`, not to `drivers/cxl/`.
- Prototype change, what the compiler checks: `mock.c` includes `cxlmem.h` and
  `cxlpci.h`, so the wrapper's call to `<name>()` and its call to the op are
  checked; no header declares `__wrap_<name>()`, so the wrapper's own
  parameter list and return type are checked against nothing.
- Prototype change, places: `__wrap_<name>()` in `mock.c`; the member of
  `struct cxl_mock_ops` and the mock in `test/cxl.c` only where the wrapper
  has an op; there is no typedef or trampoline to update.
- Context passed to `acpi_table_parse_cedt()`: `mock_acpi_table_parse_cedt()`
  casts `arg` to `struct cxl_cedt_context` and reads its first member, so
  `struct cxl_cfmws_context`, `struct cxl_chbs_context` and
  `struct cxl_cxims_context` in `drivers/cxl/acpi.c` must keep
  `struct device *dev` first.
- New wrapper's export: the rebuilt module imports `__wrap_<name>`, so
  `cxl_mock` must export it; for a CXL core symbol use
  `EXPORT_SYMBOL_NS_GPL(..., "CXL")` as the existing wrappers do.
- **Unsafe usage**: adding a member to `struct cxl_mock_ops`, calling it from
  a wrapper, and not setting it in `cxl_mock_ops` in
  `tools/testing/cxl/test/cxl.c`.
  - Unsafe: wrappers test `ops` for NULL but never the member, so the call
    dereferences NULL once `cxl_test` has registered its ops.
  - Safe: set the member in the one `cxl_mock_ops` instance, as
    `.devm_cxl_add_dport_by_dev = mock_cxl_add_dport_by_dev` does.

**Build variants and ABI**

| Option | Objects | Stubs when off |
|---|---|---|
| `CONFIG_CXL_REGION` | `region.o`, `region_pmem.o`, `region_dax.o` | `drivers/cxl/core/core.h`, `drivers/cxl/cxl.h`, `drivers/cxl/cxlmem.h` |
| `CONFIG_CXL_RAS` | `ras.o`, `ras_rch.o` | `drivers/cxl/core/core.h`, `drivers/cxl/cxlpci.h` |
| `CONFIG_CXL_ATL` | `atl.o` | `drivers/cxl/cxl.h` |
| `CONFIG_CXL_FEATURES` | `features.o` | `include/cxl/features.h` only |
| `CONFIG_CXL_MCE` | `mce.o` | `drivers/cxl/core/mce.h` |
| `CONFIG_CXL_EDAC_MEM_FEATURES` | `edac.o` | `drivers/cxl/cxlmem.h` |
| `CONFIG_CXL_SUSPEND` | `suspend.o`, its own `obj-`, not part of `cxl_core` | `drivers/cxl/cxlmem.h`, `include/linux/pm.h` |

- `drivers/cxl/core/core.h` holds stubs for `CONFIG_CXL_REGION` and
  `CONFIG_CXL_RAS` only; it has none for MCE, features or EDAC.
- `CONFIG_CXL_FEATURES` block in `drivers/cxl/core/core.h`: declarations with
  no `#else`; `cxl_get_feature()`, `cxl_set_feature()` and
  `cxl_feature_info()` are called only from `features.c` and `edac.c`, and a
  call from an always-built file breaks the build with the option off.
- `devm_cxl_add_dax_region()` and `devm_cxl_add_pmem_region()`: same pattern,
  declared under `CONFIG_CXL_REGION` with no stub, called only from the region
  files.
- `cxlfs` in `struct cxl_dev_state` (`include/cxl/cxl.h`): exists only under
  `CONFIG_CXL_FEATURES`; outside `features.c` use `to_cxlfs()`, which has a
  stub that returns NULL.
- `cxl_region_attach()` is `static` in `drivers/cxl/core/region.c` and has no
  stub; `cxl_decoder_detach()` has one.
- There is no cxl_port_get_spa_cache_alias() and no
  devm_cxl_memdev_edac_release() in this tree.
- `CONFIG_CXL_RAS`, PCI side: `aer_cxl_rch.o` in `drivers/pci/pcie/Makefile`,
  stubs in `drivers/pci/pcie/portdrv.h`.
- `CONFIG_CXL_PMU`: defined in `drivers/perf/Kconfig`, not
  `drivers/cxl/Kconfig`; `pmu.o` is in `cxl_core-y` unconditionally and has no
  stubs.
- `CONFIG_CXL_EDAC_SCRUB`, `CONFIG_CXL_EDAC_ECS`, `CONFIG_CXL_EDAC_MEM_REPAIR`,
  `CONFIG_CXL_MEM_RAW_COMMANDS`: no objects and no stubs; tested with
  `IS_ENABLED()` or `#ifdef` inside `drivers/cxl/core/edac.c` and
  `drivers/cxl/core/mbox.c`.
- Event record structures decoded by the trace events: defined in
  `include/cxl/event.h`, not in `drivers/cxl/cxlmem.h`.
- Trace events: all are in `drivers/cxl/core/trace.h`; search it for
  `TRACE_EVENT(`. Easy to miss: `cxl_port_aer_uncorrectable_error`,
  `cxl_port_aer_correctable_error` and `cxl_memory_sparing`.
- Region trace events: none; `cxl_general_media`, `cxl_dram` and `cxl_poison`
  read `cxlr->params.uuid` and the region name, and `cxl_poison` calls
  `cxl_dpa_to_hpa()`, so a change to `struct cxl_region` or to that helper's
  stub in `core.h` also touches `trace.h`.
- EDAC attributes published by `edac.c`: documented in
  `Documentation/ABI/testing/sysfs-edac-scrub`,
  `Documentation/ABI/testing/sysfs-edac-ecs` and
  `Documentation/ABI/testing/sysfs-edac-memory-repair`, not in
  `Documentation/ABI/testing/sysfs-bus-cxl`.
- Debugfs files: `Documentation/ABI/testing/debugfs-cxl`.

## Model gaps

### Other mistakes models make

- Models take `devm_cxl_add_region()` to hang region removal on a devres
  action. It registers none: a region sits in the `regions` xarray of
  `struct cxl_root_decoder`, and `unregister_region()` in
  `drivers/cxl/core/region.c` removes it under `regions_lock`, for example
  from `delete_region_store()`, `kill_regions()` or
  `endpoint_unregister_region()`.
- Models take `cxld_unregister()` to act on endpoint decoders only. For a root
  decoder it calls `kill_regions()`, which unregisters every region left and
  sets `cxlrd->dead`; `__create_region()` then returns `-ENXIO`.
- Models take every committed region to spawn a pmem or dax child device.
  `cxl_region_probe()` returns 0 with no child when a target memdev has
  `attach` (`cxl_region_has_memdev_attach()`), or when a ram region overlaps
  System RAM.
- Models take `cxl_mem_sanitize()` to hold `cxl_rwsem.region` alone. It takes
  the memdev device lock first, with `guard(device)(&cxlmd->dev)`.
- Models take a trace array to match the size of the hardware data. The
  `header_log` field is `CXL_HEADERLOG_TRACE_SIZE_U32` (128) while hardware
  gives `CXL_HEADERLOG_SIZE_U32` (16); callers pass a zero-filled 128-entry
  buffer, and a `static_assert()` in `drivers/cxl/core/ras.c` pins the size.
- Models gate CXL error handling on PCIEAER_CXL or CXL_RCH_RAS.
  `CONFIG_CXL_RAS` in `drivers/cxl/Kconfig` is the gate, and it depends on
  `ACPI_APEI_GHES` as well as `PCIEAER`.
- Models know only `rwsem_write_kill` and `rwsem_read_intr` as conditional
  guard classes here. `mutex_intr` is also used on `poison.mutex` in
  `cxl_mem_get_poison()`, and `device_intr` on the memdev in
  `drivers/cxl/mem.c`.
- Models take CXL symbols to be exported in namespace `CXL`.
  `devm_cxl_add_endpoint()` (in `drivers/cxl/port.c`) and
  `cxl_memdev_attach_region()` use `EXPORT_SYMBOL_FOR_MODULES()` for `cxl_mem`
  alone.
- Models place the definition of `cxl_rwsem` in `drivers/cxl/core/port.c` or
  `drivers/cxl/core/region.c`. It is in `drivers/cxl/core/hdm.c` and is not
  exported.
- Models name find_cxl_port(). It is not defined; `find_cxl_port_by_dport()`
  and `find_cxl_port_by_uport()` in `drivers/cxl/core/port.c` look a port up.
- Models spell the DVSEC ids and offsets with a CXL_DVSEC prefix. They are
  `PCI_DVSEC_CXL_DEVICE`, `PCI_DVSEC_CXL_RANGE_SIZE_LOW()` and so on in
  `include/uapi/linux/pci_regs.h`; only `CXL_DVSEC_RANGE_MAX` has that
  prefix.
