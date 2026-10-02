# Questions: LED Subsystem

- guide: leds.md
- title: LED Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/leds-measurement.md` is the wider
set the readers were measured on and `catalogue/leds-measurement-results.md` says what they got
wrong. The part "Conventions" is not built from a question: the build inserts
`../verbatim/leds-conventions.md`, which is kept by hand. No number says how long an answer or the
guide should be. Format: `../../docs/subsystem-questions.md`.

# Main structures

## leds.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## leds.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Which files hold the LED class, the brightness and blink core, the trigger
core, the multicolor class, the flash class and the headers that drivers
include, and what does `drivers/leds/leds.h` hold that `include/linux/leds.h`
does not? Start from `drivers/leds/Makefile`.

## leds.outside-code: LED code elsewhere

- section: Finding your way
- relevance: 3 - many LEDs and triggers are registered by other subsystems

Where in the tree, outside `drivers/leds/`, does code register LED class
devices and LED triggers, and which files carry the LED support of the network
PHY layer, of the V4L2 flash wrapper and of the sound core? Start from
`drivers/net/phy/phy_device.c`, `drivers/media/v4l2-core/v4l2-flash-led-class.c`
and `sound/core/control_led.c`.

## leds.driver-directories: Driver directories

- section: Finding your way
- relevance: 2 - says where a new driver belongs

How are the LED drivers under `drivers/leds/` divided into subdirectories, and
which kind of driver goes in each? Start from `drivers/leds/Kconfig`.

## leds.docs: Documentation

- section: Finding your way
- relevance: 3 - some contracts are written only there, and some text is out of date

Which files under `Documentation/leds/` and `Documentation/ABI/testing/` are
the authority on the LED class, on the multicolor and flash classes and on the
sysfs files of each trigger? Does the class documentation name any function
that this tree does not define? Start from `Documentation/leds/leds-class.rst`.

## leds.tests: Tests and tools

- section: Finding your way
- relevance: 2 - a core change is expected to keep the test passing

What tests and user-space tools does the tree carry for the LED core, how is
each built and run, and what do the tests cover? Start from
`drivers/leds/led-test.c` and `tools/leds/`.

# Kconfig and header stubs

## leds.kconfig: Configuration symbols

- section: Kconfig and header stubs
- relevance: 4 - a wrong dependency is a link failure in some configurations

Which configuration symbols gate the LED class, the trigger core, the
multicolor class and the flash class, and which of them can be built as a
module? What does a driver outside `drivers/leds/` that registers an LED need
in its own Kconfig entry so that it links in every configuration? Start from
`drivers/leds/Kconfig` and `drivers/leds/trigger/Kconfig`.

## leds.header-stubs: Stubs when configured out

- section: Kconfig and header stubs
- relevance: 3 - decides whether a caller needs its own guard

When the LED class or the trigger core is configured out, which groups of
functions declared in `include/linux/leds.h` have empty inline versions and
which have none? What does that require of a caller that can be built without
`CONFIG_LEDS_CLASS` or `CONFIG_LEDS_TRIGGERS`?

# Class device state

## leds.classdev-flags: Flags word

- section: Class device state
- relevance: 4 - a driver that sets the wrong half changes core state

How is the `flags` member of `struct led_classdev` divided between state that
the core keeps and settings that a driver chooses, and what does each
driver-chosen flag change in the core? Is any lock held when the core changes
`flags`? Start from `LED_CORE_SUSPENDRESUME` in `include/linux/leds.h`.

## leds.work-flags: Work flags

- section: Class device state
- relevance: 3 - private to the core, yet some triggers touch it

What is the `work_flags` member of `struct led_classdev` for, how is it
accessed compared with `flags`, and who may set and clear its bits? Start from
`LED_BLINK_SW`.

## leds.brightness-field: Cached brightness value

- section: Class device state
- relevance: 3 - drivers and triggers read it without a lock

What does the `brightness` member of `struct led_classdev` hold, who writes it,
and is any lock held when the core writes it? Can it differ from what the
hardware shows?

## leds.max-brightness: Maximum brightness

- section: Class device state
- relevance: 4 - the driver's value is not always the final one

How is the `max_brightness` of an LED decided: what does the core do when the
driver leaves it zero, which inputs other than the driver can change it during
registration, and where does the core limit a requested brightness to it?

## leds.brightness-type: Brightness type and constants

- section: Class device state
- relevance: 3 - new code is reviewed against the current convention

Which type do the brightness functions and callbacks take in this tree, and
what is the status of `enum led_brightness` and of constants such as
`LED_FULL`? Start from `drivers/leds/TODO`.

# Sysfs interface

## leds.sysfs-attributes: Class sysfs attributes

- section: Sysfs interface
- relevance: 4 - the user-space contract of every LED

Which sysfs attributes does the LED class create for every LED, which lock
does each handler take, and what does a write to `brightness` do to the trigger
of the LED and to a blink in progress? Start from `brightness_store()`.

## leds.hw-changed: Hardware brightness changes

- section: Sysfs interface
- relevance: 3 - the call warns when its precondition is missing

What are the requirements for calling
`led_classdev_notify_brightness_hw_changed()` in order to assure safe usage:
what must the driver have set before registration, and which configuration
symbol must be on? What does the attribute return before the first
notification?

## leds.driver-attributes: Driver sysfs attributes

- section: Sysfs interface
- relevance: 4 - attributes added by hand race with user space

What are the requirements for a driver that adds its own sysfs attributes to an
LED class device in order to assure safe usage, and how does the handler of
such an attribute reach the driver's data? Start from the `groups` member of
`struct led_classdev`.

# Registering an LED

## leds.register-steps: Registration steps

- section: Registering an LED
- relevance: 5 - the LED is live before the call returns

What does `led_classdev_register_ext()` do, in order, and at which point can
sysfs handlers, a trigger and the driver's callbacks first run against the
LED? Which lock does it hold while it does so?

## leds.register-firmware-props: Properties the core reads

- section: Registering an LED
- relevance: 4 - drivers parse again what the core already parsed, or skip what it did not

Which firmware properties does the core read by itself when
`struct led_init_data` carries a firmware node, and which common LED properties
are left for the driver to parse? Start from `led_classdev_register_ext()` and
`led_init_default_state_get()`.

## leds.compose-name: Name composition

- section: Registering an LED
- relevance: 4 - the precedence decides the name that user space sees

How does `led_compose_name()` build the name of an LED from the `label`,
`color`, `function` and `function-enumerator` properties and from
`struct led_init_data`, which source is used when several are present, and
when does it fail?

## leds.name-fields: Name after registration

- section: Registering an LED
- relevance: 4 - code that prints or matches the wrong field uses a stale name

After registration, which field or call gives the name that the LED has in
sysfs, and when can that name differ from the `name` member of
`struct led_classdev`? Start from `led_classdev_next_name()`.

## leds.naming-rules: Naming rules

- section: Registering an LED
- relevance: 4 - user space finds LEDs by name

Which form does the class documentation give for the name of an LED, what
should the device name part refer to, and which rules does it give for keyboard
backlights? Start from `Documentation/leds/leds-class.rst`.

## leds.driver-shape: Shape of a small driver

- section: Registering an LED
- relevance: 3 - the pattern that new drivers are compared with

What does a small in-tree LED driver do in probe, from walking the child
firmware nodes to registering each LED, and which helpers does it use for the
iteration and for the initial state? Start from `drivers/leds/leds-gpio.c` and
`drivers/leds/leds-pwm.c`.

## leds.probe-order: Readiness before registration

- section: Registering an LED
- relevance: 5 - a callback that runs during registration finds the driver half set up

What are the requirements for what a driver's probe has finished before it
registers an LED in order to assure safe usage, given what the core may call
during registration? Start from `led_update_brightness()` and
`led_trigger_set_default()`.

## leds.child-node-refs: Child node references

- section: Registering an LED
- relevance: 3 - reference counting of child nodes is a frequent subject of fixes

What are the requirements for holding and dropping references to child
firmware nodes while a driver registers one LED for each child in order to
assure safe usage? Does the core take its own reference on the node that
`struct led_init_data` carries? Start from `device_set_node()` in
`led_classdev_register_ext()`.

# Removing an LED

## leds.unregister-steps: Unregistration steps

- section: Removing an LED
- relevance: 5 - the driver is called back while the LED goes away

What does `led_classdev_unregister()` do, in order, and which driver callbacks
can it call while it runs? What does it do when the LED was never registered,
or when registration failed?

## leds.devm-unregister: Managed unregister

- section: Removing an LED
- relevance: 2 - rarely needed, and it warns when misused

When does a driver need `devm_led_classdev_unregister()`, which device must be
passed to it, and what does it do if the LED was not registered with the
managed call? Start from `drivers/leds/uleds.c`.

## leds.hot-unplug-errors: Errors after unplug

- section: Removing an LED
- relevance: 2 - concerns only drivers for removable devices

How does the core treat an error from a brightness callback while the LED is
being unregistered, and which flag and which error code does a driver for a
removable device use for that? Start from
`set_brightness_delayed_set_brightness()`.

## leds.remove-ordering: Removal ordering

- section: Removing an LED
- relevance: 5 - the wrong order is a use after free that no test shows

What are the requirements for the order in which a driver releases its
resources and unregisters its LEDs in order to assure safe usage, both when
registration is managed and when it is not? Which driver resources must still
work while the LED is being unregistered? Start from
`devm_led_classdev_release()`.

# Setting brightness

## leds.set-brightness-variants: Brightness setting functions

- section: Setting brightness
- relevance: 5 - choosing the wrong one sleeps in atomic context or loses a change

Which functions set the brightness of an LED from kernel code, which of them
may sleep, and which are private to the LED core and its triggers? Start from
`led_set_brightness()`, `led_set_brightness_sync()` and
`led_set_brightness_nosleep()`.

## leds.brightness-work: Deferred brightness work

- section: Setting brightness
- relevance: 4 - ordering of two quick changes depends on it

How does the core deliver a brightness change to a driver whose callback may
sleep: which work item does it use, what is guaranteed when two changes are
requested before the work runs, and what happens to an error that the callback
returns? Start from `set_brightness_delayed()`.

## leds.set-brightness-sync: Synchronous brightness setting

- section: Setting brightness
- relevance: 3 - its error returns differ from what the name suggests

What does `led_set_brightness_sync()` return when the LED is blinking, when
the driver has no blocking callback, and when the LED is suspended?

## leds.brightness-get: Brightness get callback

- section: Setting brightness
- relevance: 3 - it is called earlier than drivers expect

When does the core call a driver's `brightness_get` callback, what may the
callback return, and which lock is held around the call? Start from
`led_update_brightness()`.

## leds.brightness-callbacks: Brightness set callbacks

- section: Setting brightness
- relevance: 5 - sleeping in the wrong callback is the most common driver bug

What are the requirements for a driver's `brightness_set` and
`brightness_set_blocking` callbacks in order to assure safe usage: in which
contexts does the core call each, and what does the core do when a driver sets
both or neither? Start from `led_set_brightness_nopm()`.

# Blinking

## leds.blink-variants: Blink functions

- section: Blinking
- relevance: 4 - one of them may sleep and the others are called from atomic context

Which functions start blinking on an LED, which of them may sleep, and what do
zero delays mean to each? Start from `led_blink_set()`,
`led_blink_set_nosleep()` and `led_blink_set_oneshot()`.

## leds.set-brightness-blinking: Brightness while blinking

- section: Blinking
- relevance: 4 - the value does not always reach the hardware at once

What does `led_set_brightness()` do when software blinking is active, for a
zero value and for a non-zero value, and when does the change reach the
hardware?

## leds.oneshot-blink: One-shot blink

- section: Blinking
- relevance: 3 - activity triggers call it at a high rate

What does `led_blink_set_oneshot()` do when a one-shot blink is already
running, what does its `invert` argument change, and does a one-shot blink
ever use the driver's `blink_set`?

## leds.blink-set-callback: Hardware blink callback

- section: Blinking
- relevance: 4 - the rule on sleeping depends on another callback

What are the requirements for a driver's `blink_set` callback in order to
assure safe usage: when may it sleep, what must it do with the delay values it
is given, and how is hardware blinking turned off again?

## leds.blink-stop: Stopping a blink

- section: Blinking
- relevance: 4 - a timer left running touches a freed LED

What are the requirements for stopping software and hardware blinking in order
to assure safe usage: which calls stop each, from which context may they be
made, and what does a direct call to the driver's `brightness_set` do to a
blink in progress? Start from `led_stop_software_blink()`.

## leds.own-timer-triggers: Triggers with their own timer

- section: Blinking
- relevance: 3 - they reach into state that is private to the core

What are the requirements for a trigger that drives an LED from its own timer
in order to assure safe usage together with `led_set_brightness()`: which bits
of `work_flags` must it set, test and clear, and when? Start from
`drivers/leds/trigger/ledtrig-heartbeat.c`.

# Trigger core

## leds.trigger-set: Attaching a trigger

- section: Trigger core
- relevance: 5 - the order of its steps is what a change must preserve

What does `led_trigger_set()` do, in order, when it replaces one trigger with
another, which lock must the caller hold, and in what state is the LED left
when the `activate` callback of the new trigger fails?

## leds.trigger-locks: Trigger locks and their order

- section: Trigger core
- relevance: 5 - a new path that nests them the other way deadlocks

Which locks protect the list of triggers, the list of LEDs and the trigger of
one LED, in what order do they nest with each other and with `led_access`, and
which list is walked under RCU? Start from `triggers_list_lock`,
`leds_list_lock` and `trigger_lock`.

## leds.trigger-file: Trigger file

- section: Trigger core
- relevance: 3 - it is a binary attribute for a reason the code states

How is the `trigger` file of an LED implemented, what do the words none and
default do when written to it, and which triggers does a read list for a given
LED? Start from `led_trigger_read()` and `led_trigger_write()`.

## leds.default-trigger: Default trigger

- section: Trigger core
- relevance: 4 - the trigger may be registered after the LED

How does an LED get its default trigger: who sets `default_trigger`, what
happens when the named trigger is not registered yet, and how is a trigger
module loaded on demand? Start from `led_trigger_set_default()`.

## leds.private-trigger: Private triggers

- section: Trigger core
- relevance: 4 - decides which LEDs may select a trigger

What is `struct led_hw_trigger_type` for, how do the `trigger_type` members of
an LED and of a trigger decide which triggers an LED may use, and what does the
class return for a read of `brightness` while such a trigger is active? Start
from `trigger_relevant()`.

## leds.simple-trigger: Simple triggers

- section: Trigger core
- relevance: 4 - failure is reported through the pointer, not a return value

What do `led_trigger_register_simple()` and `led_trigger_unregister_simple()`
allocate and free, how does a caller learn that registration failed, and what
do `led_trigger_event()` and `led_trigger_blink_oneshot()` do when they are
given a NULL trigger?

## leds.trigger-event-context: Trigger event context

- section: Trigger core
- relevance: 5 - events arrive from interrupt handlers

From which contexts may `led_trigger_event()`, `led_trigger_blink()` and
`led_trigger_blink_oneshot()` be called, how do they walk the LEDs of a
trigger, and what does that require of the functions they call for each LED?

## leds.trigger-unregister: Trigger unregistration

- section: Trigger core
- relevance: 4 - the precondition is not checked in every case

What are the requirements for calling `led_trigger_unregister()` in order to
assure safe usage: what does it do to LEDs that use the trigger, what state
must the trigger structure be in before the call, and what may the caller free
afterwards?

# Writing a trigger

## leds.trigger-data: Trigger data for each LED

- section: Writing a trigger
- relevance: 4 - a handler that runs at the wrong moment reads a stale pointer

How does a trigger keep data for each LED it is attached to, which accessors
read that data in a sysfs handler, and at which points of attaching and
detaching is the data valid? Start from `led_set_trigger_data()` and
`led_trigger_get_drvdata()`.

## leds.default-pattern-init: Default pattern at activation

- section: Writing a trigger
- relevance: 2 - used by a few triggers and one driver

What is `LED_INIT_DEFAULT_TRIGGER` for, who sets it and who clears it, and who
frees the array that `led_get_default_pattern()` returns?

## leds.panic-trigger: Panic indicator

- section: Writing a trigger
- relevance: 3 - it bypasses every lock of the trigger core

How does the panic trigger take over LEDs when the kernel panics, which LEDs
does it take, and what does that require of the brightness callback of an LED
that is marked as a panic indicator? Start from
`drivers/leds/trigger/ledtrig-panic.c`.

## leds.activity-hooks: Activity hooks for other subsystems

- section: Writing a trigger
- relevance: 3 - they are called from hot paths

Which functions do other subsystems call to report disk, MTD, CPU and camera
activity to the built-in triggers, what do the calls compile to when the
trigger is configured out, and from which contexts are they called? Start from
`ledtrig_disk_activity()` and `ledtrig_cpu()`.

## leds.trigger-callbacks: Activate and deactivate callbacks

- section: Writing a trigger
- relevance: 5 - what deactivate leaves running is a use after free

What are the requirements for the `activate` and `deactivate` callbacks of a
trigger in order to assure safe usage: which locks are held when they run, may
they sleep, and what must `deactivate` have stopped before it frees the data of
the trigger?

# Hardware control

## leds.hw-control-providers: Hardware control providers

- section: Hardware control
- relevance: 2 - they all live outside the LED directory

Where in the tree are LEDs registered that offer hardware control, and which
layer fills in the callbacks on behalf of a network PHY driver? Start from
`of_phy_led()`.

## leds.hw-control-netdev: Netdev trigger offload

- section: Hardware control
- relevance: 4 - the only trigger that uses hardware control

How does the netdev trigger decide between hardware control and software
blinking, which conditions must all hold for hardware control, and what does a
write return to user space when neither is possible? Start from
`can_hw_control()` in `drivers/leds/trigger/ledtrig-netdev.c`.

## leds.netdev-locking: Netdev trigger locking

- section: Hardware control
- relevance: 3 - it nests networking locks around its own

Which locks does the netdev trigger take, in what order, and which of its
paths run with the RTNL lock already held? Start from `set_device_name()` and
`netdev_trig_notify()`.

## leds.hw-control-callbacks: Hardware control callbacks

- section: Hardware control
- relevance: 4 - the trigger calls one of them without a check

What are the requirements for an LED driver that offers hardware control in
order to assure safe usage: which callbacks and which field must it set
together, what must a callback return when a mode is not supported, and how is
hardware control turned off? Start from `hw_control_trigger` in
`include/linux/leds.h`.

# Patterns

## leds.pattern-trigger: Pattern trigger

- section: Patterns
- relevance: 2 - one file, with three kinds of pattern

Which kinds of pattern does the pattern trigger run, which timer drives each,
and how many entries does a software pattern need? Start from
`drivers/leds/trigger/ledtrig-pattern.c`.

## leds.pattern-callbacks: Pattern callbacks

- section: Patterns
- relevance: 3 - the trigger changes the callbacks when they are inconsistent

What are the requirements for a driver's `pattern_set` and `pattern_clear`
callbacks in order to assure safe usage: what does the pattern trigger do when
only one of them is set, what do the entries of `struct led_pattern` and the
repeat count mean, and when is each callback called?

# Multicolor class

## leds.mc-struct: Multicolor structures

- section: Multicolor class
- relevance: 4 - three similar fields of a sub-LED mean different things

What do `struct led_classdev_mc` and `struct mc_subled` represent, who
allocates the array of sub-LEDs, and what do the `intensity`, `brightness` and
`max_intensity` members of a sub-LED each mean?

## leds.mc-register: Multicolor registration

- section: Multicolor class
- relevance: 4 - it overwrites a field that the driver may have set

What does `led_classdev_multicolor_register_ext()` check and set before it
registers the LED, which members of the embedded `struct led_classdev` does it
overwrite, and how can the driver of a multicolor LED add sysfs attributes of
its own?

## leds.mc-calc: Component calculation

- section: Multicolor class
- relevance: 4 - the core never calls it for the driver

What does `led_mc_calc_color_components()` compute, from which fields, and who
is expected to call it, and when?

## leds.mc-sysfs: Multicolor sysfs files

- section: Multicolor class
- relevance: 3 - a write changes the hardware only in some states

Which sysfs files does the multicolor class add, what does a write to the
intensity file do to the hardware, and how is a written value limited? Start
from `multi_intensity_store()`.

## leds.mc-kernel-set: Multicolor from kernel code

- section: Multicolor class
- relevance: 3 - misuse is logged once and then ignored

How does kernel code set the color of a multicolor LED, and what do
`led_mc_set_brightness()` and `led_mc_trigger_event()` do when the LED is not
multicolor or the number of colors does not match?

# Flash class

## leds.flash-struct: Flash structures

- section: Flash class
- relevance: 3 - units and mandatory operations are easy to guess wrong

Which settings of a flash LED do `struct led_classdev_flash` and
`struct led_flash_ops` carry, which operations must a driver supply, and in
which units is each setting expressed?

## leds.flash-register: Flash registration

- section: Flash class
- relevance: 4 - the checks apply only when a flag is set

What does `led_classdev_flash_register_ext()` require of the LED before it
registers it, what does `LED_DEV_CAP_FLASH` select, and how are the flash sysfs
groups chosen?

## leds.flash-settings: Flash setting helpers

- section: Flash class
- relevance: 3 - the stored value is not always the value passed in

What do `led_set_flash_brightness()` and `led_set_flash_timeout()` do with a
value that is outside the limits or between two steps, what do they do when the
LED is suspended, and what do they return when the driver lacks the operation?
Start from `led_clamp_align()`.

## leds.flash-v4l2: V4L2 flash wrapper

- section: Flash class
- relevance: 3 - it takes the LED away from sysfs while it is open

How does the V4L2 flash wrapper use a flash LED: which functions create and
release it, what does it do to the sysfs interface and to the trigger of the
LED while the sub-device is open, and which brightness function does it call?
Start from `v4l2_flash_init()`.

## leds.flash-strobe: Flash strobe helpers

- section: Flash class
- relevance: 3 - the inline helpers check less than the others

What are the requirements for calling `led_set_flash_strobe()` and
`led_get_flash_strobe()` in order to assure safe usage: what must be true of
the flash LED and of its operations before each call? Which lock do the sysfs
handlers hold around them?

# LED consumers

## leds.consumer-get: Getting an LED

- section: LED consumers
- relevance: 3 - the return value for a missing LED decides probe deferral

Which functions let a driver obtain an LED that another driver registered, how
does each find the LED, and what do they return when the LED is described in
firmware and is not registered yet? Start from `led_get()` and
`devm_of_led_get()`.

## leds.consumer-refs: Consumer references

- section: LED consumers
- relevance: 3 - two references are taken, and both must be dropped

Which references does getting an LED take, which function drops them, and what
keeps the driver that provides the LED from being unloaded while a consumer
holds the LED? Start from `led_put()`.

## leds.consumer-lookup: Lookup table

- section: LED consumers
- relevance: 2 - used on systems without a firmware description

What is `struct led_lookup_data` for, how are its entries matched, and what are
the requirements for the lifetime of an entry passed to `led_add_lookup()` in
order to assure safe usage?

# Suspend and shutdown

## leds.suspend-resume: Suspend and resume

- section: Suspend and shutdown
- relevance: 4 - a change made while suspended is kept, not applied

What do `led_classdev_suspend()` and `led_classdev_resume()` do to the hardware
and to the cached brightness, when does the class call them by itself, and
what happens to a brightness that is set while the LED is suspended?

## leds.shutdown-state: State at shutdown

- section: Suspend and shutdown
- relevance: 3 - the core and the driver each handle part of it

What does `LED_RETAIN_AT_SHUTDOWN` change in the core, which firmware property
sets it, and what is left to the shutdown callback of the driver? Start from
`drivers/leds/leds-gpio.c`.

# Device tree bindings

## leds.dt-common: Common binding

- section: Device tree bindings
- relevance: 4 - every LED binding refers to it

Which file defines the properties common to all LED nodes, does it mark any of
those properties as deprecated, and how does the binding of one LED controller
include the common properties? Start from
`Documentation/devicetree/bindings/leds/common.yaml`.

## leds.dt-constants: Function and color constants

- section: Device tree bindings
- relevance: 3 - a made-up string defeats the naming scheme

Where are constants such as `LED_FUNCTION_STATUS` and `LED_COLOR_ID_RED`
defined, which type does each of the two properties take in a device tree, and
what does the tree say to do when no existing constant fits?

## leds.color-ids: Color identifiers

- section: Device tree bindings
- relevance: 3 - three places have to change together

Where are the LED color identifiers defined, which table turns them into
names, and what must change together when a color is added? Start from
`LED_COLOR_ID_MAX`.

## leds.dt-multicolor: Multicolor binding

- section: Device tree bindings
- relevance: 2 - narrow, but the node name is checked

How is a multicolor LED described in a device tree: which node name and which
`color` values does the binding require, and how are the sub-LEDs described?
Start from `Documentation/devicetree/bindings/leds/leds-class-multicolor.yaml`.

## leds.dt-links: Trigger sources and consumers

- section: Device tree bindings
- relevance: 2 - two bindings that are easy to confuse

Which bindings describe an LED that follows another device and a device that
uses an LED, and which code in the tree reads each? Start from
`Documentation/devicetree/bindings/leds/trigger-source.yaml` and
`Documentation/devicetree/bindings/leds/leds-consumer.yaml`.

# User-space LEDs

## leds.uleds: User-space LED driver

- section: User-space LEDs
- relevance: 2 - one small driver with a user-space interface

How does user space create an LED through the `uleds` driver, what does the
driver check in the name it is given, and how does user space learn of a
brightness change? Start from `drivers/leds/uleds.c`.

# Conventions

## leds.conventions: Conventions for new code

- section: Conventions
- verbatim: ../verbatim/leds-conventions.md

# Model gaps

## leds.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
