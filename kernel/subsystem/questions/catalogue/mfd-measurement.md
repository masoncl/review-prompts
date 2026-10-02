# Questions: MFD (measurement set)

- guide: mfd.md
- title: Multi-Function Devices (MFD)

A wide set of questions about the MFD core in `drivers/mfd/mfd-core.c` and
`include/linux/mfd/core.h`, and about the helpers that MFD drivers share: the
platform devices that cells become, firmware nodes for children, regmap and
the regmap interrupt controller as parent drivers use them, the system
controller helper, and the `simple-mfd` compatible. The set is used to measure
what a model already knows, before anyone decides what the built guide should
hold. The questions are about the core and about what every parent and child
driver has to do. They are not about one chip. The hand-written guide that the
built guide will replace is 902 words, and it was never checked against
current sources. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## mfd.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Which files hold the code that registers and removes the children of a
multi-function device, the lookup of system controller regmaps, the generic
I2C parent driver, and the code that creates devices for the children of a
`simple-mfd` node? Which header declares the core API? Start from
`drivers/mfd/Makefile`.

## mfd.docs: Documentation files

- section: Finding your way
- relevance: 3 - says whether a rule can be looked up or lives only in the code

Where does this tree document the MFD core API, the device tree conventions
for multi-function devices, and the ACPI handling of their children? Is there
a document for the core under `Documentation/driver-api/`? Start from
`Documentation/devicetree/bindings/mfd/`.

## mfd.kconfig: Kconfig symbols

- section: Finding your way
- relevance: 3 - a new parent driver that gets this wrong fails to link

Which Kconfig symbols build the MFD core and the system controller helper, and
how does a driver get each of them built? What does the core symbol select?
What does the whole MFD menu depend on? Start from `drivers/mfd/Kconfig`.

## mfd.outside-callers: Callers outside the directory

- section: Finding your way
- relevance: 2 - says whether a caller in another directory is unusual

Does code outside `drivers/mfd/` register children through the MFD core in
this tree? What must the Kconfig entry of such a driver do? Start from the
callers of `mfd_add_devices()` and `devm_mfd_add_devices()`.

## mfd.shared-headers: Shared headers

- section: Finding your way
- relevance: 2 - a new driver has to put its header somewhere

Where do the headers live that a parent driver shares with child drivers in
other directories, and where do the headers live that only files under
`drivers/mfd/` include? Start from `include/linux/mfd/`.

## mfd.tests: Tests of the core

- section: Finding your way
- relevance: 2 - says what a change to the core can be run against

Does this tree have KUnit tests or selftests for the MFD core, for the system
controller helper, or for the regmap interrupt controller? If it has none for
one of them, say so. Start from `drivers/base/regmap/regmap-kunit.c`.

# The core

## mfd.overview: Parent, cell and child

- section: Objects and API
- relevance: 5 - nothing else makes sense without it

What is the MFD core for, and how do a parent device, a `struct mfd_cell` and
the child device made from the cell relate to each other? On which bus do the
children sit when the parent is on I2C, SPI, PCI or USB? Start from
`mfd_add_device()`.

## mfd.api-variants: Add and remove functions

- section: Objects and API
- relevance: 4 - the variants differ in what they remove and when

Which functions does the core export for adding and for removing children,
and which one is used in which case? Start from `include/linux/mfd/core.h`.

## mfd.core-state: Global state and locks

- section: Objects and API
- relevance: 3 - a change to registration has to keep the list consistent

What global state does the MFD core keep, and which lock protects that state?
When are entries added and removed? Start from `drivers/mfd/mfd-core.c`.

## mfd.device-type: Device type of children

- section: Objects and API
- relevance: 3 - removal depends on it

How does the core mark the devices it creates, and what in the core relies on
that mark? Start from `mfd_remove_devices_fn()`.

# Cells

## mfd.cell-copy: Cell storage and lifetime

- section: Cell contents
- relevance: 5 - decides whether a cell built on the stack or changed later is a bug

What does the core keep of a cell after `mfd_add_devices()` returns, and who
frees what the core keeps? What does a child see through `mfd_get_cell()`?
What are the requirements for the storage of a cell array, and of the data
that its members point to, in order to assure safe usage? Start from
`mfd_add_device()` and `platform_device_release()`.

## mfd.cell-written: Cells written at probe

- section: Cell contents
- relevance: 4 - a common pattern in parent drivers

What are the requirements for a driver that writes members of a cell before
the driver registers the cell, in order to assure safe usage? Start from
`drivers/mfd/intel-lpss.c` and `drivers/mfd/88pm800.c`.

## mfd.cell-macros: Cell initialiser macros

- section: Cell contents
- relevance: 3 - the argument order is easy to get wrong

Which macros does this tree offer to initialise a `struct mfd_cell`, and which
one is used in which case? Which members of the structure does no macro set?
Start from `MFD_CELL_ALL`.

## mfd.cell-pm-callbacks: Cell suspend and resume

- section: Cell contents
- relevance: 3 - a patch that sets them expects them to run

Does anything in this tree call the `suspend` and `resume` members of
`struct mfd_cell`? In what order are the children of a multi-function device
and their parent suspended and resumed over system sleep?

## mfd.get-cell: Cell lookup from a child

- section: Cell contents
- relevance: 3 - used as a test for how a device was created

What does `mfd_get_cell()` return for a platform device that the MFD core did
not create, and what does code in this tree use the function for?

# Child devices

## mfd.device-id: Platform device id

- section: Names and binding
- relevance: 5 - the arithmetic is not what the argument names suggest

How does the core compute the id of a child platform device from the `id`
argument of `mfd_add_devices()` and the `id` member of the cell? What is the
result for `PLATFORM_DEVID_AUTO`, for `PLATFORM_DEVID_NONE` and for a base of
zero or more, and what device name follows from each? Start from
`mfd_add_device()`.

## mfd.id-uniqueness: Unique child names

- section: Names and binding
- relevance: 4 - a second instance of the parent fails to probe

What are the requirements for the `id` argument and for the ids in the cells
in order to assure safe usage when a system can hold more than one instance of
the parent, or when two cells have the same name? What fails when two children
get the same device name? Start from `platform_device_add()`.

## mfd.driver-binding: Child driver binding

- section: Names and binding
- relevance: 4 - a child module that is not loaded automatically looks like a missing device

How is a child bound to its driver, and which MODALIAS does the kernel emit
for a child that has a device tree node, for one that has an ACPI companion,
and for one that has neither? What must the module of a child driver declare
so that the module is loaded automatically in each case? Start from
`platform_match()` and `platform_uevent()` in `drivers/base/platform.c`.

## mfd.probe-timing: Child probe timing

- section: Names and binding
- relevance: 5 - decides what the parent must finish before it adds children

Does `mfd_add_devices()` wait for the child drivers to probe, and does a child
probe that fails make the call fail? What are the requirements for what the
parent has set up before the call in order to assure safe usage? Start from
`platform_device_add()`.

## mfd.sibling-order: Order among children

- section: Names and binding
- relevance: 3 - children often need a regulator, a clock or a GPIO from a sibling

What does the core guarantee about the order in which the children of one
parent are registered and probed? How does a child that needs a resource
provided by another child of the same parent get that resource?

# Resources

## mfd.mem-resources: Memory resources

- section: Resource translation
- relevance: 4 - offsets and absolute addresses look the same in a cell

How does the core turn a memory resource of a cell into the resource of the
child, with a `mem_base` argument and without one? What is the parent of the
resulting resource, and what follows for a child that requests the region?
Start from `mfd_add_device()`.

## mfd.irq-resources: Interrupt resources

- section: Resource translation
- relevance: 5 - the same number in a cell is read differently with a domain and without

How does the core turn an interrupt resource of a cell into the resource of
the child when `mfd_add_devices()` gets an interrupt domain, and when it gets
only `irq_base`? What does the core do with a resource that spans more than
one interrupt? Start from `mfd_add_device()`.

## mfd.other-resources: Register and other resources

- section: Resource translation
- relevance: 3 - used by parents on I2C and SPI to hand out register ranges

What does the core do with a cell resource that is neither memory nor an
interrupt, such as one of type `IORESOURCE_REG`? How does a child read such a
resource? Start from `drivers/mfd/ocelot-core.c`.

## mfd.resource-conflicts: Resource conflict check

- section: Resource translation
- relevance: 3 - confined to parents with an ACPI companion

When does the core check a child resource for a conflict, and against what?
What happens to the registration when the check finds a conflict? How does a
cell turn the check off? Start from `acpi_check_resource_conflict()`.

## mfd.child-irq-lookup: Interrupt lookup in a child

- section: Resource translation
- relevance: 4 - two sources can describe the same interrupt

When a child calls `platform_get_irq()` or `platform_get_irq_byname()`, where
does the number come from if the child has both a firmware node that
describes interrupts and interrupt resources from its cell? Start from
`platform_get_irq_affinity()`.

## mfd.child-dma: DMA settings of children

- section: Resource translation
- relevance: 3 - matters for children that do DMA through the parent

Which DMA settings does a child get from its parent when the core creates the
child, and is each one copied or shared? Start from `mfd_add_device()`.

# Firmware nodes

## mfd.of-matching: Device tree node matching

- section: Nodes for children
- relevance: 5 - decides which child gets which node

How does the core choose the device tree node of a child from
`of_compatible`, and which nodes does the core search? What stops two cells
from getting the same node? Start from `mfd_match_of_node_to_dev()`.

## mfd.of-reg: Matching by address

- section: Nodes for children
- relevance: 3 - only for several children with one compatible

What do `of_reg` and `use_of_reg` in a cell do, and what is each of the two
members for? Which value from the node does the core compare? Start from
`mfd_match_of_node_to_dev()`.

## mfd.of-missing: Disabled and missing nodes

- section: Nodes for children
- relevance: 5 - a child that does not appear, or appears without a node, is not visible in a diff

What does the core do with a cell whose `of_compatible` matches only nodes
that are disabled, and with a cell whose `of_compatible` matches no node? What
does `mfd_add_devices()` return in each case? Start from `mfd_add_device()`.

## mfd.acpi-companion: ACPI companion of a child

- section: Nodes for children
- relevance: 4 - decides which ACPI resources a child sees

How does a child get its ACPI companion, with `acpi_match` in its cell and
without? What do the two members of `struct mfd_cell_acpi_match` select, and
what happens to a device tree node that the core has already set on the child?
Start from `mfd_acpi_add_device()`.

## mfd.swnode: Software nodes

- section: Nodes for children
- relevance: 3 - used by a growing number of parent drivers

How does the core attach the software node that a cell names in `swnode`, and
when is the software node removed? What are the requirements for a software
node that a cell names, in order to assure safe usage when more than one
instance of the parent exists? Start from `device_add_software_node()`.

## mfd.parent-node-reuse: Parent node reuse

- section: Nodes for children
- relevance: 4 - a common pattern in child drivers, with side effects in the driver core

How does a child that has no device tree node of its own read properties from
the node of its parent? What are the requirements for a child driver that sets
its own node to the node of its parent, in order to assure safe usage? Start
from `device_set_of_node_from_dev()`.

# Shared state

## mfd.platform-data: Platform data of a child

- section: Data shared with children
- relevance: 4 - a child dereferences what the parent passed

How does the core pass the `platform_data` of a cell to the child, and what
does the child get when `pdata_size` is zero? What are the requirements for
pointers inside the platform data in order to assure safe usage? Start from
`platform_device_add_data()`.

## mfd.parent-data: Parent data in children

- section: Data shared with children
- relevance: 5 - every child driver does this

How do child drivers in this tree reach the regmap and the driver data of
their parent? What are the requirements for when the parent creates its regmap
and sets its driver data, in order to assure safe usage by the children? Start
from `dev_get_regmap()` and `dev_get_drvdata()`.

## mfd.named-regmaps: Several regmaps per parent

- section: Data shared with children
- relevance: 3 - only parents with more than one register space

How does `dev_get_regmap()` choose a regmap when the parent has more than one,
and what does the function return when the parent has none? Where does the
function look for the regmap?

## mfd.regmap-concurrency: Shared regmap concurrency

- section: Data shared with children
- relevance: 4 - children run at the same time on one register space

What does a regmap that several children share guarantee when two children
access it at the same time? What are the requirements for a child that needs a
sequence of several accesses to be atomic, in order to assure safe usage?
Start from `regmap_update_bits()`.

## mfd.supply-alias: Parent regulator supplies

- section: Data shared with children
- relevance: 3 - confined to a few audio codecs

What do `parent_supplies` and `num_parent_supplies` in a cell do, and when
does the core set up and remove what they describe? Start from
`regulator_bulk_register_supply_alias()`.

## mfd.runtime-pm: Runtime PM of children

- section: Data shared with children
- relevance: 3 - a child that touches registers needs the parent awake

What does `pm_runtime_no_callbacks` in a cell do, and at which step of
registration does the core apply it? How does runtime PM of a child relate to
runtime PM of its parent?

## mfd.match-data: Variant selection

- section: Data shared with children
- relevance: 4 - most parent drivers support several chips

How do parent drivers in this tree choose the set of cells for a chip variant?
What are the requirements for the values that a driver stores as match data in
its device id tables, in order to assure safe usage with
`device_get_match_data()`?

# Adding and removing

## mfd.add-failure: Failure while adding

- section: Registration and removal
- relevance: 5 - decides what an error path still has to undo

When one cell of an `mfd_add_devices()` call fails to register, which devices
are still registered when the call returns? Is the result different when an
earlier call added children to the same parent, or when the cell that fails is
the first cell of the call?

## mfd.remove-scope: Scope of removal

- section: Registration and removal
- relevance: 5 - removal is by parent, and a reviewer has to know what that covers

Which devices does `mfd_remove_devices()` remove, and in what order? How does
the function tell those devices from the other children of the parent? What
does the function undo for each device besides unregistering it? Start from
`mfd_remove_devices_fn()`.

## mfd.levels: Dependency levels

- section: Registration and removal
- relevance: 4 - decides which removal call takes which child

What does `level` in a cell mean, and which cells does each of
`mfd_remove_devices()`, `mfd_remove_devices_late()` and the release of
`devm_mfd_add_devices()` remove? What are the requirements for a driver that
sets `MFD_DEP_LEVEL_HIGH` in a cell, in order to assure safe usage? Start from
`drivers/mfd/madera-core.c`.

## mfd.devm-add: Managed registration

- section: Registration and removal
- relevance: 5 - most parent drivers use it

What does `devm_mfd_add_devices()` register for release, and on which device?
When does the release run relative to the other managed resources of the
parent? What are the requirements for the device passed as the first argument,
in order to assure safe usage?

## mfd.manual-teardown: Manual removal with devres

- section: Registration and removal
- relevance: 5 - a recurring source of use after free on unbind

What are the requirements for a parent driver that adds children with
`mfd_add_devices()` and also holds resources through devres that the children
use, in order to assure safe usage? Cover the removal of the driver and a
probe that fails after the children were added.

## mfd.hotplug: Hot-pluggable parents

- section: Registration and removal
- relevance: 3 - confined to parents on USB and similar buses

What does `mfd_add_hotplug_devices()` pass to `mfd_add_devices()`? What are
the requirements for a parent on a bus where the device can disappear while
its children are in use, in order to assure safe usage? Start from
`drivers/mfd/dln2.c`.

## mfd.core-change: Changes to registration

- section: Registration and removal
- relevance: 4 - what a patch to the core has to keep

What must a change to `mfd_add_device()` preserve about the order of its
steps, and about what each failure path undoes? Which code outside
`drivers/mfd/mfd-core.c` depends on what the function sets in the platform
device?

# Interrupts

## mfd.irq-chip-registration: Interrupt chip registration

- section: Regmap interrupt controller
- relevance: 4 - the flags and the base are passed by every parent

What does `devm_regmap_add_irq_chip()` do with the primary interrupt of the
parent: how is the interrupt requested, and with which flags? What does a
non-zero `irq_base` do, and which firmware node does the new interrupt domain
get? Start from `regmap_add_irq_chip_fwnode()`.

## mfd.irq-to-children: Interrupts for children

- section: Regmap interrupt controller
- relevance: 5 - parent and child have to agree on one of several ways

By which means do children in this tree get their interrupt numbers from a
parent that uses a regmap interrupt chip, and which one is used in which case?
Start from `regmap_irq_get_domain()` and `regmap_irq_get_virq()`.

## mfd.irq-handler-context: Child handler context

- section: Regmap interrupt controller
- relevance: 5 - a wrong request fails at run time, not at build time

In which context does the handler of a child interrupt run when the parent
uses a regmap interrupt chip? What are the requirements for how a child
requests such an interrupt, in order to assure safe usage? Start from
`regmap_irq_thread()`.

## mfd.irq-chip-removal: Interrupt chip removal

- section: Regmap interrupt controller
- relevance: 4 - the order of teardown is easy to get wrong with devres

What does `regmap_del_irq_chip()` do to the interrupts that children have
mapped or requested? What are the requirements for the order of removing the
children and removing the interrupt chip, in order to assure safe usage?

## mfd.irq-chip-fields: Interrupt chip description

- section: Regmap interrupt controller
- relevance: 3 - partly caught at registration

Which combinations of members of `struct regmap_irq_chip` does registration
refuse? What do `mask_base` and `unmask_base` each mean for the value that is
written to mask an interrupt? Start from `regmap_add_irq_chip_fwnode()`.

## mfd.irq-index: Interrupt index lookup

- section: Regmap interrupt controller
- relevance: 3 - the index often comes from a table in the child

What does `regmap_irq_get_virq()` return for an index that the chip does not
describe? What are the requirements for the index that a caller passes, in
order to assure safe usage?

## mfd.irq-sleep: Interrupts across system sleep

- section: Regmap interrupt controller
- relevance: 4 - the handler needs a bus that may be suspended

What are the requirements for the primary interrupt of a parent on I2C or SPI
across system suspend and resume, in order to assure safe usage? How does a
child make its interrupt a wakeup source through a regmap interrupt chip, and
what does the chip then do with the primary interrupt? Start from
`regmap_irq_set_wake()`.

# System controllers

## mfd.syscon-model: Syscon regmap creation

- section: Syscon helper
- relevance: 5 - decides who owns the regmap and when the regmap exists

Does this tree have a platform driver that binds to nodes with the `syscon`
compatible? When is the regmap of a system controller created, and which
device owns the regmap? Is the regmap ever freed? Start from
`of_syscon_register()`.

## mfd.syscon-lookups: Syscon lookup functions

- section: Syscon helper
- relevance: 4 - the variants accept different nodes

Which functions look up the regmap of a system controller, and which one is
used in which case? How do `syscon_node_to_regmap()` and
`device_node_to_regmap()` differ in the nodes they accept, and in what they do
with clocks and resets?

## mfd.syscon-errors: Syscon lookup results

- section: Syscon helper
- relevance: 5 - callers test for the wrong value

What does each syscon lookup function return when the property or the node is
missing, when the node lacks the `syscon` compatible, and when
`CONFIG_MFD_SYSCON` is off? What are the requirements for how a caller tests
the result of `syscon_regmap_lookup_by_phandle_optional()`, in order to assure
safe usage?

## mfd.syscon-register: Registering a regmap

- section: Syscon helper
- relevance: 4 - the order against the first lookup matters

What does `of_syscon_register_regmap()` do, and what does it return when the
node already has a regmap? Can a registration be undone? What are the
requirements for when a driver calls the function, and for the lifetime of the
regmap and of the node, in order to assure safe usage?

## mfd.syscon-config: Syscon regmap configuration

- section: Syscon helper
- relevance: 3 - decides which accesses the regmap accepts

Which properties of the device tree node shape the regmap that the syscon code
creates? What is the register width when the node gives none, and how does the
code set the highest register? What does the code do when the node names a
hardware spinlock? Start from `of_syscon_register()`.

## mfd.syscon-locking: Syscon list locking

- section: Syscon helper
- relevance: 3 - limits the contexts a lookup may run in

Which lock protects the list of system controllers, and in which contexts may
the lookup functions be called? Start from `device_node_get_regmap()`.

## mfd.syscon-binding: Syscon binding rules

- section: Syscon helper
- relevance: 3 - new device trees are checked against it

What does the schema require of the `compatible` property of a node that
contains `syscon`, alone and together with `simple-mfd`? Where is a new syscon
compatible added? Start from
`Documentation/devicetree/bindings/mfd/syscon-common.yaml` and
`Documentation/devicetree/bindings/mfd/syscon.yaml`.

## mfd.syscon-child-access: Children of a syscon node

- section: Syscon helper
- relevance: 3 - the usual way a child of a system controller finds its registers

How does the driver of a child node of a system controller get the regmap of
its parent node in this tree? Start from the callers of
`syscon_node_to_regmap()`.

# Children from the device tree

## mfd.simple-mfd: The simple-mfd compatible

- section: Populating from the device tree
- relevance: 5 - a device tree that relies on it may get no child devices

Which code acts on the `simple-mfd` compatible, and under which conditions are
devices created for the children of such a node? Are devices created for the
children when the node is a child of an I2C or SPI controller? Start from
`of_platform_default_populate()`.

## mfd.simple-mfd-binding: Driver for simple-mfd nodes

- section: Populating from the device tree
- relevance: 3 - explains a driver bound to a node that needs none

Which driver, if any, binds to a node whose compatible list contains
`simple-mfd`, and when does that driver decline the node? Start from
`drivers/bus/simple-pm-bus.c`.

## mfd.populate-or-cells: Populate or cells

- section: Populating from the device tree
- relevance: 4 - the two ways differ in how the children are removed

When does a parent driver in this tree create its children with
`devm_of_platform_populate()`, and when with `mfd_add_devices()`? What does
`mfd_remove_devices()` do to children that were created from the device tree,
and what removes those children?

## mfd.simple-mfd-i2c: Generic I2C parent

- section: Populating from the device tree
- relevance: 3 - the place for a chip that needs no code of its own

What does the driver in `drivers/mfd/simple-mfd-i2c.c` do for a device, and
how does the driver choose between cells and device tree children? Which
regmap configuration does the driver use when the match data names none? What
does adding a new device to the driver take?

## mfd.binding-layout: Binding conventions

- section: Populating from the device tree
- relevance: 2 - binding review has its own guide

What does this tree say about when the `simple-mfd` compatible may be used in
a binding, and about the `ranges` property of such a node? Start from
`Documentation/devicetree/bindings/mfd/mfd.txt`.

# Driver layout

## mfd.driver-layout: Split between directories

- section: Where driver code goes
- relevance: 3 - a patch that adds a chip touches several directories

Where does this tree put the driver for one function of a multi-function chip,
and what do the drivers under `drivers/mfd/` hold besides the registration of
children? Start from `drivers/mfd/max77650.c` and the drivers of its children.

## mfd.bus-split: Core and bus files

- section: Where driver code goes
- relevance: 2 - a layout convention that a search shows

How do parent drivers in this tree that support both I2C and SPI split their
code between files, and in which file do the cells and the call to the MFD
core go? Start from `drivers/mfd/wm831x-core.c`.
