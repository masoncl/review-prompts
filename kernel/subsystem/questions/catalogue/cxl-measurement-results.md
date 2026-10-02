# What the cxl measurement found

Three models were asked the 33 questions in `cxl-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C needed the fewest corrections
and assumed the newest kernel, reader A was a few releases behind it, and
reader B was several releases behind both and wrong about most of the subject.
The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

`drivers/cxl/` changes quickly, and that is what the measurement shows. Readers
A and C describe the architecture correctly and know idioms that are one or two
releases old (the combined region and address lock, the interruptible lock
acquisition, dports created on demand). What they get wrong is what moved in the
last few releases: a lock that was renamed, a structure that moved to a public
header, the entry points for registering a memdev, files split out of
`region.c` and `ras.c`. Reader B describes a driver that no longer exists.

## What all three readers got wrong

- **The lock on a root decoder's regions is `regions_lock`.** Every reader
  called it range_lock, in four or five answers each. `struct cxl_root_decoder`
  has `regions_lock`, a `regions` xarray and `dead`; the lock is taken by
  `create_region_store()`, `delete_region_store()`, `kill_regions()`,
  `endpoint_unregister_region()` and `cxl_add_to_region()`, which holds it
  across `attach_target()` and `device_attach()` (reader C said it is dropped
  first). No range_lock exists under `drivers/cxl/`.
- **`cxl_rwsem` is defined in `drivers/cxl/core/hdm.c`.** Two readers said
  `core/port.c`, one a core.c that does not exist.
- **`struct cxl_dev_state` is in `include/cxl/cxl.h`**, not
  `drivers/cxl/cxlmem.h`, with the register maps and the partition types. A
  bare one is allocated by the `devm_cxl_dev_state_create()` macro, which
  requires it to be the first member of the driver's structure; reader C knew of
  no such allocator and reader A doubted it. An accelerator driver is merged,
  `drivers/net/ethernet/sfc/efx_cxl.c`; no reader knew that it was.
- **There is no devm_cxl_add_memdev().** All three named it. A class device is
  registered with `devm_cxl_add_classdev()` and an accelerator with
  `devm_cxl_probe_mem()`, both in `drivers/cxl/mem.c` over
  `__devm_cxl_add_memdev()`. With a `struct cxl_memdev_attach` a memdev that
  does not bind is unregistered and the call returns -ENXIO, and
  `detach_memdev()` releases the parent device's driver. No reader had all of
  that; reader B invented cxl_accel_state_create() and a cdev_lock.
- **Files.** The pmem and dax devices of a region are in `region_pmem.c` and
  `region_dax.c` (every reader put them in `region.c`, reader C with a "maybe
  split"). Readers A and B did not know `atl.c` or `ras_rch.c`.
- **When RAS registers are mapped.** `__devm_cxl_add_dport()` calls
  `devm_cxl_dport_ras_setup()`, and only for a dport that is not RCH; an RCH
  dport waits for `devm_cxl_dport_rch_ras_setup()` in
  `cxl_endpoint_port_probe()`; a switch port's own registers are mapped by
  `devm_cxl_port_ras_setup()` when its first dport is added. The error handlers
  read `cxlmd->endpoint->regs.ras` for both topologies. Each reader had two or
  three of these wrong, and readers A and C offered
  cxl_dport_init_ras_reporting(), which is gone.
- **Which core functions the mock wraps.** Six: `cxl_await_media_ready()`,
  `devm_cxl_add_rch_dport()`, `cxl_endpoint_parse_cdat()`,
  `devm_cxl_endpoint_decoders_setup()`,
  `devm_cxl_switch_port_decoders_setup()` and `devm_cxl_add_dport_by_dev()`.
  Reader A listed seven functions that are not wrapped, reader C a
  DECLARE_TESTABLE mechanism that does not exist, reader B said mailbox send is
  wrapped.
- **What the mock build asserts.** `config_check.c` wants `CONFIG_CXL_BUS`,
  `CONFIG_CXL_ACPI` and `CONFIG_CXL_PMEM` as modules and five more options
  enabled; it does not check the mem, port or region options. Nothing reads
  CXL_TEST_ENABLE.
- **Region flags.** There are four. Readers B and C left out
  `CXL_REGION_F_NORMALIZED_ADDRESSING`, reader B also `CXL_REGION_F_LOCK`, and
  reader A offered a CXL_REGION_F_INCOHERENT that does not exist. Nothing ever
  clears `CXL_REGION_F_AUTO`.
- **What a skip is.** All three described it loosely. `__cxl_dpa_alloc()`
  computes it as the unallocated space in lower partitions up to the start of
  the partition being allocated from.
- **`port_to_host()`** returns the root's `uport_dev`, the platform firmware
  device, for the root and for every first-level port, and the parent port for
  the rest. Each reader had it some other way.
- `module_cxl_driver()` is used by `cxl_mem` alone; the rest call
  `cxl_driver_register()` (readers A and C said it registers them all).

## What readers A and B got wrong

- **Dport creation.** Reader B has dports enumerated at port probe and decoders
  set up after them. Reader A knew they are created on demand but not the
  callback, `add_dport` in `struct cxl_driver`, nor
  `cxl_port_update_decoder_targets()`. Reader C had all of it.
- **Teardown caller.** Reader A named cxl_decoder_kill_region(), which is gone;
  the unconditional lock in `cxl_decoder_detach()` is for `DETACH_INVALIDATE`
  from `cxld_unregister()`. Reader B said the function always locks
  unconditionally.
- **Cache invalidation** happens before the decoders are reset and before they
  are committed (reader A had it after). On a platform that cannot do it the
  commit fails with -ENXIO; the test option only prints once and carries on
  (reader B said it taints).
- **Address translation.** `cxl_dpa_to_hpa()` adds `p->cache_size` and then
  applies `cxlrd->ops.hpa_to_spa`; `ops` is an embedded `struct cxl_rd_ops`.
  Reader B tied normalized addressing to a decoder flag and to identity
  translation; such regions get `ULLONG_MAX` and no poison debugfs files.
- The order in `cxl_memdev_unregister()` is `cdev_device_del()` and then
  `cxl_memdev_shutdown()` (reader A had it reversed).

## What reader B got wrong as well

These would change a verdict, and there are too many to build a 600-word guide
around; they argue for that reader reading the source.

- The partition model: it has ram_res and pmem_res in the device state and a
  mode of CXL_DECODER_RAM or CXL_DECODER_PMEM in the endpoint decoder. The tree
  has `cxlds->part[]` and an index, `cxled->part`.
- The two separate rwsems by their old names in some answers and the new one in
  others.
- `cxl_internal_send_cmd()`: -EBUSY for a dead mailbox, and "never a positive
  value" for the transport. The body passes the transport's error through,
  reserves -EIO for a short output, and warns and returns -ENXIO if the
  transport itself returns -EIO.
- Background commands waited for with a completion (it is an rcuwait), sanitize
  holding the mailbox mutex, a uevent on completion.
- User commands: a size mismatch is -ENOMEM and a refused payload -EBUSY, not
  -EINVAL; raw commands are gated by a configuration option, lockdown and a
  debugfs switch, not a module parameter.
- `to_cxl_memdev_state()` called an unchecked cast. It returns NULL for anything
  that is not a class device.
- Region states: two of the five missing, a CXL_CONFIG_RESET that does not
  exist, and the driver released after the decoders are reset instead of
  before.
- `dports` a list on the parent (an xarray keyed by `dport_dev`), calc_hb() on
  the root decoder, the error handlers in `pci.c`, `drivers/cxl/acpi.c` not
  rebuilt by the mock (it is; `pci.c` is the one that is not), module
  parameters for the mock's port counts (they are constants).

## What the readers already knew

Readers A and C: the object model (ports, dports, endpoints and how they are
keyed), the three decoder kinds, `cxl_rwsem` and its two members, the
`ACQUIRE()` and `ACQUIRE_ERR()` idiom and that skipping the error check is the
bug, the order region then dpa, the ordering of DPA allocation by `hdm_end` and
of commits by `commit_end`, the region states, what attach checks, the return
values of `cxl_internal_send_cmd()` including the -EIO rule, the ioctl checks,
the `--wrap` mechanism and that a new core file must be added to the mock's
Kbuild, and the hand-written guide's one subject (reader A exactly, reader C
with a wrong function name). Reader C also: the on-demand dports end to end,
background commands and sanitize, `atl.c` and `ras_rch.c`,
`EXPORT_SYMBOL_FOR_MODULES()`.

## Where the hand-written guide is stale

`cxl.md` is about one bug and is still right about it: `DEFINE_RES_MEM()` is
what `cxl_setup_extended_linear_cache()` uses, a resource of type 0 fails
`resource_contains()`, and `hmat_get_extended_linear_cache_size()` then returns
0 with a zero size. Two details have moved. The type comparison is now in
`__resource_contains_unbound()`, which `resource_contains()` calls after its own
test for `IORESOURCE_UNSET`. And the zero is stored in the root decoder,
`cxlrd->cache_size`; a region picks it up later in
`cxl_extended_linear_cache_resize()`, which is where the size that user space
sees goes wrong. What is wrong with the guide is what it leaves out: it is
loaded for every patch under `drivers/cxl/` and says nothing about ports,
decoders, regions, locking, the mailbox or the mock. Reader A answers its one
subject from memory.

## What was left out of the build set, and why

The hand-written guide is 218 words, so the built guide aims at the 600-word
floor. The build set has ten questions and asks for 550 words, none of them for
fewer than 40. The first cut aimed at 300 words with eight questions and
budgets of 20 to 35 words, and its answers came out as fragments that needed
the question beside them. The same eight are kept with room to say what each
fact is about, and `cxl.port-removal` and `cxl.devm-host-usage` came back:
every reader had details of them wrong (which device `port_to_host()` returns,
for one), a change to port lifetime depends on both, and nothing else in the
guide says how a port goes away. Everything below was measured and is real;
there is no room.

- `cxl.mbox-send`, `cxl.mbox-background`, `cxl.mbox-user-commands`,
  `cxl.poison-locking`: readers A and C answer them, reader C almost without
  correction. Only reader B is wrong, and about all of it.
- `cxl.port-objects`, `cxl.decoder-kinds`, `cxl.conditional-guards`,
  `cxl.commit-order`, `cxl.region-states`, `cxl.region-attach-detach`,
  `cxl.auto-regions`: the same. The renamed lock that spoils several of them is
  covered by `cxl.core-locks`.
- `cxl.device-state`: all three were wrong, about where the structure is and
  how it is created. Both facts are asked for by `cxl.core-files` and
  `cxl.memdev-lifetime`.
- `cxl.ras-handling`: all three were wrong about when the registers are mapped.
  The port half is asked for by `cxl.dport-creation`; the handlers themselves
  are left to the source.
- `cxl.dpa-allocation`, `cxl.dpa-partitions`: the definition of a skip and the
  lists of busy errors are relevance 3 at most once the ordering rule is known,
  which readers A and C do know.
- `cxl.port-enumeration`: every reader had details wrong (what each error code
  from the helpers means), but it is confined to `core/port.c`, the answer
  needs seventy words or more, and `cxl.dport-creation` already says where
  enumeration starts and which callback it reaches. First to come back if the
  guide is given more room.
- `cxl.test-mock-ops`, `cxl.test-topology`, `cxl.change-checklist`: the list of
  wrapped functions and what a patch must touch are folded into
  `cxl.test-build`.
- `cxl.cache-invalidation`, `cxl.address-translation`, `cxl.modules-and-bus`,
  `cxl.docs`: relevance 2 or 3.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           94        40%      2     16   6.12 to 6.18
reader B          117        81%      0     33   6.10 to 6.12
reader C           90        23%     10      4   6.17 to 7.0

question                      reader A      reader B      reader C
cxl.core-files                31% ( 5)      55% ( 7)      22% ( 4)
cxl.docs                      28% ( 1)      70% ( 2)       0% ( 0)
cxl.modules-and-bus           30% ( 4)      64% ( 4)      22% ( 2)
cxl.port-objects              10% ( 1)      69% ( 6)       0% ( 0)
cxl.decoder-kinds             27% ( 3)      74% ( 3)       4% ( 3)
cxl.device-state              60% ( 3)      82% ( 3)      44% ( 4)
cxl.dpa-partitions            50% ( 2)      87% ( 2)      23% ( 2)
cxl.core-locks                22% ( 4)      46% ( 5)      13% ( 4)
cxl.lock-order                29% ( 2)      74% ( 3)      26% ( 3)
cxl.conditional-guards        40% ( 3)      89% ( 2)      26% ( 1)
cxl.devm-host-usage           34% ( 5)      82% ( 5)      26% ( 4)
cxl.port-enumeration          50% ( 4)      91% ( 3)      19% ( 4)
cxl.dport-creation            65% ( 2)      88% ( 2)       5% ( 1)
cxl.port-removal              40% ( 3)      92% ( 2)      31% ( 3)
cxl.dpa-allocation            47% ( 3)      82% ( 6)      42% ( 3)
cxl.commit-order              30% ( 2)      84% ( 3)      33% ( 3)
cxl.region-states             47% ( 3)      95% ( 5)      18% ( 4)
cxl.region-attach-detach      45% ( 2)      92% ( 2)       6% ( 2)
cxl.region-flags              80% ( 2)      83% ( 1)      32% ( 3)
cxl.auto-regions              36% ( 1)      89% ( 1)      35% ( 4)
cxl.cache-invalidation        47% ( 6)      81% ( 3)      26% ( 2)
cxl.address-translation       62% ( 2)      96% ( 4)      37% ( 2)
cxl.hmat-resource-usage       29% ( 1)      75% ( 2)      22% ( 2)
cxl.memdev-lifetime           78% ( 7)      92% ( 5)      28% ( 7)
cxl.mbox-send                 11% ( 1)      83% ( 2)       5% ( 1)
cxl.mbox-background           49% ( 2)      80% ( 3)       0% ( 0)
cxl.mbox-user-commands        25% ( 2)      93% ( 4)      10% ( 1)
cxl.poison-locking            39% ( 2)      87% ( 2)      13% ( 1)
cxl.ras-handling              62% ( 5)      87% ( 5)      49% ( 6)
cxl.test-build                41% ( 4)      85% ( 5)      43% ( 4)
cxl.test-mock-ops             34% ( 3)      81% ( 2)      35% ( 2)
cxl.test-topology             39% ( 1)      78% ( 3)      39% ( 2)
cxl.change-checklist          28% ( 3)      74% (10)      29% ( 6)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `cxl.device-state`, `cxl.dpa-partitions`, `cxl.port-enumeration`, `cxl.dpa-allocation`, `cxl.auto-regions`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `cxl.port-objects`, `cxl.decoder-kinds`, `cxl.conditional-guards`, `cxl.commit-order`, `cxl.region-states`, `cxl.region-attach-detach`, `cxl.mbox-send`, `cxl.mbox-background`, `cxl.mbox-user-commands`, `cxl.test-mock-ops`, `cxl.change-checklist`.

## Questions reorganised

By subject now, 27 questions where there were 28: locks; device state and memdevs; ports and
dports (with `cxl.devm-host-usage`); decoders and device addresses (with `cxl.dpa-partitions`);
regions (with `cxl.region-flags` and `cxl.hmat-resource-usage`); mailbox; the mock build and other
builds. `cxl.test-build` and `cxl.test-mock-ops` both asked which core functions are wrapped and what
a patch must touch, and are merged as `cxl.mock-build`. `cxl.change-checklist` keeps the
configured-out builds, the trace events and the ABI document; the mock build and devices without a
mailbox are asked by `cxl.mock-build` and `cxl.device-state`. `cxl.port-objects` and
`cxl.decoder-kinds` no longer ask what each structure is or which fields it adds. Nothing else dropped.
