# What the mfd measurement found

Three models were asked the 68 questions in `mfd-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc5). The readers are labelled A, B and C; which
models they were does not matter here.

| Reader | Kernel it assumed | Corrections | Rewritten on average | Answers rewritten by 40% or more |
|---|---|---|---|---|
| A | 6.12 to 6.19 | 234 | 17% | 1 of 68 |
| B | 6.12 to 6.14 | 252 | 24% | 9 of 68 |
| C | 6.12 | 287 | 46% | 47 of 68 |

Readers A and B know the MFD core well. Most of the corrections to their
answers narrow a rule that they stated without its condition, or replace a name
that has moved. Reader C describes an older core. Reader C:

- has the copy of the cell in the wrong place
- names functions and members that this tree does not have
- describes a platform driver for `syscon` nodes that this tree does not have

The build set is written for reader C, since a guide is written for the weakest
of its readers.

The hand-written guide was never checked against current sources, so
differences between that guide and the built guide are expected. They are
noted near the end.

## What all three readers got wrong

- **What a failed `mfd_add_devices()` leaves registered.** Every reader said
  the call removes the children that the call had added. The code is
  `if (i) mfd_remove_devices(parent);`, so:
  - when the first cell of the call fails, the call removes nothing, and the
    children of an earlier call stay registered
  - when a later cell fails, the call removes every MFD child of the parent at
    `MFD_DEP_LEVEL_NORMAL`, the children of earlier calls included
  - a child at `MFD_DEP_LEVEL_HIGH` stays registered in both cases
- **The table that lists `simple-mfd`.** Every reader named
  of_default_bus_match_table. That name is in no source file of this tree; only
  `Documentation/devicetree/usage-model.rst` has it. The table is the static
  `match_table` inside `of_platform_default_populate()`.
  `devm_of_platform_populate()` passes a NULL table to
  `of_platform_populate()`, and `__of_match_node()` returns NULL for a NULL
  table. So `devm_of_platform_populate()` creates devices for the direct
  children only.
- **The mark for a reused device tree node.** Every reader wrote that
  `device_set_of_node_from_dev()` sets a member of_node_reused in
  `struct device`. This tree has no such member. The helper calls
  `dev_set_of_node_reused()`, and code that reads the flag calls
  `dev_of_node_reused()`.
- **A resource of type `IORESOURCE_REG` with a `mem_base`.** Every reader said
  the core copies such a resource unchanged. `mfd_add_device()` tests the
  flags of the resource with a bitwise AND against `IORESOURCE_MEM`.
  `IORESOURCE_REG` is 0x300, which contains the bit of `IORESOURCE_MEM`,
  0x200. So the core copies the resource unchanged only when `mem_base` is
  NULL.
- **A syscon lookup on a node without the `syscon` compatible.** Every reader
  said the lookup returns -EINVAL, and reader C added -ENODEV. When the node
  has no registered regmap, `device_node_get_regmap()` returns
  `ERR_PTR(-EPROBE_DEFER)`. Two rules that the readers built on -EINVAL were
  therefore the wrong way round: a consumer that looks up the node before a
  provider calls `of_syscon_register_regmap()` is retried later.
- **The MODALIAS of a child that has an ACPI companion.** Every reader gave
  every such child an alias that starts with acpi. `acpi_companion_match()`
  returns NULL when the companion has no PNP ids, and when the child is not
  the first physical node of the companion. A child without `acpi_match` gets
  the companion of its parent (`adev ?: parent` in `mfd_acpi_add_device()`), so
  its alias starts with platform.
- **Software nodes that several instances share.** Reader A said that the
  in-tree parent copies the node for each instance. Reader B said that the
  node must have static lifetime. Reader C said that a node can belong to one
  device at a time. In the tree the nodes that `drivers/mfd/intel-lpss-pci.c`
  names are static and shared between instances, and the limit is one software
  node for each device.
- **Who calls `mfd_get_cell()`.** Reader A said a few child drivers read the
  name or the compatible through the function. Reader B said that many child
  drivers use the function. Reader C said that callers use the function for
  platform data and for enable and disable callbacks. Outside the core this
  tree has three callers: one reads `id`, and two only test the result for
  NULL.
- **The global state of the core.** Readers A and B said that no lock protects
  `mfd_of_node_list`. Reader C described a counter that numbers the cells,
  which does not exist. The core has `mfd_of_node_mutex` and takes that mutex
  around every walk and every change of the list.
- **Who drops the reference on the device tree node of a child.** Readers A and
  B placed an of_node_put() in `platform_device_release()`, and reader C said
  the core drops the reference on failure. `platform_device_release()` puts
  `dev.fwnode` only, and `drivers/mfd/mfd-core.c` has no of_node_put().
- **What `Documentation/devicetree/bindings/mfd/mfd.txt` says.** Every reader
  attributed these rules to the file, and the file states none of them:
  - that `simple-mfd` must follow a specific compatible
  - that the string must not stand alone
  - what `ranges` means when it is empty

  The only rule of that kind in the tree is `minItems: 3` in
  `syscon-common.yaml`, for a node that has both `syscon` and `simple-mfd`.
- **Rules stated without their condition.** The check relabelled many rules
  from "unsafe" to "potentially unsafe", since correct code in the tree does
  what the rule forbade. Three examples:
  - "set the driver data before adding the cells": `ti_tscadc_probe()` sets
    the driver data after `mfd_add_devices()`, and its children read platform
    data
  - "`pdata_size` must not be the size of a pointer": the same driver passes
    a pointer on purpose
  - "register only a regmap that is not managed by devres with
    `of_syscon_register_regmap()`": all three callers in the tree register a
    regmap that devres manages

## What readers B and C got wrong as well

- **Dependency levels.** Reader B said that `mfd_remove_devices()` removes the
  normal children and then the high ones, and that
  `mfd_remove_devices_late()` removes only the high ones. Reader C said that
  the release of `devm_mfd_add_devices()` calls `mfd_remove_devices_late()`.
  In the tree `mfd_remove_devices()` and the devres release skip every cell at
  `MFD_DEP_LEVEL_HIGH`, and `mfd_remove_devices_late()` removes every MFD child
  that is left. The levels are two macros; there is no enum.
- **Cell callbacks that are gone.** Both named mfd_cell_enable() and
  mfd_cell_disable(), and members enable, disable and usage_count of
  `struct mfd_cell`. None of them is in this tree. Reader A said so correctly.
- **The ACPI companion and the device tree node.** Both said that setting the
  companion clears a device tree node that the core had set. The core calls
  `set_primary_fwnode()`, which writes `dev->fwnode` and leaves `dev->of_node`
  alone. Reader A was unsure.
- **`MFD_RES_SIZE()`.** Both took it for `ARRAY_SIZE()`. It divides `sizeof`
  of its argument by the size of `struct resource`, so it gives 0 for a
  pointer.
- **A non-zero `irq_base` for a regmap interrupt chip.** Both said that it
  creates a legacy domain. `regmap_irq_create_domain()` always calls
  `irq_domain_instantiate()`, with `virq_base` set to the base.
- **The platform device id.** Reader C described a separate case for
  `PLATFORM_DEVID_NONE` that keeps the id of the cell. The code has one test:
  the id is `id + cell->id` unless the `id` argument is `PLATFORM_DEVID_AUTO`.
  Reader B missed that `platform_device_add()` reads a sum of -1 as "no id"
  and a sum of -2 as "allocate one".
- **Memory resources.** Reader B said that the core makes a memory resource
  relative to `mem_base`; the core adds the start of `mem_base`. Reader C said
  that `mfd_add_device()` calls `insert_resource()`; `platform_device_add()`
  does.
- **How `drivers/mfd/syscon.c` maps the registers.** Both named ioremap(); the
  code calls `of_iomap()`. Both also said that the code reads `reg-shift`;
  `of_syscon_register()` does not.

## What only reader C got wrong

- **Where the copy of the cell is.** Reader C said that the core stores the
  copy as platform data and that `mfd_get_cell()` returns
  `dev_get_platdata()`. The core stores a `kmemdup()` copy in
  `pdev->mfd_cell`, and `platform_device_release()` frees that copy.
- **A platform driver for `syscon`.** Reader C described a driver and a probe
  function in `drivers/mfd/syscon.c`. The file registers no driver. Reader C
  also described the lock of the list as a spinlock that is dropped before a
  regmap is created. The lock is the mutex `syscon_list_lock`, held across the
  search and the creation.
- **Which syscon lookup gets clocks and resets.** Reader C had the two lookups
  the wrong way round. `syscon_node_to_regmap()` gets clocks and resets, and
  `device_node_to_regmap()` does not.
- **When `pm_runtime_no_callbacks()` is applied.** Reader C said before
  `platform_device_add()`; the core calls the function afterwards.
- **What stops two cells from getting one node.** Reader C named the
  `OF_POPULATED` flag. The core uses `mfd_of_node_list`.
- **What `of_reg` is compared with.** Reader C said a translated address;
  `of_property_read_reg()` does not translate.
- **`regmap_irq_get_virq()`.** Reader C said the function checks the range of
  the index. The function only tests the `mask` of the entry it is given.
- **Which combinations `regmap_add_irq_chip_fwnode()` refuses.** Most of the
  list that reader C gave was wrong, and reader C named members type_base and
  num_type_reg, which `struct regmap_irq_chip` does not have.
- **`dev_get_regmap()`.** Reader C said that only a regmap made by a devm
  function is found. `__regmap_init()` calls `regmap_attach_dev()` for every
  regmap that has a device.
- **Requesting a child interrupt.** Reader C said that a child must pass a
  NULL hard handler and `IRQF_ONESHOT`. A nested interrupt needs neither.
- **Files that reader C made up:** drivers/mfd/simple-mfd.c and
  drivers/mfd/intel_soc_pmic_core.c.

## What only reader A or reader B got wrong

Each bullet gives what the reader said, and then in brackets what the tree
has.

- Reader A:
  - `platform_match()` compares a driver_override member of the platform
    device (the code calls `device_match_driver_override()`)
  - `MFD_SIMPLE_MFD_I2C` has a prompt (it has none, so only `select` enables
    it)
  - the flag `mask_unmask_non_inverted` is probably gone (it exists, and
    registration refuses both bases without it)
- Reader B:
  - callers of the core exist under `sound/` and `drivers/usb/` (there are
    none)
  - a header drivers/mfd/cros_ec_dev.h exists (it does not)
  - an error path need not call `mfd_remove_devices()` after a failed add (the
    call is needed when an earlier call added children)
  - `Documentation/devicetree/bindings/mfd/syscon.yaml` has a `select` list
    (it has none, and reader A said the same)

## What the readers said they did not know

- Reader A: whether the `suspend` and `resume` members of a cell still exist
  (they do, and nothing calls them), and the name of the lock for the node
  list.
- Reader B: whether a document for the core exists under
  `Documentation/driver-api/` (none does), and whether the syscon code takes a
  reference on the node (it does not).
- Reader C:
  - whether `mfd_remove_devices_late()` exists
  - which driver binds to `simple-mfd` (`drivers/bus/simple-pm-bus.c` lists
    it)
  - whether an ACPI document covers MFD children
    (`Documentation/firmware-guide/acpi/enumeration.rst` does)

## What the readers already knew

- A child is a platform device whose parent is the device of the chip, and
  `mfd_add_devices()` does not wait for a child to probe.
- The core copies platform data with its size, and a child sees the copy.
- A resource with an interrupt domain is mapped, and one without is offset by
  `irq_base` (readers A and B).
- Removal is by parent and by device type (readers A and B).
- When a parent creates children from the device tree and when from cells, and
  what `drivers/mfd/simple-mfd-i2c.c` does.
- Each regmap access takes the lock of the regmap, and a sequence of accesses
  is not atomic.
- The handler of a child interrupt runs in a nested thread.
- The lookup functions of the syscon code and when to use each (readers A and
  B).

## Where the hand-written guide is stale

`kernel/subsystem/mfd.md` is mostly conventions that no code states. Four of
its statements about the code are contradicted by the tree, and two more name
something that does not exist.

| The guide says | The tree |
|---|---|
| with a manual `mfd_add_devices()`, the error path must call `mfd_remove_devices()` | `mfd_add_devices()` calls `mfd_remove_devices()` itself when a cell after the first fails. What an error path still has to remove is narrower: the children of an earlier call, and a child at `MFD_DEP_LEVEL_HIGH` |
| use the `id` of the platform device for numbering, not the id of the cell | the core computes the id of the platform device from the `id` argument and `cell->id`. A driver has no other way to choose it |
| a child gets the data of its parent with `platform_get_drvdata()` | `platform_get_drvdata()` returns the driver data of the device it is given, which is the child |
| `drivers/mfd/simple-mfd-i2c.c` passes its cell arrays through `.data` | `.data` points at a `struct simple_mfd_data`, which holds a regmap configuration and a pointer to the cells |
| `struct max77650` as the example of a private structure | no such structure is defined |
| the `.data` field of `spi_device_id` | the member is `driver_data` |

Two more statements are not wrong, yet a review cannot use them as they are
worded:

- The guide asks that a header used only by the parent and its immediate
  children stays in `drivers/mfd/`. Children in other directories cannot
  include a header from `drivers/mfd/`. No file outside that directory
  includes one. In `mfd.shared-headers` the build set asks where headers live.
- The guide names `rtc_devs` in `drivers/mfd/88pm800.c` as an array that
  cannot be `const`. The driver writes that file-scope array at probe, and the
  check could not show that the write is safe for more than one instance. In
  `mfd.cell-written` the build set asks for the requirement.

## What was left out of the build set and why

The build set has 59 of the 68 measured questions, and the question for "Model
gaps", which is not put to the readers.

Nine questions were dropped. A question is dropped when every reader answers
it correctly, or when the answer would not change a review.

| Question | Why it was dropped |
|---|---|
| `mfd.probe-timing` | every reader knew that the call does not wait for a probe. `mfd.parent-data` asks what the parent must set up first |
| `mfd.resource-conflicts` | every reader knew when the check runs and how a cell turns it off. The corrections were about one return value |
| `mfd.regmap-concurrency` | every reader stated the contract. The corrections added kinds of lock |
| `mfd.supply-alias` | every reader knew what the members do. `mfd.remove-scope` asks what removal undoes |
| `mfd.irq-chip-removal` | every reader stated the order of removal |
| `mfd.populate-or-cells` | every reader was right, at 11%, 8% and 5% rewritten |
| `mfd.simple-mfd-i2c` | every reader was right, at 9%, 10% and 13% rewritten. `mfd.core-files` says where the driver is |
| `mfd.driver-layout` | every reader knew the layout. `mfd.driver-binding` asks how a child binds |
| `mfd.bus-split` | the corrections were about the files of one chip, which would not change a review of another driver |

Eleven questions were kept although no answer to them was rewritten by 40% or
more, since at least one correction changes what a review concludes:

| Question | The correction that matters |
|---|---|
| `mfd.shared-headers` | readers B and C named headers that do not exist |
| `mfd.core-state` | a mutex protects the node list |
| `mfd.id-uniqueness` | what a failed add removes, and where the name collides |
| `mfd.driver-binding` | the MODALIAS of a child that shares the companion of its parent |
| `mfd.of-reg` | the core compares the address as the node gives it |
| `mfd.platform-data` | in-tree code passes a pointer as platform data on purpose |
| `mfd.named-regmaps` | every regmap that has a device is found |
| `mfd.runtime-pm` | the core applies the flag after the device is added |
| `mfd.match-data` | match data of 0 is unsafe only where the driver tests for "no match" |
| `mfd.irq-index` | `regmap_irq_get_virq()` does not check the range of the index |
| `mfd.manual-teardown` | removal is still needed after some failed adds |

`mfd.overview` is kept whatever the measurement says.

Four questions are worded differently from how they were measured:

| Question | What changed |
|---|---|
| `mfd.overview` | it has the text that every build set uses for "Main structures" |
| `mfd.cell-macros` | it stopped asking which members no macro sets, since a search gives that list |
| `mfd.syscon-config` | it no longer asks which properties the code reads, since a search gives that list |
| `mfd.match-data` | it no longer asks how each driver chooses its cells, and asks only for the requirement |

In the build set `mfd.core-change` asks what code outside the core relies on.
In the measurement set the question asks which code that is.

The questions are organised by subject, and all the questions of a part share
one section: cells; child names and driver binding; resources of a child;
firmware nodes of a child; parent data and regmaps; suspend and runtime PM;
registration and removal; the regmap interrupt controller; system
controllers; children from the device tree.

The conventions of the hand-written guide are kept by hand in
`../../verbatim/mfd-conventions.md`, and the build inserts that file. These
parts of the hand-written guide are in neither the file nor a question:

- the four statements in the table above that the tree contradicts
- the rule about headers, for the reason given above
- the sentences that tell a reviewer what to report, and the reasons given for
  each convention
- the two code examples

One convention in the file may disagree with a built answer. The file says "do
not create local copies of cells in order to amend them at run time". The check
found that `intel_lpss_assign_devs()` copies its cell for each instance, and
took that for the safe way to amend a cell at probe.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          234        17%     31      1   6.12 to 6.19
reader B          252        24%     18      9   6.12 to 6.14
reader C          287        46%      3     47   6.12 to 6.12

question                       reader A      reader B      reader C   verdict
mfd.core-files                 13% ( 5)       8% ( 6)      41% (11)   weak: reader C
mfd.docs                       17% ( 2)      24% ( 4)      62% ( 3)   weak: reader C
mfd.kconfig                     3% ( 1)      19% ( 2)      40% ( 4)   weak: reader C
mfd.outside-callers            22% ( 3)      32% ( 2)      45% ( 2)   weak: reader C
mfd.shared-headers              9% ( 1)      32% ( 2)      23% ( 1)   middling
mfd.tests                      31% ( 3)      36% ( 2)      57% ( 2)   weak: reader C
mfd.overview                   11% ( 6)      11% ( 8)      29% (15)   middling
mfd.api-variants               23% ( 3)      48% (10)      45% ( 7)   weak: reader B, reader C
mfd.core-state                 19% ( 5)      24% ( 3)      16% ( 3)   middling
mfd.device-type                30% ( 6)      36% ( 4)      40% ( 4)   weak: reader C
mfd.cell-copy                  19% ( 7)      40% (11)      51% ( 7)   weak: reader B, reader C
mfd.cell-written               30% ( 4)      34% ( 3)      77% ( 4)   weak: reader C
mfd.cell-macros                 2% ( 1)      35% ( 3)      84% ( 3)   weak: reader C
mfd.cell-pm-callbacks          11% ( 2)      40% ( 3)      58% ( 2)   weak: reader B, reader C
mfd.get-cell                   28% ( 3)      48% ( 4)      86% ( 4)   weak: reader B, reader C
mfd.device-id                   0% ( 2)      19% ( 3)      53% ( 7)   weak: reader C
mfd.id-uniqueness              24% ( 5)      38% ( 5)      32% ( 4)   middling
mfd.driver-binding             15% ( 5)      25% ( 4)      35% ( 7)   middling
mfd.probe-timing               20% ( 3)      19% ( 5)       1% ( 1)   middling
mfd.sibling-order              17% ( 5)      17% ( 3)      42% ( 5)   weak: reader C
mfd.mem-resources               7% ( 5)      46% ( 6)      40% ( 4)   weak: reader B, reader C
mfd.irq-resources               2% ( 2)       0% ( 0)      40% ( 5)   weak: reader C
mfd.other-resources            25% ( 4)      37% ( 3)      68% ( 4)   weak: reader C
mfd.resource-conflicts         12% ( 2)      21% ( 3)      38% ( 5)   middling
mfd.child-irq-lookup           11% ( 3)      28% ( 5)      68% ( 3)   weak: reader C
mfd.child-dma                  14% ( 4)       8% ( 2)      49% ( 2)   weak: reader C
mfd.of-matching                26% ( 6)       7% ( 4)      59% (17)   weak: reader C
mfd.of-reg                      2% ( 1)      17% ( 1)      16% ( 1)   middling
mfd.of-missing                  4% ( 1)      27% ( 4)      63% ( 5)   weak: reader C
mfd.acpi-companion             14% ( 1)      19% ( 2)      60% ( 7)   weak: reader C
mfd.swnode                     20% ( 3)      40% ( 6)      57% ( 4)   weak: reader B, reader C
mfd.parent-node-reuse          36% ( 7)      38% ( 5)      47% ( 8)   weak: reader C
mfd.platform-data              27% ( 5)      23% ( 4)      20% ( 5)   middling
mfd.parent-data                39% ( 4)      42% ( 5)      22% ( 4)   weak: reader B
mfd.named-regmaps              17% ( 3)       9% ( 3)      25% ( 2)   middling
mfd.regmap-concurrency         33% ( 3)      31% ( 3)      20% ( 4)   middling
mfd.supply-alias                6% ( 2)       0% ( 0)      24% ( 4)   middling
mfd.runtime-pm                  4% ( 3)       9% ( 2)      34% ( 4)   middling
mfd.match-data                 35% ( 7)      27% ( 3)      34% ( 5)   middling
mfd.add-failure                16% ( 3)      18% ( 7)      66% ( 6)   weak: reader C
mfd.remove-scope                4% ( 2)       7% ( 1)      49% ( 5)   weak: reader C
mfd.levels                     13% ( 4)      36% ( 5)      74% ( 4)   weak: reader C
mfd.devm-add                   15% ( 1)      31% ( 2)      43% ( 2)   weak: reader C
mfd.manual-teardown            12% ( 2)      34% ( 3)      35% ( 1)   middling
mfd.hotplug                    25% ( 3)      35% ( 2)      67% ( 2)   weak: reader C
mfd.core-change                16% ( 2)      28% ( 5)      88% ( 5)   weak: reader C
mfd.irq-chip-registration       9% ( 5)      12% ( 3)      42% ( 5)   weak: reader C
mfd.irq-to-children            12% ( 2)       2% ( 1)      55% ( 3)   weak: reader C
mfd.irq-handler-context        32% ( 3)      17% ( 2)      45% ( 3)   weak: reader C
mfd.irq-chip-removal           28% ( 3)      21% ( 3)      16% ( 2)   middling
mfd.irq-chip-fields            17% ( 1)      22% ( 3)      55% ( 2)   weak: reader C
mfd.irq-index                  25% ( 4)      22% ( 2)      34% ( 3)   middling
mfd.irq-sleep                  36% ( 8)      36% ( 4)      54% ( 3)   weak: reader C
mfd.syscon-model                5% ( 5)      31% ( 8)      40% ( 5)   weak: reader C
mfd.syscon-lookups              9% ( 2)       3% ( 3)      51% ( 2)   weak: reader C
mfd.syscon-errors              23% ( 3)      39% ( 5)      59% ( 3)   weak: reader C
mfd.syscon-register            44% ( 5)      53% ( 4)      52% ( 3)   all weak
mfd.syscon-config               3% ( 1)       7% ( 3)      46% ( 3)   weak: reader C
mfd.syscon-locking             19% ( 2)       4% ( 2)      58% ( 1)   weak: reader C
mfd.syscon-binding             16% ( 2)      24% ( 2)      44% ( 1)   weak: reader C
mfd.syscon-child-access        16% ( 2)      25% ( 3)      61% ( 2)   weak: reader C
mfd.simple-mfd                 33% ( 8)      22% (10)      40% ( 6)   weak: reader C
mfd.simple-mfd-binding         19% ( 4)       9% ( 2)      78% ( 3)   weak: reader C
mfd.populate-or-cells          11% ( 2)       8% ( 3)       5% ( 1)   all fair: drop, or shrink to a pointer
mfd.simple-mfd-i2c              9% ( 2)      10% ( 1)      13% ( 3)   all fair: drop, or shrink to a pointer
mfd.binding-layout             33% ( 4)      21% ( 3)      78% ( 5)   weak: reader C
mfd.driver-layout              13% ( 5)      13% ( 4)      29% ( 6)   middling
mfd.bus-split                  15% ( 6)      45% ( 8)      56% ( 8)   weak: reader B, reader C
```

## Wording after the measurement

After the measurement, the wording of some questions was made clearer in both
sets: a sentence that asked three things became two sentences, and a pronoun
became the name it stood for. What each question asks did not change, so the
numbers above still describe the questions.
