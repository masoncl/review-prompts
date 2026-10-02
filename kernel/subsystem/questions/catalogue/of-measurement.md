# Questions: Open Firmware and device tree (measurement set)

- guide: of.md
- title: Open Firmware (Device Tree) Subsystem

A wide set of questions about the device tree core under `drivers/of/` and
`include/linux/of.h` with its sibling headers: the live tree and its nodes,
reference counting, the iterators, property access, address and interrupt
translation, ID maps and MSI, run-time changes and overlays, and the link to
the driver model. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written
guide it will replace is 640 words, so most of what is asked here cannot be in
the built guide; the point is to find which few things must be. Binding
documents and the schema tooling have their own guide and are not covered. The
trimmed set a guide is built from is `../of.md`. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## of.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold node lookup and phandle parsing, typed property reads and the
graph helpers, the firmware-node operations, address translation, interrupt and
MSI parsing, reference counting and changesets, overlays and phandle
resolution, the flat tree and its unflattening, reserved memory, platform
device creation, the sysfs representation and the tests? A table. Start from
`drivers/of/` and `drivers/of/of_private.h`.

## of.entry-points: Entry points

- section: Finding your way
- relevance: 3 - the function to start reading from for each job
- words: 100

For each job (find a node by path, by phandle and by compatible string, read an
integer property, parse one entry of a phandle list, turn a `reg` entry into a
CPU physical address, turn an interrupt specifier into a Linux interrupt
number, create platform devices for a subtree, apply an overlay), which
function do you start reading from? A table.

## of.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - a change has to keep two kinds of test passing
- words: 80

Which files under `Documentation/devicetree/` describe the kernel API, the
usage model, changesets, overlays and the unit tests, and what in the tree
exercises a change to `drivers/of/`: which configuration options build the
tests, when do they run, and how is their console output checked? Start from
`drivers/of/Kconfig`.

## of.config-options: Configuration options

- section: Finding your way
- relevance: 4 - several functions compile to nothing in most kernels
- words: 90

Which configuration options gate which parts of `drivers/of/` (dynamic changes,
overlays, the sysfs view, address and interrupt translation, the flat tree, the
PROM-based tree), which select which, and what do callers get for the functions
of a part that is compiled out? Start from `drivers/of/Kconfig` and
`drivers/of/Makefile`.

# The live tree

## of.node-structure: Nodes and tree links

- section: Nodes and properties
- relevance: 4 - what every lookup walks
- words: 90

What does `struct device_node` hold, how are nodes linked into a tree, how is a
walk over every node done without a global list, and which global node pointers
does the core keep? Start from `include/linux/of.h` and
`__of_find_all_nodes()`.

## of.node-flags: Node flags

- section: Nodes and properties
- relevance: 4 - the flags decide whether memory is freed and devices made
- words: 90

Give a table of the flag bits kept in a node's `_flags`, saying who sets and
clears each and what reads it. Start from `OF_DYNAMIC` in `include/linux/of.h`.

## of.locks: Locks

- section: Nodes and properties
- relevance: 5 - which calls may sleep and which run with interrupts off
- words: 100

Which locks protect the live tree, what kind is each, what does each protect,
in what order are they taken, and which common lookup functions take one and so
must not be called with it held? Start from `drivers/of/base.c` and
`drivers/of/of_private.h`.

## of.early-fdt: Flat tree before unflattening

- section: Nodes and properties
- relevance: 3 - early code cannot use the node API
- words: 80

Before the tree is unflattened, which functions read the flat blob, what may
they be called from, and at what point in boot do `struct device_node` lookups
start to work? Who owns the memory the unflattened nodes and property values
point into? Start from `drivers/of/fdt.c`.

# Reference counting

## of.refcount-basics: Node reference counts

- section: Holding a node
- relevance: 5 - what a leak or an extra put actually does
- words: 100

What do `of_node_get()` and `of_node_put()` do in a kernel with dynamic device
tree support and in one without, which nodes are ever freed, and what does the
release function check and print when the count reaches zero? Start from
`drivers/of/dynamic.c` and `of_node_release()`.

## of.acquiring-functions: Functions that return a reference

- section: Holding a node
- relevance: 5 - each one needs a matching put
- words: 110

Which node lookup functions a driver is likely to call return a node with its
reference count raised, and which commonly used ways of reaching a node return
a pointer with no reference taken? Give two lists. Start from
`drivers/of/base.c`.

## of.from-argument: Lookups that consume an argument

- section: Holding a node
- relevance: 5 - a put on the argument afterwards is one too many
- words: 90

Which lookup and step functions drop the reference on the node passed in as
their starting point or previous position, and which take such an argument and
leave its count alone? What does that mean for a caller that wants to keep
using the node it passed in? Start from `of_get_next_child()`,
`of_get_next_parent()` and `of_find_node_by_name()`.

## of.iterator-macros: Iterator macros

- section: Holding a node
- relevance: 5 - the rules differ by macro and are not in the name
- words: 120

Give a table of the node and property iterator macros in `include/linux/of.h`
and `include/linux/of_graph.h`: for each, the function it steps with, whether
the loop variable holds a reference during the body, whether the macro declares
the variable itself with automatic cleanup, and what lock if any the caller
must hold.

## of.iterator-put-usage: Puts inside iterator loops

- section: Holding a node
- relevance: 5 - the commonest device tree bug in drivers
- words: 100

What usage of `of_node_put()` inside or after a node iterator loop is unsafe,
and what that looks similar is correct? Cover leaving the loop early, going
round again, keeping the node after the loop, and the iterators that clean up
automatically. Name in-tree code that shows the correct forms.

## of.scoped-cleanup: Automatic cleanup of nodes

- section: Holding a node
- relevance: 4 - new code is written this way and the pitfalls are new too
- words: 90

How is a node pointer declared so that its reference is dropped when it goes
out of scope, how is a node handed out of such a scope without being dropped,
and what usage of automatic cleanup on a node is unsafe while looking like the
correct form? Start from `DEFINE_FREE` in `include/linux/of.h` and
`of_graph_get_port_by_id()`.

## of.borrowed-pointers: Keeping a node pointer

- section: Holding a node
- relevance: 4 - decides whether a stored pointer needs its own reference
- words: 80

When code stores a node pointer in a longer-lived structure, or uses a
device's `of_node`, what must it do about the reference count, and which core
helpers take that reference for it? What usage is unsafe, and what that looks
similar is correct?

## of.phandle-args-ref: Phandle lists and references

- section: Holding a node
- relevance: 4 - the reference hides in an output structure
- words: 100

How is a property holding a list of phandles with arguments parsed: which
variants exist for a named cell count, a fixed one and an optional one, what
does each return for an empty entry and for a malformed one, how many argument
cells fit, and who must drop which reference, including when a loop over the
iterator is left early? Start from `__of_parse_phandle_with_args()` and
`of_phandle_iterator_next()`.

# Properties

## of.property-read-returns: Typed property reads

- section: Reading properties
- relevance: 4 - callers test for the wrong error
- words: 90

What do the integer, array and string property read functions return when the
property is missing, when it is present with no value, and when it is shorter
or longer than asked, and is the output argument written on failure? What do
the variable-length array forms return on success? Start from
`drivers/of/property.c`.

## of.bool-and-present: Boolean and presence tests

- section: Reading properties
- relevance: 4 - the two look interchangeable and are not
- words: 60

Which function tests a boolean property and which tests that any property is
present, what happens when the boolean one is used on a property that has a
value, and where is each implemented?

## of.property-value-lifetime: Lifetime of property values

- section: Reading properties
- relevance: 4 - decides whether a returned pointer can be kept
- words: 90

How long does a pointer returned by `of_get_property()`, `of_find_property()`
or `of_property_read_string()` stay valid, what byte order is the data in, and
what happens to a property's memory when it is removed or replaced in the live
tree? Start from `__of_remove_property()`.

## of.property-iterators: Loops over property values

- section: Reading properties
- relevance: 3 - the macro arguments have changed
- words: 70

How are the macros that loop over the 32-bit values and over the strings of a
property written: what arguments does each take, which variables must the
caller declare, and may the loop body change the value through them? Start
from `of_prop_next_u32()` and `of_prop_next_string()`.

## of.status-values: Status property

- section: Reading properties
- relevance: 4 - "available" is not the only state the core knows
- words: 90

Which values of a node's `status` property does the core recognise, which
helper tests for each, and which child and CPU iterators skip nodes in which
state? What does a missing `status` mean? Start from
`__of_device_is_status()` in `drivers/of/base.c`.

## of.compatible-matching: Compatible matching

- section: Reading properties
- relevance: 3 - the best match is not the first match
- words: 90

How does the core score a node against a compatible string, a device type and
a name, how does that decide which entry of a match table wins, and which
helpers match the machine (the root node) instead of a device? Start from
`__of_device_is_compatible()` and `of_match_node()`.

# Addresses, interrupts and ID maps

## of.address-translation: Address translation

- section: Translating what the tree says
- relevance: 4 - failure is a value, not an errno
- words: 100

How is a `reg` address translated to a CPU physical address: how is the bus
type of each level chosen, what does a missing or empty `ranges` mean, what is
returned on failure, and how does DMA address translation differ? Start from
`of_translate_address()` and `of_translate_one()` in `drivers/of/address.c`.

## of.irq-parse: Interrupt parsing

- section: Translating what the tree says
- relevance: 4 - two properties and a map, with a reference at the end
- words: 100

How is a device's interrupt resolved to a controller and a specifier: which
properties are tried in which order, how is the interrupt parent found, how is
`interrupt-map` applied and when is it ignored, and what reference does the
caller hold on success? Start from `of_irq_parse_one()` and
`of_irq_parse_raw()`.

## of.irq-get-returns: Interrupt lookup results

- section: Translating what the tree says
- relevance: 4 - zero, negative and deferral mean different things
- words: 70

What do `of_irq_get()`, `of_irq_get_byname()` and `irq_of_parse_and_map()`
return on success, when the interrupt cannot be mapped, when the controller has
no domain yet and on a parse error, and how should a probe function treat each?

## of.id-map: ID map translation

- section: Translating what the tree says
- relevance: 5 - the interface may differ from what a reader remembers
- words: 110

How does the tree translate a device ID through a map property such as the
ones used for IOMMUs and for MSI controllers: what arguments does the
translating function take, what does it give back when the property is absent,
when no entry matches and when one does, how is the number of output cells
decided, and who owns the node it hands back? Start from `of_map_id()` in
`drivers/of/base.c`.

## of.msi-bindings: MSI controller lookup

- section: Translating what the tree says
- relevance: 4 - a platform using the other form gets no MSIs
- words: 100

Which device tree properties can tell the kernel which MSI controller a device
uses and which ID it presents there, which function handles each form, how is
the controller's cell-count property interpreted including when it is absent,
and who holds a reference on a controller node that is handed back? Start from
`of_msi_xlate()` and `of_msi_get_domain()` in `drivers/of/irq.c`.

# Changing the tree at run time

## of.live-tree-changes: Single changes to the live tree

- section: Dynamic changes
- relevance: 3 - the order of lock, change and notifier
- words: 90

How do the functions that attach or detach one node, or add, remove or update
one property, order taking the locks, changing the tree, updating sysfs and
calling the notifier chain, and what do the forms with two leading underscores
leave to the caller? Start from `of_attach_node()` and `of_add_property()`.

## of.changesets: Changesets

- section: Dynamic changes
- relevance: 4 - the supported way to change the tree, with its own lifetime rules
- words: 110

What is the life of a changeset from init to destroy, what happens when one
entry fails to apply or to revert, when are notifiers sent relative to the
tree changes and under which lock, what reference does an entry hold, and what
does destroying an applied changeset do? Start from `of_changeset_apply()` and
`of_changeset_destroy()` in `drivers/of/dynamic.c`.

## of.reconfig-notifiers: Reconfiguration notifiers

- section: Dynamic changes
- relevance: 3 - the callback sees the tree after the change
- words: 90

Which actions does the reconfiguration notifier chain deliver, what does the
data passed with each hold, may a callback sleep or veto the change, and how
does a bus decide from a notification whether to create or remove a device?
Start from `of_reconfig_notify()` and `of_reconfig_get_state_change()`.

## of.overlay-apply: Applying an overlay

- section: Overlays
- relevance: 4 - the error path is not the usual one
- words: 110

What are the arguments and the result of the function that applies an overlay
blob, what steps does it go through and under which locks, what must the caller
do when it returns an error, and when does the core refuse every further
overlay operation? Start from `of_overlay_fdt_apply()` in
`drivers/of/overlay.c`.

## of.overlay-remove: Removing an overlay

- section: Overlays
- relevance: 4 - pointers into a removed overlay dangle
- words: 100

When is removing an overlay refused, in what order are the notifiers called,
when is the overlay's memory freed, and what may and may not keep a pointer to
an overlay's nodes or property values? What does the core check about node
reference counts when the overlay's changeset is destroyed? Start from
`of_overlay_remove()` and `Documentation/devicetree/overlay-notes.rst`.

# The driver model

## of.platform-populate: Creating platform devices

- section: Devices from nodes
- relevance: 4 - which nodes become devices, and only once
- words: 100

Which nodes get a platform device when a subtree is populated, which are
skipped, how do the populated flags stop a second device being made and how are
they cleared again, and what does looking a device up by its node hand back
that the caller must release? Start from `of_platform_populate()` and
`of_platform_bus_create()` in `drivers/of/platform.c`.

## of.fwnode: Firmware node handles

- section: Devices from nodes
- relevance: 3 - generic property code lands in these callbacks
- words: 80

How is a `struct device_node` tied to a `struct fwnode_handle`, how does code
convert in each direction and what does each conversion return for a handle of
another kind or NULL, and do the firmware-node get and put operations share the
node's reference count? Start from `of_fwnode_ops` in `drivers/of/property.c`.

## of.fw-devlink: Supplier links from properties

- section: Devices from nodes
- relevance: 3 - a new binding with phandles usually needs an entry here
- words: 90

How does the core turn phandle properties into supplier links between
devices: where is the table of recognised properties, what does each entry
supply, which are treated as optional, and what must someone adding a new
provider binding do there? Start from `of_supplier_bindings` and
`of_link_property()`.

# Changing the implementation

## of.change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - the code is built in more configurations than a developer tests
- words: 100

What must a change to `drivers/of/` or to `include/linux/of.h` keep working
besides the default build: the stubs for kernels without device tree support,
the inline reference counting when dynamic support is off, the architectures
that build the tree from PROM calls, the boot-time unit tests and their
expected console messages, and the KUnit tests? Say where each lives.
