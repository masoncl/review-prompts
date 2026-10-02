# What the pci measurement found

Three models were asked the 32 questions in `pci-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 6.19), reader A close behind it (6.12 to 6.17),
and reader B older (6.10 to 6.12) and much less sure of itself, with names it
made up and several rules stated backwards. The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

Readers A and C know the driver-facing interface well, including all four
things the hand-written guide is about: which endpoint functions return an
error pointer and which NULL, which release functions check their argument,
which MSI functions are legacy, and who names a PCI device. What all three get
wrong is inside the core: what restoring state does when nothing was saved,
which locks a function reset takes, when error recovery resets the link, and
the newer facilities under `drivers/pci/`. Reader B also gets the old guide's
own topics wrong in ways that would change a review verdict, so those stay in
the build set although two readers answer them.

## What all three readers got wrong

- **`pci_restore_state()` has no early return.** Every reader said it does
  nothing when `state_saved` is false. Its body never reads the flag: it
  restores from `saved_config_space` and the capability save buffers
  unconditionally and then clears the flag. The test the readers remembered is
  in `pci_store_saved_state()`. No reader listed `pci_bus_add_device()` among
  the places the core saves state; it calls `pci_save_state()` for every device
  as it is added. To the power management callbacks a set `state_saved` means
  the driver saved state itself, and `pci_pm_suspend_noirq()` then skips both
  its own save and the move to a low-power state.
- **What a function reset locks.** `pci_reset_function()` takes
  `pci_dev_lock()` (the device lock plus `pci_cfg_access_lock()`) on the
  upstream bridge as well as on the device. Reader A had only the device lock
  on the bridge; readers B and C left the bridge out or had
  `__pci_reset_function_locked()` and `pci_reset_function_locked()` needing or
  taking the configuration access lock. Both only call `device_lock_assert()`.
  `pci_try_reset_function()` trylocks the device alone. Reader B's list of
  reset methods was wrong as well; `pci_reset_fn_methods` is device_specific,
  acpi, flr, af_flr, pm, bus, cxl_bus.
- **Error recovery.** Each reader had the outline of `pcie_do_recovery()` and
  each had steps wrong. The reset is done when the state is
  `pci_channel_io_frozen` or the combined vote is
  `PCI_ERS_RESULT_NEED_RESET`, including for a non-fatal error, and it comes
  after the `mmio_enabled` pass, not straight after `error_detected`. A
  device that is not a bridge and has no `error_detected` handler votes
  `PCI_ERS_RESULT_NO_AER_DRIVER`, which wins in `merge_result()` and fails
  recovery for everything under the port (reader B said such a device is
  skipped); the `error_detected` walk still reaches every device. On failure
  `report_perm_failure_detected()` calls `error_detected` with
  `pci_channel_io_perm_failure` on the drivers that have one and sends a
  disconnect uevent for every device; nothing is removed.
- **Power control has moved to the controller drivers.** Readers A and C said
  that marking a power control device ready starts a bus rescan, which is what
  the kerneldoc above `pci_pwrctrl_device_set_ready()` still says. The body
  only registers a bus notifier. The devices are created and powered by host
  controller drivers calling `pci_pwrctrl_create_devices()` and
  `pci_pwrctrl_power_on_devices()` before they scan. Reader B did not know the
  facility. Reader A named a slot.c under `drivers/pci/pwrctrl/`; the files are
  `core.c`, `generic.c` and two device drivers.
- **Resizable BARs** are in `drivers/pci/rebar.c` (readers A and B put
  `pci_resize_resource()` in other files), and the function itself returns
  `-EBUSY` when memory decoding is on. Data object exchange is called by the
  TSM code as well as by CXL, which no reader said.
- **Driver probe runs from a workqueue.** All three said `pci_call_probe()`
  uses `work_on_cpu()`. It queues on `pci_probe_wq` on a housekeeping CPU of
  the device's node and probes directly when there is none. Binding is gated
  by `pci_dev_allow_binding()` and started with `device_initial_probe()` in
  `pci_bus_add_device()`; reader A remembered a match_driver flag and reader B
  an is_added member of `struct pci_dev`, neither of which exists.
- **Lock requirements are asserted, not just documented.** Readers A and C
  said the need to hold `pci_rescan_remove_lock` is stated only in comments,
  and reader B had the rule the wrong way round.
  `pci_stop_and_remove_bus_device()` has
  `lockdep_assert_held(&pci_rescan_remove_lock)`, and the functions whose
  names end in locked assert `pci_bus_sem` or the device lock.
- **Configuration callbacks and `pci_lock`.** Every reader said a controller's
  read and write callbacks always run under `pci_lock`. With
  `CONFIG_PCI_LOCKLESS_CONFIG` (x86 and UML) the bus accessors do not take it
  while the user-space accessors still do, and some architectures'
  `raw_pci_read()` calls the callback with no lock. A callback need not set the
  all-ones value itself: the wrappers do that whenever it returns nonzero. A
  read at a misaligned offset returns `PCIBIOS_BAD_REGISTER_NUMBER` before the
  output is written, so "always all ones after a failure" is not quite so.
- **Interrupt vector flags.** No reader mentioned `pci_irq_type()`, which is
  how a driver learns which type it was given. Readers A and B used
  PCI_IRQ_LEGACY, which this tree no longer defines; the flag is
  `PCI_IRQ_INTX`. The error returned is that of the last type tried, and
  `-ENOSPC` only when neither MSI-X nor MSI was tried.
- **Freeing vectors on a managed device.** All three knew that a second
  `pci_free_irq_vectors()` does nothing because `pci_disable_msix()` and
  `pci_disable_msi()` return when the mode is not enabled, which is more than
  the kerneldoc admits (it warns of a double free). Each had the mechanism
  slightly off: the devres action `pcim_msi_release()` is added by
  `pcim_setup_msi_release()` on the first MSI or MSI-X enable of a managed
  device, not by `pcim_enable_device()`; reader A expected a warning for
  vectors freed while handlers are attached and cited a document that does not
  mention the subject; reader B invented pcim_alloc_irq_vectors().
- **Registering a host bridge.** Each reader had a step of `pci_host_probe()`
  wrong: a probe-only check that is not there, the devices being added by the
  scan function, or what the runtime power management comment asks for. It
  takes the rescan lock around the scan and again around
  `pci_bus_add_devices()`, not around resource assignment, and enables runtime
  power management on the bridge device itself.
- **What else a change must keep working.** UML also selects lockless
  configuration access; there are no KUnit tests under `drivers/pci/`;
  `tools/testing/selftests/pcie_bwctrl/` exists beside the endpoint selftest;
  the stubs for a kernel without MSI are in `include/linux/pci.h`, not under
  `drivers/pci/msi/`.

## What only some readers got wrong

Reader B, and nobody else. The first seven would change a verdict:

- `pci_epc_get()` returns NULL. It returns `ERR_PTR(-EINVAL)`.
- `pci_epf_destroy()` tolerates NULL and `pci_epf_free_space()` does not
  guard. The first is a bare `device_unregister(&epf->dev)`; the second
  returns on a NULL `addr`.
- A PCI Express capability register the device does not implement reads as
  `PCIBIOS_DEVICE_NOT_FOUND`. `pcie_capability_read_word()` returns 0 with the
  value 0. The read-modify-write lock is the per-device `pcie_cap_lock`, for
  `PCI_EXP_LNKCTL`, `PCI_EXP_LNKCTL2` and `PCI_EXP_RTCTL` only, and the dword
  form takes none.
- `PCIBIOS_BAD_REGISTER_NUMBER` becomes `-EINVAL` (it is `-EFAULT`), callers
  should not compare a value with all ones (`PCI_POSSIBLE_ERROR()` is for
  that), and a device is gone when its error state is a recovery result
  (`pci_dev_is_disconnected()` tests `pci_channel_io_perm_failure`).
- The core disables virtual functions when the physical function's driver is
  removed. `pci_iov_remove()` only warns.
- `pci_disable_device()` is a no-op on a managed device, clears bus mastering
  before it decrements, and turns decoding off. It decrements first, clears
  `PCI_COMMAND_MASTER` only at zero and touches nothing else, and devres calls
  it a second time.
- Memory-mapped reads and writes are intercepted for a disconnected device.
  Only the configuration accessors check.
- Names that exist nowhere: pcim_iomap_regions_request_all() (gone from this
  tree), PCI_MSIX_FLAGS_ALLOC_DYN, pci_enable_tph() (it is
  `pcie_enable_tph()`), PCI_ERS_RESULT_NO_AND_NEED_RESET, a core_init event and
  pci_epc_register_notifier(), reserved_bar, bar_fixed_size and bar_fixed_64bit
  members of `struct pci_epc_features`, alloc_addr_space in `struct
  pci_epc_ops`.
- Writing the `start` attribute binds a function (the configfs link does);
  SR-IOV BARs are outside `dev->resource[]`; the header fixup runs before BARs
  are sized; only the documentation calls the older MSI functions legacy.

Readers A and B: a positive return from probe is a failure (it is warned about
and treated as success); the static ID table is matched with `pci_match_id()`.

Reader A alone: a cfg_access_blocked field (it is `block_cfg_access`);
pcim_iounmap_regions() as deprecated (it is gone); a misaligned PCI Express
capability access returns `-EINVAL`; `PCI_EXP_LNKCTL2` missing from the locked
registers; `pci_dev_str_match()` comparing device names; resizable BAR, ATS,
PRI and PASID state listed as saved (they are only restored); a pci_ep-cfs.c
file name; pci_dev_run_wake() as a weak architecture hook.

Reader C alone: the device's power state becoming unknown after remove;
`pci_pm_poweroff_noirq()` saving state; the suspend fixup running from the
suspend callback rather than `pci_pm_suspend_late()`.

## What the readers already knew

The file map, the entry points and the documentation (no reader needed more
than small additions). Readers A and C: the endpoint functions that return an
error pointer and those that return NULL, with their codes; that
`pci_epc_put()` checks `IS_ERR_OR_NULL()` and `pci_epf_destroy()` checks
nothing; the five older MSI functions and what each lacks; who names a
function, a bus and a host bridge, that a driver must not rename its
`pci_dev`, and that naming a child it creates is fine; lookups that return a
reference and consume `from`; the fixup phases; the PCI Express capability
accessors (reader C had nothing to correct); surprise removal and
`pci_dev_is_disconnected()`; the SR-IOV path; the enable count; the resource
indexes. These are dropped from the build set or kept only because reader B
has them wrong.

## Where the hand-written guide is stale

- It says every error path after a successful `pci_alloc_irq_vectors()` must
  call `pci_free_irq_vectors()`. For a device enabled with
  `pcim_enable_device()` the vectors are freed by devres, and both
  `Documentation/PCI/msi-howto.rst` and the kerneldoc of
  `pci_free_irq_vectors()` tell such a driver not to call it. The rule is
  missing that precondition.
- It lists `pci_enable_msi()` and `pci_disable_msi()` as the legacy functions.
  The source and the documentation say the same of
  `pci_enable_msix_range()`, `pci_enable_msix_exact()` and
  `pci_disable_msix()`, and the documentation discourages the two vector count
  functions.
- Its reason for preferring `pci_alloc_irq_vectors()` with
  `PCI_IRQ_ALL_TYPES` is that the legacy call lacks MSI-X. It also lacks
  multiple vectors, affinity spreading and the fall back to a pin interrupt.
- Its list of endpoint functions that return an error pointer is two of four
  (the two controller create functions do as well), and it says nothing of
  those that return NULL: `pci_epc_get_features()`, `pci_epf_alloc_space()`
  and `pci_epc_mem_alloc_addr()`.
- It names `pci_epf_destroy()` as the function that must not be given an error
  pointer. `pci_epc_destroy()` is the same: it reads `epc->group` before
  anything else.
- What it says of `pci_epc_get()`, `pci_epf_create()`, `pci_epc_put()` and
  device naming is correct. The naming rule is one every reader knew, so it is
  not in the build set.

## Left out of the build set

The hand-written guide is 493 words, which is under the 600-word floor for a
built guide, so the build set is sized to 600 words (480 to 720) with no
question budgeted under 40. It holds 11 of the 32 questions and asks for 535
words, which with titles and headings comes to about 650. The first build set
held the same eleven at 415 words, with budgets of 25 to 50, and its answers
came out as fragments. When it was resized the room went to those eleven and no
twelfth was added: most of them ask for three to seven things, and eleven
questions at 40 words or more already fill the size. The guide loads for
patches under `drivers/pci/` and for users of the endpoint framework, so the
choice is weighted towards the core and the endpoint functions rather than the
interface ordinary drivers use. Four of the eleven are narrower than their
form in the measurement set: the saved state question drops the list of
capabilities, the managed functions question drops the list of what is offered
and asks only which plain functions change behaviour and which managed ones
are deprecated, the reset question asks for the method list as one line, and
the recovery question leads with when the reset happens. The older MSI
functions question asks what the enabling functions lack, not what each
function lacks, because a disable function lacks nothing worth a line. Two
ask for constant names in full, and two for the answer to say so where the
tree has none of what is asked about. Left out although a reader got them
wrong:

- Interrupt vector flags and `pci_irq_type()`: a removed flag does not
  compile, and the rest is in the kerneldoc of the function being called.
- Matching and probing, the lifecycle and the locks: the corrections were to
  internals of `pci-driver.c`, `bus.c` and `remove.c` that a patch touching
  them has open; the lockdep assertions enforce the lock rule at run time.
- Registering a host bridge and the configuration callbacks: every reader was
  weak, but controller drivers call one function and the order inside it
  matters only to someone changing it.
- The PCI Express capability accessors, enabling, surprise removal, SR-IOV,
  resources, fixup phases, lookups and device names: only reader B was wrong.
  Its belief that an unimplemented capability register reads as an error, and
  that the core disables virtual functions for a driver, are the real losses.
- Endpoint objects, BARs and events: the feature structure has grown
  (`BAR_DISABLED`, reserved subregions, `dynamic_inbound_mapping`,
  `subrange_mapping`) and reader B had old member names, but a function driver
  patch has `include/linux/pci-epc.h` open.
- Dynamic MSI-X: a handful of drivers.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 87 corrections, 30% rewritten on average
reader B: 109 corrections, 72% rewritten on average
reader C: 64 corrections, 21% rewritten on average

question                           reader A      reader B      reader C
pci.core-files                      6% ( 1)      17% ( 3)       0% ( 0)
pci.entry-points                    0% ( 0)       7% ( 1)       1% ( 1)
pci.docs                            0% ( 0)      12% ( 1)       0% ( 0)
pci.newer-facilities               44% ( 7)      70% ( 6)      19% ( 4)
pci.device-lifecycle               34% ( 5)      79% ( 6)       3% ( 2)
pci.driver-binding                 55% ( 5)      87% ( 4)      32% ( 2)
pci.locks                          42% ( 3)      89% ( 5)      22% ( 3)
pci.device-references              47% ( 1)      83% ( 2)       2% ( 1)
pci.device-naming                  38% ( 1)      72% ( 2)       2% ( 1)
pci.quirk-phases                   21% ( 1)      82% ( 2)      18% ( 2)
pci.config-access-returns          44% ( 4)      73% ( 5)      30% ( 2)
pci.pcie-capability-accessors      33% ( 3)      89% ( 3)       0% ( 0)
pci.save-restore-state             54% ( 4)      86% ( 3)      29% ( 4)
pci.enable-device                  23% ( 2)      79% ( 4)      13% ( 1)
pci.managed-functions              18% ( 3)      88% ( 4)      20% ( 2)
pci.bar-resources                  22% ( 1)      94% ( 2)      11% ( 1)
pci.irq-vector-api                 24% ( 3)      79% ( 6)      31% ( 3)
pci.legacy-msi-api                 32% ( 1)      88% ( 3)      23% ( 1)
pci.irq-vector-cleanup             31% ( 3)      69% ( 2)      49% ( 4)
pci.msix-dynamic                   25% ( 1)      81% ( 2)      37% ( 1)
pci.error-recovery                 40% ( 4)      90% ( 5)      43% ( 4)
pci.function-reset                 28% ( 3)      91% ( 5)      20% ( 3)
pci.surprise-removal               42% ( 1)      79% ( 2)       0% ( 0)
pci.sriov                          26% ( 1)      81% ( 2)      11% ( 0)
pci.host-bridge-api                50% ( 6)      78% ( 5)      42% ( 3)
pci.config-ops                     27% ( 3)      86% ( 3)      56% ( 4)
pci.endpoint-objects               32% ( 4)      61% ( 4)      11% ( 3)
pci.endpoint-error-returns         16% ( 5)      37% ( 3)      18% ( 2)
pci.endpoint-teardown-usage        19% ( 1)      81% ( 2)      44% ( 2)
pci.endpoint-bars                  57% ( 3)      80% ( 2)      30% ( 2)
pci.endpoint-init-events           15% ( 2)      87% ( 2)      28% ( 2)
pci.change-checklist               43% ( 5)      60% ( 8)      29% ( 4)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `pci.driver-binding`, `pci.host-bridge-api`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `pci.device-lifecycle`, `pci.locks`, `pci.device-references`, `pci.pcie-capability-accessors`, `pci.irq-vector-api`, `pci.surprise-removal`, `pci.endpoint-objects`.

## Questions reorganised

Organised by subject, 22 questions before and after: configuration space, devices and their
drivers, interrupt vectors and managed devices, removal, reset and recovery, controller drivers,
the endpoint framework. Nothing merged; the lock around a function reset is now asked only in
`pci.function-reset`, not also in `pci.locks`.
Narrowed: `pci.driver-binding` drops how a driver is matched, `pci.device-lifecycle` asks where a
change must go and not for the list of steps, `pci.irq-vector-api` drops the build without MSI.
Replaced: `pci.change-checklist`, an inventory of stubs and tests, by `pci.config-ops-locking`:
callbacks entered without `pci_lock` is what every reader had wrong in it. The rest is dropped.
