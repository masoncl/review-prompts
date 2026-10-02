# Questions: LED Subsystem (measurement set)

- guide: leds.md
- title: LED Subsystem

A wide set of questions about the LED core and what it expects from every
driver that registers an LED: the class device and its callbacks, registration
and removal, setting brightness, blinking, triggers, hardware control,
patterns, the multicolor and flash classes, consumers of an LED, suspend and
shutdown, the device tree bindings and the user-space LED driver. It is used to
measure what a model already knows before deciding what the built guide should
hold. The hand-written guide it will replace is 539 words and was never checked
against current sources. The inside of individual LED controller drivers is
left out. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## leds.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

Which files hold the LED class, the brightness and blink core, the trigger
core, the multicolor class, the flash class and the headers that drivers
include, and what does `drivers/leds/leds.h` hold that `include/linux/leds.h`
does not? Start from `drivers/leds/Makefile`.

## leds.driver-directories: Driver directories

- section: Finding your way
- relevance: 2 - says where a new driver belongs

How are the LED drivers under `drivers/leds/` divided into subdirectories, and
which kind of driver goes in each? Start from `drivers/leds/Kconfig`.

## leds.outside-code: LED code elsewhere

- section: Finding your way
- relevance: 3 - many LEDs and triggers are registered by other subsystems

Where in the tree, outside `drivers/leds/`, does code register LED class
devices and LED triggers, and which files carry the LED support of the network
PHY layer, of the V4L2 flash wrapper and of the sound core? Start from
`drivers/net/phy/phy_device.c`, `drivers/media/v4l2-core/v4l2-flash-led-class.c`
and `sound/core/control_led.c`.

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

## leds.kconfig: Configuration symbols

- section: Finding your way
- relevance: 4 - a wrong dependency is a link failure in some configurations

Which configuration symbols gate the LED class, the trigger core, the
multicolor class and the flash class, and which of them can be built as a
module? What does a driver outside `drivers/leds/` that registers an LED need
in its own Kconfig entry so that it links in every configuration? Start from
`drivers/leds/Kconfig` and `drivers/leds/trigger/Kconfig`.

## leds.header-stubs: Stubs when configured out

- section: Finding your way
- relevance: 3 - decides whether a caller needs its own guard

When the LED class or the trigger core is configured out, which groups of
functions declared in `include/linux/leds.h` have empty inline versions and
which have none? What does that require of a caller that can be built without
`CONFIG_LEDS_CLASS` or `CONFIG_LEDS_TRIGGERS`?

# The class device

## leds.classdev-struct: Class device structure

- section: Class device
- relevance: 5 - every other answer refers to it

What does `struct led_classdev` represent, who allocates it, and which parts
does the driver fill and which parts does the core fill? How does a driver get
from it to its own private data and to the `struct device` that the class
created?

## leds.classdev-flags: Flags word

- section: Class device
- relevance: 4 - a driver that sets the wrong half changes core state

How is the `flags` member of `struct led_classdev` divided between state that
the core keeps and settings that a driver chooses, and what does each
driver-chosen flag change in the core? Is any lock held when the core changes
`flags`? Start from `LED_CORE_SUSPENDRESUME` in `include/linux/leds.h`.

## leds.work-flags: Work flags

- section: Class device
- relevance: 3 - private to the core, yet some triggers touch it

What is the `work_flags` member of `struct led_classdev` for, how is it
accessed compared with `flags`, and who may set and clear its bits? Start from
`LED_BLINK_SW`.

## leds.name-fields: Name after registration

- section: Class device
- relevance: 4 - code that prints or matches the wrong field uses a stale name

After registration, which field or call gives the name that the LED has in
sysfs, and when can that name differ from the `name` member of
`struct led_classdev`? Start from `led_classdev_next_name()`.

## leds.brightness-callbacks: Brightness set callbacks

- section: Class device
- relevance: 5 - sleeping in the wrong callback is the most common driver bug

What are the requirements for a driver's `brightness_set` and
`brightness_set_blocking` callbacks in order to assure safe usage: in which
contexts does the core call each, and what does the core do when a driver sets
both or neither? Start from `led_set_brightness_nopm()`.

## leds.brightness-get: Brightness get callback

- section: Class device
- relevance: 3 - it is called earlier than drivers expect

When does the core call a driver's `brightness_get` callback, what may the
callback return, and which lock is held around the call? Start from
`led_update_brightness()`.

## leds.max-brightness: Maximum brightness

- section: Class device
- relevance: 4 - the driver's value is not always the final one

How is the `max_brightness` of an LED decided: what does the core do when the
driver leaves it zero, which inputs other than the driver can change it during
registration, and where does the core limit a requested brightness to it?

## leds.brightness-type: Brightness type and constants

- section: Class device
- relevance: 3 - new code is reviewed against the current convention

Which type do the brightness functions and callbacks take in this tree, and
what is the status of `enum led_brightness` and of constants such as
`LED_FULL`? Start from `drivers/leds/TODO`.

## leds.sysfs-attributes: Class sysfs attributes

- section: Class device
- relevance: 4 - the user-space contract of every LED

Which sysfs attributes does the LED class create for every LED, which lock
does each handler take, and what does a write to `brightness` do to the trigger
of the LED and to a blink in progress? Start from `brightness_store()`.

## leds.driver-attributes: Driver sysfs attributes

- section: Class device
- relevance: 4 - attributes added by hand race with user space

What are the requirements for a driver that adds its own sysfs attributes to an
LED class device in order to assure safe usage, and how does the handler of
such an attribute reach the driver's data? Start from the `groups` member of
`struct led_classdev`.

## leds.sysfs-disable: Disabling sysfs writes

- section: Class device
- relevance: 3 - only some handlers honour it

What do `led_sysfs_disable()` and `led_sysfs_enable()` do, which lock must the
caller hold, and which attribute handlers honour the disabled state? Start from
`led_sysfs_is_disabled()`.

## leds.hw-changed: Hardware brightness changes

- section: Class device
- relevance: 3 - the call warns when its precondition is missing

What are the requirements for calling
`led_classdev_notify_brightness_hw_changed()` in order to assure safe usage:
what must the driver have set before registration, and which configuration
symbol must be on? What does the attribute return before the first
notification?

# Registration and removal

## leds.register-variants: Registration functions

- section: Registering an LED
- relevance: 4 - several wrappers end in one function

Which functions register an LED class device, a multicolor LED and a flash
LED, which of them are managed, and which one function do the others all call?
When does a driver need the variant that takes a `struct led_init_data`?

## leds.register-steps: Registration steps

- section: Registering an LED
- relevance: 5 - the LED is live before the call returns

What does `led_classdev_register_ext()` do, in order, and at which point can
sysfs handlers, a trigger and the driver's callbacks first run against the
LED? Which lock does it hold while it does so?

## leds.probe-order: Readiness before registration

- section: Registering an LED
- relevance: 5 - a callback that runs during registration finds the driver half set up

What are the requirements for what a driver's probe has finished before it
registers an LED in order to assure safe usage, given what the core may call
during registration? Start from `led_update_brightness()` and
`led_trigger_set_default()`.

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

## leds.name-collision: Name collisions

- section: Registering an LED
- relevance: 3 - the default outcome surprises drivers that match by name

What does registration do when another LED already has the requested name, how
can a driver choose a different outcome, and what does `devname_mandatory` in
`struct led_init_data` require of the caller?

## leds.naming-rules: Naming rules

- section: Registering an LED
- relevance: 4 - user space finds LEDs by name

Which form does the class documentation give for the name of an LED, what
should the device name part refer to, and which rules does it give for keyboard
backlights? Start from `Documentation/leds/leds-class.rst`.

## leds.child-node-refs: Child node references

- section: Registering an LED
- relevance: 3 - reference counting of child nodes is a frequent subject of fixes

What are the requirements for holding and dropping references to child
firmware nodes while a driver registers one LED for each child in order to
assure safe usage? Does the core take its own reference on the node that
`struct led_init_data` carries? Start from `device_set_node()` in
`led_classdev_register_ext()`.

## leds.driver-shape: Shape of a small driver

- section: Registering an LED
- relevance: 3 - the pattern that new drivers are compared with

What does a small in-tree LED driver do in probe, from walking the child
firmware nodes to registering each LED, and which helpers does it use for the
iteration and for the initial state? Start from `drivers/leds/leds-gpio.c` and
`drivers/leds/leds-pwm.c`.

## leds.unregister-steps: Unregistration steps

- section: Removing an LED
- relevance: 5 - the driver is called back while the LED goes away

What does `led_classdev_unregister()` do, in order, and which driver callbacks
can it call while it runs? What does it do when the LED was never registered,
or when registration failed?

## leds.remove-ordering: Removal ordering

- section: Removing an LED
- relevance: 5 - the wrong order is a use after free that no test shows

What are the requirements for the order in which a driver releases its
resources and unregisters its LEDs in order to assure safe usage, both when
registration is managed and when it is not? Which driver resources must still
work while the LED is being unregistered? Start from
`devm_led_classdev_release()`.

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

# Setting brightness

## leds.set-brightness-variants: Brightness setting functions

- section: Brightness
- relevance: 5 - choosing the wrong one sleeps in atomic context or loses a change

Which functions set the brightness of an LED from kernel code, which of them
may sleep, and which are private to the LED core and its triggers? Start from
`led_set_brightness()`, `led_set_brightness_sync()` and
`led_set_brightness_nosleep()`.

## leds.set-brightness-blinking: Brightness while blinking

- section: Brightness
- relevance: 4 - the value does not always reach the hardware at once

What does `led_set_brightness()` do when software blinking is active, for a
zero value and for a non-zero value, and when does the change reach the
hardware?

## leds.brightness-work: Deferred brightness work

- section: Brightness
- relevance: 4 - ordering of two quick changes depends on it

How does the core deliver a brightness change to a driver whose callback may
sleep: which work item does it use, what is guaranteed when two changes are
requested before the work runs, and what happens to an error that the callback
returns? Start from `set_brightness_delayed()`.

## leds.workqueue: LED workqueue

- section: Brightness
- relevance: 3 - one slow callback can delay other LEDs

What kind of workqueue runs the deferred brightness work, is it shared between
LEDs, and what does that mean for a callback that blocks for a long time?
Start from `leds_init()`.

## leds.set-brightness-sync: Synchronous brightness setting

- section: Brightness
- relevance: 3 - its error returns differ from what the name suggests

What does `led_set_brightness_sync()` return when the LED is blinking, when
the driver has no blocking callback, and when the LED is suspended?

## leds.brightness-field: Cached brightness value

- section: Brightness
- relevance: 3 - drivers and triggers read it without a lock

What does the `brightness` member of `struct led_classdev` hold, who writes it,
and is any lock held when the core writes it? Can it differ from what the
hardware shows?

# Blinking

## leds.blink-variants: Blink functions

- section: Blink
- relevance: 4 - one of them may sleep and the others are called from atomic context

Which functions start blinking on an LED, which of them may sleep, and what do
zero delays mean to each? Start from `led_blink_set()`,
`led_blink_set_nosleep()` and `led_blink_set_oneshot()`.

## leds.blink-set-callback: Hardware blink callback

- section: Blink
- relevance: 4 - the rule on sleeping depends on another callback

What are the requirements for a driver's `blink_set` callback in order to
assure safe usage: when may it sleep, what must it do with the delay values it
is given, and how is hardware blinking turned off again?

## leds.software-blink: Software blink fallback

- section: Blink
- relevance: 4 - the return value of the driver selects it

When does the core blink an LED in software, which timer and which members of
`struct led_classdev` carry the state, and at what brightness does the LED
blink? Start from `led_blink_setup()` and `led_timer_function()`.

## leds.blink-stop: Stopping a blink

- section: Blink
- relevance: 4 - a timer left running touches a freed LED

What are the requirements for stopping software and hardware blinking in order
to assure safe usage: which calls stop each, from which context may they be
made, and what does a direct call to the driver's `brightness_set` do to a
blink in progress? Start from `led_stop_software_blink()`.

## leds.oneshot-blink: One-shot blink

- section: Blink
- relevance: 3 - activity triggers call it at a high rate

What does `led_blink_set_oneshot()` do when a one-shot blink is already
running, what does its `invert` argument change, and does a one-shot blink
ever use the driver's `blink_set`?

## leds.own-timer-triggers: Triggers with their own timer

- section: Blink
- relevance: 3 - they reach into state that is private to the core

What are the requirements for a trigger that drives an LED from its own timer
in order to assure safe usage together with `led_set_brightness()`: which bits
of `work_flags` must it set, test and clear, and when? Start from
`drivers/leds/trigger/ledtrig-heartbeat.c`.

# Triggers

## leds.trigger-struct: Trigger structure

- section: Trigger core
- relevance: 4 - the two kinds of trigger have different rules

What does `struct led_trigger` represent, what is the difference between a
trigger with `activate` and `deactivate` callbacks and one without, and how
many LEDs can one trigger drive at once?

## leds.trigger-register: Trigger registration

- section: Trigger core
- relevance: 4 - registration attaches the trigger to existing LEDs at once

Which functions register a trigger, what does registration do to LEDs that
already exist, and when does registration fail? Start from
`led_trigger_register()`, `devm_led_trigger_register()` and
`module_led_trigger()`.

## leds.trigger-unregister: Trigger unregistration

- section: Trigger core
- relevance: 4 - the precondition is not checked in every case

What are the requirements for calling `led_trigger_unregister()` in order to
assure safe usage: what does it do to LEDs that use the trigger, what state
must the trigger structure be in before the call, and what may the caller free
afterwards?

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

## leds.trigger-set: Attaching a trigger

- section: Trigger core
- relevance: 5 - the order of its steps is what a change must preserve

What does `led_trigger_set()` do, in order, when it replaces one trigger with
another, which lock must the caller hold, and in what state is the LED left
when the `activate` callback of the new trigger fails?

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

## leds.trigger-locks: Trigger locks and their order

- section: Trigger core
- relevance: 5 - a new path that nests them the other way deadlocks

Which locks protect the list of triggers, the list of LEDs and the trigger of
one LED, in what order do they nest with each other and with `led_access`, and
which list is walked under RCU? Start from `triggers_list_lock`,
`leds_list_lock` and `trigger_lock`.

## leds.trigger-uevent: Trigger change events

- section: Trigger core
- relevance: 2 - user space depends on it, and few know that it exists

What does the core tell user space when the trigger of an LED changes, through
which mechanism, and what happens when sending fails?

## leds.trigger-callbacks: Activate and deactivate callbacks

- section: Writing a trigger
- relevance: 5 - what deactivate leaves running is a use after free

What are the requirements for the `activate` and `deactivate` callbacks of a
trigger in order to assure safe usage: which locks are held when they run, may
they sleep, and what must `deactivate` have stopped before it frees the data of
the trigger?

## leds.trigger-data: Trigger data for each LED

- section: Writing a trigger
- relevance: 4 - a handler that runs at the wrong moment reads a stale pointer

How does a trigger keep data for each LED it is attached to, which accessors
read that data in a sysfs handler, and at which points of attaching and
detaching is the data valid? Start from `led_set_trigger_data()` and
`led_trigger_get_drvdata()`.

## leds.trigger-attributes: Trigger sysfs attributes

- section: Writing a trigger
- relevance: 4 - the order against activate and deactivate is the whole contract

How does a trigger add sysfs attributes to the LEDs it is attached to, on which
device do they appear, and in what order are they created and removed relative
to `activate` and `deactivate`? Start from the `groups` member of
`struct led_trigger`.

## leds.default-pattern-init: Default pattern at activation

- section: Writing a trigger
- relevance: 2 - used by a few triggers and one driver

What is `LED_INIT_DEFAULT_TRIGGER` for, who sets it and who clears it, and who
frees the array that `led_get_default_pattern()` returns?

## leds.private-trigger: Private triggers

- section: Writing a trigger
- relevance: 4 - decides which LEDs may select a trigger

What is `struct led_hw_trigger_type` for, how do the `trigger_type` members of
an LED and of a trigger decide which triggers an LED may use, and what does the
class return for a read of `brightness` while such a trigger is active? Start
from `trigger_relevant()`.

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

# Hardware control

## leds.hw-control-callbacks: Hardware control callbacks

- section: Offload to hardware
- relevance: 4 - the trigger calls one of them without a check

What are the requirements for an LED driver that offers hardware control in
order to assure safe usage: which callbacks and which field must it set
together, what must a callback return when a mode is not supported, and how is
hardware control turned off? Start from `hw_control_trigger` in
`include/linux/leds.h`.

## leds.hw-control-netdev: Netdev trigger offload

- section: Offload to hardware
- relevance: 4 - the only trigger that uses hardware control

How does the netdev trigger decide between hardware control and software
blinking, which conditions must all hold for hardware control, and what does a
write return to user space when neither is possible? Start from
`can_hw_control()` in `drivers/leds/trigger/ledtrig-netdev.c`.

## leds.netdev-locking: Netdev trigger locking

- section: Offload to hardware
- relevance: 3 - it nests networking locks around its own

Which locks does the netdev trigger take, in what order, and which of its
paths run with the RTNL lock already held? Start from `set_device_name()` and
`netdev_trig_notify()`.

## leds.hw-control-providers: Hardware control providers

- section: Offload to hardware
- relevance: 2 - they all live outside the LED directory

Where in the tree are LEDs registered that offer hardware control, and which
layer fills in the callbacks on behalf of a network PHY driver? Start from
`of_phy_led()`.

# Patterns

## leds.pattern-callbacks: Pattern callbacks

- section: Pattern support
- relevance: 3 - the trigger changes the callbacks when they are inconsistent

What are the requirements for a driver's `pattern_set` and `pattern_clear`
callbacks in order to assure safe usage: what does the pattern trigger do when
only one of them is set, what do the entries of `struct led_pattern` and the
repeat count mean, and when is each callback called?

## leds.pattern-trigger: Pattern trigger

- section: Pattern support
- relevance: 2 - one file, with three kinds of pattern

Which kinds of pattern does the pattern trigger run, which timer drives each,
and how many entries does a software pattern need? Start from
`drivers/leds/trigger/ledtrig-pattern.c`.

# The multicolor class

## leds.mc-struct: Multicolor structures

- section: Multicolor
- relevance: 4 - three similar fields of a sub-LED mean different things

What do `struct led_classdev_mc` and `struct mc_subled` hold, who allocates the
array of sub-LEDs, and what do the `intensity`, `brightness` and
`max_intensity` members of a sub-LED each mean?

## leds.mc-register: Multicolor registration

- section: Multicolor
- relevance: 4 - it overwrites a field that the driver may have set

What does `led_classdev_multicolor_register_ext()` check and set before it
registers the LED, which members of the embedded `struct led_classdev` does it
overwrite, and how can the driver of a multicolor LED add sysfs attributes of
its own?

## leds.mc-calc: Component calculation

- section: Multicolor
- relevance: 4 - the core never calls it for the driver

What does `led_mc_calc_color_components()` compute, from which fields, and who
is expected to call it, and when?

## leds.mc-sysfs: Multicolor sysfs files

- section: Multicolor
- relevance: 3 - a write changes the hardware only in some states

Which sysfs files does the multicolor class add, what does a write to the
intensity file do to the hardware, and how is a written value limited? Start
from `multi_intensity_store()`.

## leds.mc-kernel-set: Multicolor from kernel code

- section: Multicolor
- relevance: 3 - misuse is logged once and then ignored

How does kernel code set the color of a multicolor LED, and what do
`led_mc_set_brightness()` and `led_mc_trigger_event()` do when the LED is not
multicolor or the number of colors does not match?

## leds.color-ids: Color identifiers

- section: Multicolor
- relevance: 3 - three places have to change together

Where are the LED color identifiers defined, which table turns them into
names, and what must change together when a color is added? Start from
`LED_COLOR_ID_MAX`.

# The flash class

## leds.flash-struct: Flash structures

- section: Flash
- relevance: 3 - units and mandatory operations are easy to guess wrong

What do `struct led_classdev_flash` and `struct led_flash_ops` hold, which
operations must a driver supply, and in which units are flash brightness and
flash timeout expressed?

## leds.flash-register: Flash registration

- section: Flash
- relevance: 4 - the checks apply only when a flag is set

What does `led_classdev_flash_register_ext()` require of the LED before it
registers it, what does `LED_DEV_CAP_FLASH` select, and how are the flash sysfs
groups chosen?

## leds.flash-settings: Flash setting helpers

- section: Flash
- relevance: 3 - the stored value is not always the value passed in

What do `led_set_flash_brightness()` and `led_set_flash_timeout()` do with a
value that is outside the limits or between two steps, what do they do when the
LED is suspended, and what do they return when the driver lacks the operation?
Start from `led_clamp_align()`.

## leds.flash-strobe: Flash strobe helpers

- section: Flash
- relevance: 3 - the inline helpers check less than the others

What are the requirements for calling `led_set_flash_strobe()` and
`led_get_flash_strobe()` in order to assure safe usage: what must be true of
the flash LED and of its operations before each call? Which lock do the sysfs
handlers hold around them?

## leds.flash-v4l2: V4L2 flash wrapper

- section: Flash
- relevance: 3 - it takes the LED away from sysfs while it is open

How does the V4L2 flash wrapper use a flash LED: which functions create and
release it, what does it do to the sysfs interface and to the trigger of the
LED while the sub-device is open, and which brightness function does it call?
Start from `v4l2_flash_init()`.

# LED consumers

## leds.consumer-get: Getting an LED

- section: Consumers
- relevance: 3 - the return value for a missing LED decides probe deferral

Which functions let a driver obtain an LED that another driver registered, how
does each find the LED, and what do they return when the LED is described in
firmware and is not registered yet? Start from `led_get()` and
`devm_of_led_get()`.

## leds.consumer-refs: Consumer references

- section: Consumers
- relevance: 3 - two references are taken, and both must be dropped

Which references does getting an LED take, which function drops them, and what
keeps the driver that provides the LED from being unloaded while a consumer
holds the LED? Start from `led_put()`.

## leds.consumer-lookup: Lookup table

- section: Consumers
- relevance: 2 - used on systems without a firmware description

What is `struct led_lookup_data` for, how are its entries matched, and what are
the requirements for the lifetime of an entry passed to `led_add_lookup()` in
order to assure safe usage?

# Power management

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

# Firmware description

## leds.dt-common: Common binding

- section: Device tree
- relevance: 4 - every LED binding refers to it

Which file defines the properties common to all LED nodes, which of those
properties does it mark as deprecated, and how does the binding of one LED
controller include the common properties? Start from
`Documentation/devicetree/bindings/leds/common.yaml`.

## leds.dt-constants: Function and color constants

- section: Device tree
- relevance: 3 - a made-up string defeats the naming scheme

Where are constants such as `LED_FUNCTION_STATUS` and `LED_COLOR_ID_RED`
defined, which type does each of the two properties take in a device tree, and
what does the tree say to do when no existing constant fits?

## leds.dt-multicolor: Multicolor binding

- section: Device tree
- relevance: 2 - narrow, but the node name is checked

How is a multicolor LED described in a device tree: which node name and which
`color` values does the binding require, and how are the sub-LEDs described?
Start from `Documentation/devicetree/bindings/leds/leds-class-multicolor.yaml`.

## leds.dt-links: Trigger sources and consumers

- section: Device tree
- relevance: 2 - two bindings that are easy to confuse

Which bindings describe an LED that follows another device and a device that
uses an LED, and which code in the tree reads each? Start from
`Documentation/devicetree/bindings/leds/trigger-source.yaml` and
`Documentation/devicetree/bindings/leds/leds-consumer.yaml`.

# User-space LEDs

## leds.uleds: User-space LED driver

- section: LEDs made by user space
- relevance: 2 - one small driver with a user-space interface

How does user space create an LED through the `uleds` driver, what does the
driver check in the name it is given, and how does user space learn of a
brightness change? Start from `drivers/leds/uleds.c`.
