# Questions: Hardware Monitoring (measurement set)

- guide: hwmon.md
- title: Hardware Monitoring Subsystem

A wide set of questions about the hardware monitoring core in
`drivers/hwmon/hwmon.c` and the headers `include/linux/hwmon.h` and
`include/linux/hwmon-sysfs.h`: the registration functions, the channel
description a driver hands over, the callbacks and what the core does with
their results, the lock the core holds, event notification, thermal zones, the
PEC attribute, the sysfs interface that userspace relies on, the legacy
interfaces, and the PMBus core that many drivers share. The questions are
about the core and about what every driver must do. They are not about any one
chip driver. The set is used to measure what a model already knows, before
anyone decides which questions the built guide needs. The hand-written guide
that the built guide will replace is 267 words, and it was never checked
against current sources. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## hwmon.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Which files hold the hwmon core, its public headers, its trace events and its
build options? Which directories under `drivers/hwmon/` hold drivers that
share a core of their own? Start from `drivers/hwmon/hwmon.c` and
`include/linux/hwmon.h`.

## hwmon.docs: Documentation files

- section: Finding your way
- relevance: 4 - several rules for drivers are stated only there

Which files under `Documentation/` are the authority on the driver interface,
on the sysfs names and units, and on what the maintainers expect of a patch?
Where does the description of a single driver go? Start from
`Documentation/hwmon/index.rst`.

## hwmon.shared-helpers: Shared helper code

- section: Finding your way
- relevance: 3 - a change to a helper reaches every driver that uses it

Which code under `drivers/hwmon/` is shared by several chip drivers and is not
a driver itself, and what is each piece for? Start from
`drivers/hwmon/hwmon-vid.c`, `drivers/hwmon/lm75.h` and
`drivers/hwmon/sch56xx-common.c`.

## hwmon.callers-elsewhere: Drivers outside the directory

- section: Finding your way
- relevance: 4 - decides whether a registration in another subsystem is normal in this tree

Does code outside `drivers/hwmon/` register hwmon devices in this tree, and in
which parts of the tree? How does `MAINTAINERS` decide that a patch to such
code goes to the hwmon mailing list?

## hwmon.build-deps: Build dependencies

- section: Finding your way
- relevance: 4 - a wrong dependency fails to link in one configuration only

What does `include/linux/hwmon.h` provide when `CONFIG_HWMON` is disabled, and
when it is a module and the caller is built in? What are the requirements for
the Kconfig entry and the code of a driver outside `drivers/hwmon/` that
registers a hwmon device as an optional feature, in order to assure safe
usage? Start from `drivers/net/phy/Kconfig` and `drivers/acpi/fan.h`.

## hwmon.tracing-tests: Tracing and tests

- section: Finding your way
- relevance: 2 - says what exercises a change to the core

Which trace events does the core emit, from which functions, and from which
number does the index they record count? Does this tree hold any test that
exercises the core? Start from `include/trace/events/hwmon.h`.

# Objects and names

## hwmon.overview: Main objects

- section: Structures and naming
- relevance: 5 - nothing else makes sense without it

What is the hwmon subsystem for, which structures does a driver fill in, and
which structure does the core keep for each registered device? How do these
structures refer to each other? Start from `struct hwmon_chip_info` and
`struct hwmon_device`.

## hwmon.class-device: Class device and parent

- section: Structures and naming
- relevance: 4 - callbacks and attributes hang off this device, not off the driver's device

What device does a registration create, how is it named and numbered, and what
is its relation to the device that the driver passed in? Where does the number
come from, and when is it given back? Start from `__hwmon_device_register()`
and `hwmon_device_unregister()`.

## hwmon.sensor-types: Sensor types

- section: Structures and naming
- relevance: 4 - the set of types has grown and two types share tables

Which sensor types does `enum hwmon_sensor_types` define in this tree, and
which of them share an attribute enumeration or a table of names with another
type? Start from `__templates` in `drivers/hwmon/hwmon.c`.

## hwmon.config-macros: Attribute bit macros

- section: Structures and naming
- relevance: 4 - a macro of the wrong type compiles and describes a different attribute

How do the bit macros used in a channel description relate to the attribute
enumerations, and which prefix goes with which sensor type? Does the compiler
detect a macro of one sensor type that is used in the description of another?
Start from `HWMON_T_INPUT` and `HWMON_C_REGISTER_TZ`.

## hwmon.attr-names: Generated attribute names

- section: Structures and naming
- relevance: 4 - the channel number in a callback is not the number in the file name

How does the core build the sysfs name of an attribute from the sensor type,
the attribute and the channel number? From which number does each sensor type
count its channels, and how long may a name be? Start from `hwmon_genattr()`
and `hwmon_attr_base()`.

## hwmon.chip-flags: Chip bits without a file

- section: Structures and naming
- relevance: 3 - these bits switch on core features and create no attribute of their name

Which bits of the `hwmon_chip` channel description produce no sysfs attribute
of their own on the hwmon device, and what does the core do when it sees each?
Start from `hwmon_chip_attrs` and `__hwmon_device_register()`.

# Registration

## hwmon.register-variants: Registration functions

- section: Registering a device
- relevance: 5 - the first thing checked in a new driver

Which functions register a hwmon device in this tree, and which of them does
the tree mark as deprecated or restricted? What does each deprecated function
do differently from `hwmon_device_register_with_info()`? Start from
`include/linux/hwmon.h`.

## hwmon.register-args: Argument checks

- section: Registering a device
- relevance: 4 - the managed and the plain function treat a missing name differently

Which arguments may be NULL for `hwmon_device_register_with_info()` and for
`devm_hwmon_device_register_with_info()`, and what does each function do with
a NULL name? What do the two functions return on failure?

## hwmon.name-rules: Device name rules

- section: Registering a device
- relevance: 4 - the documentation and the code may not agree on what happens

What are the requirements for the name passed to a registration function in
order to assure safe usage? Which characters does the core test for, and what
does the core do when the name fails the test? Start from
`hwmon_is_bad_char()` and `__hwmon_device_register()`.

## hwmon.name-lifetime: Name string lifetime

- section: Registering a device
- relevance: 4 - a name built on the stack or freed early is read later by sysfs

Does the core copy the name string it is given? What are the requirements for
the lifetime of that string, and of a string returned by
`hwmon_sanitize_name()` or `devm_hwmon_sanitize_name()`, in order to assure
safe usage?

## hwmon.chip-info-lifetime: Chip description lifetime

- section: Registering a device
- relevance: 4 - drivers that build the description at run time must keep it alive

Does the core copy the `struct hwmon_chip_info`, the channel descriptions and
the operations that it is given at registration? What are the requirements for
their lifetime when a driver builds them at run time, in order to assure safe
usage? Start from `lm90_probe()`.

## hwmon.probe-order: State before registration

- section: Registering a device
- relevance: 5 - a recurring race that a diff of probe does not show

What are the requirements for the state of the chip and of the driver's
private data at the time a driver calls a registration function, in order to
assure safe usage? Which driver callbacks can run before the registration
function has returned? Start from `__hwmon_device_register()`.

## hwmon.unregister-order: Removal order

- section: Registering a device
- relevance: 5 - decides whether a callback can run on freed data

What are the requirements for the order of removal in order to assure safe
usage, for a device registered with `hwmon_device_register_with_info()` and
for one registered with `devm_hwmon_device_register_with_info()`? When may a
driver free or power down what its callbacks use? Start from
`devm_hwmon_release()` and `hwmon_dev_release()`.

## hwmon.callback-device: Device passed to callbacks

- section: Registering a device
- relevance: 5 - using the wrong device for driver data is a common mistake

Which device do the `read`, `write` and `read_string` callbacks receive, and
what does `is_visible` receive in its place? How does a callback reach the
private data of the driver and the parent device?

## hwmon.extra-groups: Extra attribute groups

- section: Registering a device
- relevance: 4 - these attributes are outside what the core serializes or generates

On which device does the core create the attributes of `extra_groups`, and
which device do their show and store functions receive? Does the core take its
lock around them? Start from `__hwmon_device_register()` and
`drivers/hwmon/sht4x.c`.

## hwmon.device-label: Device label property

- section: Registering a device
- relevance: 3 - the core creates this attribute with no code in the driver

Where does the `label` attribute of a hwmon device come from, and when is it
visible? How does it differ from a channel label such as `hwmon_temp_label`?
Start from `hwmon_dev_attr_is_visible()`.

## hwmon.firmware-node: Firmware node of the device

- section: Registering a device
- relevance: 3 - thermal zone registration depends on it

Which firmware node does a hwmon device get when the device of the driver has
none, and which later steps of registration depend on that node? Start from
`__hwmon_device_register()`.

## hwmon.thermal-legacy: Registration from thermal

- section: Registering a device
- relevance: 2 - one caller, but a patch may try to add another

What is `hwmon_device_register_for_thermal()` for, and what restricts who may
call it? How does `drivers/thermal/thermal_hwmon.c` create its attributes?

# Channel description

## hwmon.channel-arrays: Channel arrays

- section: Describing channels
- relevance: 5 - a wrong terminator hides channels with no warning

What are the requirements for the `config` array of a
`struct hwmon_channel_info` and for the `info` array of a
`struct hwmon_chip_info` in order to assure safe usage? How does the core find
the end of each array, and what does that mean for a channel that has no
attributes? Start from `hwmon_num_channel_attrs()` and `HWMON_CHANNEL_INFO`.

## hwmon.chip-entry-position: Position of the chip entry

- section: Describing channels
- relevance: 4 - decides whether thermal zones are registered at all

Does the position of the `hwmon_chip` entry in the `info` array matter to the
core, and for which features? Start from `__hwmon_device_register()` and
`hwmon_thermal_register_sensors()`.

## hwmon.visibility: Attribute visibility

- section: Describing channels
- relevance: 4 - tells whether a driver can hide or show an attribute later

When does the core ask a driver whether an attribute is visible, and can the
answer change after registration? What is the `visible` member of
`struct hwmon_ops` for, and which does the core use when both `visible` and
`is_visible` are set? Start from `hwmon_is_visible()`.

## hwmon.missing-callbacks: Missing callbacks

- section: Describing channels
- relevance: 4 - the result is a failed probe, not a missing file

What does registration do when an attribute is visible as readable or as
writable and the driver supplies no callback for it? What does registration do
when the description holds no attribute at all? Start from `hwmon_genattr()`
and `__hwmon_create_attrs()`.

## hwmon.unknown-bits: Bits without a name

- section: Describing channels
- relevance: 3 - tells whether a stray bit fails registration

What does the core do with a bit in a channel description that has no entry in
the table of names for its sensor type? Start from `hwmon_genattrs()`.

# Callbacks

## hwmon.read-contract: Read callback contract

- section: Driver callbacks
- relevance: 4 - every driver implements it

What does the core do with the value and with the return code of the `read`
callback, and in what format does the value reach userspace? Start from
`hwmon_attr_show()`.

## hwmon.energy64: 64-bit energy values

- section: Driver callbacks
- relevance: 4 - the callback type hides the real width of the value

How does a driver return a value for the `hwmon_energy64` sensor type through
a callback whose argument is a pointer to long? What are the requirements for
the code of the driver in order to assure safe usage on a 32-bit build? Start
from `hwmon_attr_show()` and `drivers/hwmon/ina238.c`.

## hwmon.read-string: String attributes

- section: Driver callbacks
- relevance: 3 - the core keeps no copy of the string

Which attributes does the core treat as strings, and which callback serves
them? What are the requirements for the lifetime of the string that the
callback returns, in order to assure safe usage? Start from `is_string_attr()`
and `hwmon_attr_show_string()`.

## hwmon.write-parsing: Parsing written values

- section: Driver callbacks
- relevance: 4 - the sysfs document and the core may describe different parsing

How does the core turn the text written to a generated attribute into the
value it passes to the `write` callback? What does a write return for text
that is not a number, and for a number that does not fit? Start from
`hwmon_attr_store()`.

## hwmon.write-range: Range of written values

- section: Driver callbacks
- relevance: 5 - overflow in a write path is a recurring bug class

What are the requirements for how a `write` callback handles the value it
receives, in order to assure safe usage? Which values can arrive, and in what
order must a driver limit and convert a value before it writes a register?
Start from `clamp_val()` and the last section of
`Documentation/hwmon/sysfs-interface.rst`.

## hwmon.invalid-values: Invalid written values

- section: Driver callbacks
- relevance: 4 - the rule differs by kind of attribute

When a written value is outside what the chip supports, in which cases does a
driver limit the value to the nearest supported one, and in which cases does
it return an error? Where does the tree state the rule?

## hwmon.conversion-arithmetic: Conversion arithmetic

- section: Driver callbacks
- relevance: 4 - scaling to milli and micro units can overflow a long on 32-bit builds

What are the requirements for the arithmetic that converts between register
values and the units of the sysfs interface, in order to assure safe usage?
Which kernel helpers do drivers use for scaling, rounding and packing a value
into a register field? Start from `drivers/hwmon/lm75.h` and
`DIV_ROUND_CLOSEST()`.

## hwmon.error-codes: Callback error codes

- section: Driver callbacks
- relevance: 3 - one code is ignored by the core in some callers

Which error codes does the core treat specially when a callback returns them,
and in which callers? Which code do drivers return from the default branch of
a callback, for an attribute they do not handle? Start from
`hwmon_thermal_set_trips()` and `pec_store()`.

## hwmon.callback-context: Callback calling context

- section: Driver callbacks
- relevance: 4 - the thermal core is a second caller that drivers forget

From which paths does the core call `read` and `write`, apart from a sysfs
access? May the callbacks sleep? Start from `hwmon_thermal_get_temp()`.

# Locking

## hwmon.core-lock: Lock held by the core

- section: Serializing access
- relevance: 5 - decides whether a driver needs a lock of its own

Which lock does the core hold when it calls a driver callback? For which
callbacks and which callers does the core hold the lock, and for which does it
not? Start from `hwmon_attr_show()` and `struct hwmon_device`.

## hwmon.lock-helpers: Driver use of the core lock

- section: Serializing access
- relevance: 5 - the helpers take the hwmon device, not the parent

What do `hwmon_lock()` and `hwmon_unlock()` lock, which device pointer do they
take, and for which code does a driver need them? Do they work for a device
registered with `hwmon_device_register_with_groups()`?

## hwmon.lock-nesting: Taking the lock again

- section: Serializing access
- relevance: 5 - a deadlock that only shows at run time

What are the requirements for calling `hwmon_lock()` or the `hwmon_lock` guard
in order to assure safe usage? From which driver functions is the lock already
held, and from which point in probe is the lock usable?

## hwmon.interrupt-paths: Interrupt handlers and work items

- section: Serializing access
- relevance: 5 - the core serializes nothing on these paths

What are the requirements for an interrupt handler or a work item that touches
the state the callbacks use, in order to assure safe usage? When may such code
start, relative to registration, and when must it have stopped? Start from
`lm90_irq_thread()` and `lm75_alarm_handler()`.

## hwmon.driver-mutex: Drivers with their own mutex

- section: Serializing access
- relevance: 4 - a patch that removes a driver mutex is right for some drivers only

Which drivers still need a mutex of their own around register access and
cached values, and what decides that? Start from `update_lock` in
`drivers/hwmon/pmbus/pmbus_core.c` and from a driver that calls
`devm_hwmon_device_register_with_groups()`.

## hwmon.cached-readings: Cached readings

- section: Serializing access
- relevance: 3 - many older drivers cache, and the pattern has several parts

What are the requirements for a driver that caches register values between
reads, in order to assure safe usage? How does such a driver decide that a
cached value is stale, and what must a failed chip access leave in the cache?
Start from `lm90_update_device()`.

# Events and thermal zones

## hwmon.notify-event: Event notification

- section: Notification and thermal
- relevance: 4 - the function has three effects and a reviewer tends to know one

What does `hwmon_notify_event()` do for userspace and for the thermal
subsystem, what does it check about its arguments, and what does it return?

## hwmon.notify-context: Context for notification

- section: Notification and thermal
- relevance: 5 - a wrong calling context sleeps in an interrupt or deadlocks

What are the requirements for the context that calls `hwmon_notify_event()` in
order to assure safe usage? May a driver call it from hard interrupt context,
and may a driver call it while it holds the lock of the hwmon core? Start from
`hwmon_thermal_notify()` and `lm90_report_alarms()`.

## hwmon.thermal-conditions: Conditions for thermal zones

- section: Notification and thermal
- relevance: 4 - setting the bit is one of several conditions

Under which conditions does the core register thermal zone sensors for a hwmon
device? Name what the driver must set, what the firmware must provide and
which build option must be enabled. Start from
`hwmon_thermal_register_sensors()`.

## hwmon.thermal-channel-index: Thermal sensor index

- section: Notification and thermal
- relevance: 4 - a device tree that counts from the file name names the wrong sensor

For which channels does the core register a thermal zone sensor, and how does
the channel number relate to the sensor index that the device tree gives? What
does the core do for a channel that no thermal zone refers to? Start from
`hwmon_thermal_add_sensor()`.

## hwmon.thermal-ops: Thermal zone operations

- section: Notification and thermal
- relevance: 4 - the thermal core writes limits through the driver's write callback

Which thermal zone operations does the core implement, and which driver
callback and attribute does each call? What does each operation do when the
driver has no `write` callback, or when the callback returns an error? Start
from `hwmon_thermal_ops`.

## hwmon.thermal-failure: Thermal registration failure

- section: Notification and thermal
- relevance: 3 - a thermal error can fail the probe of a sensor driver

What does registration of the hwmon device do when it fails to register a
thermal zone sensor or the PEC attribute, and what does it undo? Start from
`__hwmon_device_register()`.

## hwmon.pec-attribute: PEC attribute

- section: Notification and thermal
- relevance: 3 - the core creates the attribute on a device other than the hwmon device

On which device does the core create the `pec` attribute, and under which
conditions? What does a write to it do before it changes the flags of the I2C
client? What does registration return when `HWMON_C_PEC` is set and the parent
is not an I2C client? Start from `hwmon_pec_register()` and `pec_store()`.

# Userspace interface

## hwmon.abi-units: Units of values

- section: Sysfs interface
- relevance: 4 - a wrong scale factor is the most common driver bug that userspace sees

In which unit does each sensor type report its values through sysfs, and where
does the tree define the units? Start from
`Documentation/ABI/testing/sysfs-class-hwmon`.

## hwmon.abi-alarms: Alarm and fault attributes

- section: Sysfs interface
- relevance: 3 - the document says where the comparison with a limit happens

What does the sysfs interface require of an alarm attribute and of a fault
attribute? Where does the comparison of a reading with its limit happen, and
what does a read return when a sensor is absent or its reading is not valid?
Start from `Documentation/hwmon/sysfs-interface.rst`.

## hwmon.abi-permissions: Attribute permissions

- section: Sysfs interface
- relevance: 3 - a mode returned from is_visible is user-visible policy

Which file modes does the tree prescribe for standard attributes, and where
does the tree state them? Start from
`Documentation/hwmon/sysfs-interface.rst`.

## hwmon.nonstandard-attributes: Non-standard attributes

- section: Sysfs interface
- relevance: 4 - a new attribute name is ABI for ever

What does the tree say about attributes that are not in the standard
interface, and about deprecated attributes? Where may a driver expose
chip-specific values, and what must accompany a new attribute name? Start from
`Documentation/hwmon/submitting-patches.rst`.

## hwmon.doc-versus-code: Documentation and the code

- section: Sysfs interface
- relevance: 4 - a reviewer who quotes the document can be wrong about the code

Where does `Documentation/hwmon/hwmon-kernel-api.rst` describe the structures,
the callbacks or the handling of names differently from
`include/linux/hwmon.h` and `drivers/hwmon/hwmon.c`?

# Legacy interfaces

## hwmon.sensor-attr-macros: Sensor attribute macros

- section: Older driver interfaces
- relevance: 3 - about a third of the files in the directory still use them

What do the macros in `include/linux/hwmon-sysfs.h` define, and how does a
show or store function get the index back? For which attributes does new code
still use them? Start from `SENSOR_DEVICE_ATTR_RW` and `to_sensor_dev_attr()`.

## hwmon.legacy-register: Oldest registration function

- section: Older driver interfaces
- relevance: 2 - only matters for a patch to a driver that still uses it

What does `hwmon_device_register()` create, and what does it log? Where do the
drivers that use it put their attributes and the `name` attribute?

## hwmon.i2c-detection: I2C chip detection

- section: Older driver interfaces
- relevance: 3 - a detect function that writes can misconfigure another chip

What are the requirements for an I2C hwmon driver that detects its chip
without a firmware description, in order to assure safe usage? Which addresses
may it probe, and what may its detect function write and print? Start from
`Documentation/hwmon/submitting-patches.rst` and `I2C_CLASS_HWMON`.

# PMBus

## hwmon.pmbus-files: PMBus files

- section: PMBus core
- relevance: 3 - a large share of new drivers are PMBus chip drivers

Which files hold the PMBus core and its documentation, and how does a chip
driver hand its description to the core? Start from `pmbus_do_probe()` and
`struct pmbus_driver_info`.

## hwmon.pmbus-registration: PMBus registration path

- section: PMBus core
- relevance: 3 - the PMBus core does not use the interface that new drivers must use

Which hwmon registration function does the PMBus core call, and how does it
create its attributes? Which symbol namespace must a PMBus chip driver import?
Start from `drivers/hwmon/pmbus/pmbus_core.c`.

## hwmon.pmbus-locking: PMBus locking

- section: PMBus core
- relevance: 4 - two locks exist and only one protects PMBus access

Which lock serializes chip access in the PMBus core, and how does a chip
driver take it? Does the lock of the hwmon core play any part? Start from
`pmbus_lock()`.

# Changing the core

## hwmon.new-attribute: Adding an attribute

- section: What a change must preserve
- relevance: 4 - the enumeration and the name table are kept in step by hand

When a patch adds an attribute or a sensor type to the core, which definitions
and tables must change together, and which documents? What happens at
registration when the enumeration and the table of names disagree? Start from
`enum hwmon_temp_attributes` and `hwmon_temp_attr_templates`.

## hwmon.register-unwind: Unwinding a failed registration

- section: What a change must preserve
- relevance: 4 - the error paths free through two different routes

In `__hwmon_device_register()`, which function frees the hwmon device and its
attributes on each failure path, and what changes once the function has called
`device_register()`? Start from `hwmon_dev_release()`.

## hwmon.unregister-id: Finding the id at removal

- section: What a change must preserve
- relevance: 3 - the id is not stored in the device structure

How does `hwmon_device_unregister()` find the number to give back, and what
does it do when it cannot find the number? What does that require of the
device pointer that a caller passes?

## hwmon.attribute-memory: Attribute memory

- section: What a change must preserve
- relevance: 3 - the core frees its own attributes and must leave the driver's alone

Who allocates and who frees the attributes that the core generates and the
array of groups? How does the core tell its own attributes from those of the
driver when it frees them? Start from `hwmon_free_attrs()`.
