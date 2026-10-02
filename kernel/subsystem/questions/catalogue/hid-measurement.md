# Questions: HID Subsystem (measurement set)

- guide: hid.md
- title: HID Subsystem

A wide set of questions about the HID core: the bus and the structures a
parsed report descriptor turns into, what a transport driver owes the core,
what a HID device driver's probe, remove and event callbacks may assume, the
bridges to input, hidraw, hiddev and uhid, quirks, and HID-BPF. It is used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 2,350 words and
was never checked against current sources. The inside of individual device
drivers and of the USB, I2C and Bluetooth protocols is left out. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## hid.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold the HID bus and report parser, the bridge to the input layer,
the raw character device, the legacy USB character device, the user-space
transport, the generic driver, the quirk tables, the device id constants, the
debugfs support, HID-BPF, the USB and I2C transports, and the headers drivers
include? A table. Start from `drivers/hid/` and `include/linux/hid.h`.

## hid.layers: Layers and their roles

- section: Finding your way
- relevance: 4 - every rule depends on which layer the code is in
- words: 90

What are the layers between a physical HID device and user space (transport
driver, core, device driver, listeners), which structure represents each, and
which in-tree files outside `drivers/hid/` register a `struct hid_ll_driver`?

## hid.entry-points: Entry points

- section: Finding your way
- relevance: 4 - where to start reading for each job
- words: 100

For each job (register a device from a transport, bind a driver, parse the
report descriptor, deliver an input report, send a report to the device,
connect the input layer, open the device on behalf of a user), which function
do you start reading from? A table.

## hid.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - some contracts are written only there, and some are out of date
- words: 70

Which files under `Documentation/hid/` describe the transport driver contract,
the raw device, the user-space transport, HID-BPF and report descriptors, and
which ABI files under `Documentation/ABI/` cover HID? Start from
`Documentation/hid/index.rst`.

## hid.tests: Tests

- section: Finding your way
- relevance: 3 - a core change is expected to pass them
- words: 80

Which tests cover the HID core and drivers: the KUnit suites built from
`drivers/hid/`, and the selftests under `tools/testing/selftests/hid/`? How do
the selftests create devices without hardware, and how is each kind run?

# The structures

## hid.device-struct: Device structure

- section: What a parsed device looks like
- relevance: 4 - most driver code reads these fields
- words: 110

Group the fields of `struct hid_device` by job: identity, report descriptors,
parsed reports and collections, the bound driver, the transport, status and
claimed bits, locks, and listener state. Which fields belong to the transport
and which to the device driver?

## hid.rdesc-copies: Report descriptor copies

- section: What a parsed device looks like
- relevance: 4 - three pointers with three owners
- words: 80

How many copies of the report descriptor does a `struct hid_device` point at,
who allocates each, when may two of the pointers be equal, and where is each
freed? Start from `hid_parse_report()`, `hid_open_report()` and
`hid_close_report()`.

## hid.report-structs: Reports, fields and usages

- section: What a parsed device looks like
- relevance: 4 - every driver indexes these
- words: 100

How do `struct hid_report_enum`, `struct hid_report`, `struct hid_field`,
`struct hid_usage` and `struct hid_collection` relate, how is a report looked
up by type and id, and what do `maxfield`, `maxusage`, `maxcollection` and
`maxapplication` count?

## hid.field-arrays: Field array sizes

- section: What a parsed device looks like
- relevance: 4 - decides which index checks are enough
- words: 70

How many entries do the `usage`, `value` and `new_value` arrays of a
`struct hid_field` have, relative to the field's report count and the number of
usages the descriptor declared? Start from `hid_add_field()` and
`hid_register_field()`.

## hid.padding-fields: Fields without usages

- section: What a parsed device looks like
- relevance: 3 - field numbers do not match main items in the descriptor
- words: 50

Does a main item in the report descriptor that declares no usages become a
`struct hid_field`, and how does that affect the index a driver uses in
`report->field[]`? Start from `hid_add_field()`.

## hid.report-id-byte: Report id byte

- section: What a parsed device looks like
- relevance: 4 - off-by-one in every buffer a driver builds
- words: 80

When does a report buffer start with a report id byte: for numbered and
unnumbered reports on the input path, in the buffer passed to
`hid_hw_raw_request()`, and in the length `hid_report_len()` returns? Start
from `hid_get_report()` and `__hid_request()`.

## hid.limits: Parser and buffer limits

- section: What a parsed device looks like
- relevance: 3 - numbers people quote from memory
- words: 80

What are the limits on report ids, fields per report, usages per field,
descriptor size, report buffer size, and the parser's global and collection
stacks? Where is each defined, which can a transport override, and which grow
on demand?

## hid.groups: Device groups

- section: What a parsed device looks like
- relevance: 3 - decides which driver binds without an id table entry
- words: 70

What is a device's group, which function sets it and from what, when is it
computed again, and which drivers bind by group? Start from `hid_set_group()`
and `hid_scan_report()`.

## hid.driver-callbacks: Driver callbacks

- section: What a parsed device looks like
- relevance: 4 - the whole driver API in one table
- words: 120

Give a table of the callbacks in `struct hid_driver`: when the core calls each
and what the return value means. Include the ones for mapping, events, power
management and the open and close notifications.

# Transport drivers

## hid.ll-register: Registering a device

- section: Device lifetime in a transport
- relevance: 5 - the sequence every transport follows
- words: 90

Which calls does a transport driver make to allocate, fill in and register a
`struct hid_device`, which fields must it set before registering, and from
which moment may the core call the transport's callbacks? Start from
`usbhid_probe()` and `Documentation/hid/hid-transport.rst`.

## hid.add-device-checks: Registration checks

- section: Device lifetime in a transport
- relevance: 4 - each failure has its own error code
- words: 80

List, in order, what `hid_add_device()` checks and does before `device_add()`,
and the error each failed check returns. Which of those errors is normal and
should not be logged by the transport?

## hid.destroy-device: Destroying a device

- section: Device lifetime in a transport
- relevance: 5 - leaks and use-after-free on unplug
- words: 80

What does `hid_destroy_device()` do, step by step, when is the memory of the
`struct hid_device` actually freed and by which function, and what can still
hold a reference after it returns? Start from `hiddev_free()`.

## hid.ll-free-usage: Freeing the device in a transport

- section: Device lifetime in a transport
- relevance: 4 - the structure embeds a refcounted device
- words: 80

In a transport driver, what usage around freeing a `struct hid_device` is
unsafe (after a failed `hid_add_device()`, on removal, with devres or
`kfree()`), and what that looks similar is correct? Name an in-tree transport
that shows the correct form.

## hid.ll-teardown-order: Transport teardown order

- section: Device lifetime in a transport
- relevance: 4 - in-flight I/O against a device that is going away
- words: 80

On disconnect, in what order must a transport stop its own I/O, call
`hid_destroy_device()` and free its private data, and what does the core
guarantee about transport callbacks once `hid_destroy_device()` has returned?
Start from `usbhid_disconnect()` and `i2c_hid_core_remove()`.

## hid.ll-callbacks: Transport callbacks

- section: The transport callback contract
- relevance: 5 - which are mandatory and what each must do
- words: 120

Give a table of the callbacks in `struct hid_ll_driver`: who calls each, which
are mandatory, which the core calls without checking for NULL, and what the
core does when an optional one is missing.

## hid.ll-parse: Parse callback

- section: The transport callback contract
- relevance: 4 - a parse that succeeds can still fail registration
- words: 60

What must a transport's `parse` callback do with the report descriptor it
reads, what happens if it returns success without doing it, and how often is
it called for one device?

## hid.ll-open-close: Open and close counting

- section: The transport callback contract
- relevance: 4 - the documentation and the code may differ
- words: 80

When several users open one HID device (input handlers, hidraw, a driver), how
many times is the transport's `open` callback called, and who counts and
serialises the calls? Say whether `Documentation/hid/hid-transport.rst` and
`hid_hw_open()` agree.

## hid.ll-raw-request: Raw request contract

- section: The transport callback contract
- relevance: 5 - buffer layout and return value are easy to get wrong
- words: 100

What must a transport's `raw_request` callback do: the layout of the buffer
for get and set, where the report id goes, what it returns, whether it may
sleep, and what the core has already checked before calling it? Start from
`__hid_hw_raw_request()` and `usbhid_raw_request()`.

## hid.ll-output-report: Output report contract

- section: The transport callback contract
- relevance: 4 - "asynchronous" in the documentation is not "non-blocking"
- words: 80

What must a transport's `output_report` callback do and not do, may it sleep,
what does the core return when the callback is absent, and how do callers fall
back? Start from `__hid_hw_output_report()`, `usbhid_output_report()` and
`hidraw_send_report()`.

## hid.ll-request-wait: Request and wait

- section: The transport callback contract
- relevance: 3 - optional, and the fallback behaves differently
- words: 70

What do the `request` and `wait` callbacks do, which transports implement them,
and what does the core do instead when `request` is missing? Start from
`hid_hw_request()` and `__hid_request()`.

## hid.ll-input-report: Feeding input reports

- section: The transport data path
- relevance: 5 - the size the core trusts decides whether it reads past the buffer
- words: 100

What is the difference between `hid_input_report()` and
`hid_safe_input_report()`: which sizes does each pass down, what does
`hid_report_raw_event()` check and do when the data is shorter than the report
the descriptor declares, and which in-tree transports call which?

## hid.ll-input-context: Input path context and errors

- section: The transport data path
- relevance: 4 - called from interrupt handlers
- words: 80

From which contexts do transports call `hid_input_report()`, what lock does it
take and how, and what does it return when no driver is bound, when a probe or
remove is in progress, and when the report id is unknown? Start from
`__hid_input_report()`.

## hid.ll-sync-responses: Responses to requests

- section: The transport data path
- relevance: 3 - the same bytes must not be parsed twice
- words: 60

Which replies from the device does a transport feed into the input path and
which does it hand straight back to the caller: the reply to a `raw_request`
get, and the reply to a `request` get? Where does the core itself feed a reply
back?

## hid.ll-pm: Transport power management

- section: The transport data path
- relevance: 3 - the driver's callbacks only run if the transport calls them
- words: 80

Which core helpers must a transport call from its own suspend and resume paths
for a HID driver's power management callbacks to run, what do the `power`,
`idle` and `may_wakeup` callbacks do, and what does the core assume when
`may_wakeup` is missing?

## hid.hid-is-usb: USB transport test

- section: The transport data path
- relevance: 3 - where it is defined decides what a driver must depend on
- words: 50

What exactly does `hid_is_usb()` test, in which module is it defined, and what
does that mean for the Kconfig dependencies of a driver that calls it?

# Binding a driver

## hid.match-flow: Matching a driver

- section: How a driver gets bound
- relevance: 4 - explains why the generic driver does or does not bind
- words: 110

How is a driver chosen for a device: the id table and dynamic ids, the optional
`match` callback, how the generic driver defers to a specific one, the quirks
and the module parameter that force the generic driver, and what happens to a
bound generic driver when a specific driver's module loads later? Start from
`hid_check_device_match()` and `hid_generic_match()`.

## hid.have-special-driver: Special driver list

- section: How a driver gets bound
- relevance: 3 - reviewers ask for entries that are no longer needed
- words: 60

What is the list `hid_have_special_driver` in `drivers/hid/hid-quirks.c` for in
this tree, and does a new device driver need to add its ids to it for the
driver to bind?

## hid.probe-sequence: Core work around probe

- section: How a driver gets bound
- relevance: 5 - what a probe callback may assume
- words: 110

List in order what the core does before and after calling a driver's `probe`:
the lock it takes, the HID-BPF descriptor fixup, the devres group, the quirks,
setting the driver pointer, what it does when the driver has no `probe`, and
when incoming reports start to be delivered. Start from `hid_device_probe()`
and `__hid_device_probe()`.

## hid.probe-failure: Probe failure cleanup

- section: How a driver gets bound
- relevance: 5 - decides which error paths leak
- words: 90

When `probe` returns an error, what does the core undo by itself and what must
the driver have undone before returning? Cover parsed reports, devres
allocations, a started transport, connected listeners, and the input lock.

## hid.remove-sequence: Core work around remove

- section: How a driver gets bound
- relevance: 5 - the order decides what is freed while still in use
- words: 100

List in order what `hid_device_remove()` does, including what it does when the
driver has no `remove` callback, when devres resources are released relative to
the callback, and when the driver pointer is cleared.

## hid.remove-usage: Stopping hardware in remove

- section: How a driver gets bound
- relevance: 5 - a missing stop leaves listeners pointing at freed data
- words: 90

What usage of `hid_hw_stop()` in or around a driver's `remove` callback is
unsafe (missing, doubled, in the wrong order with respect to the driver's own
cleanup), and what that looks similar is correct? Name in-tree drivers that
show the correct forms.

## hid.devres-group: Devres in device drivers

- section: How a driver gets bound
- relevance: 4 - what devm on the HID device is tied to
- words: 80

What lifetime do `devm_` allocations made against `&hdev->dev` have in a HID
device driver: during probe, after probe has returned, and across an unbind and
rebind? What happens to them if they are made against the parent device
instead?

## hid.devres-stop-usage: Stopping hardware from devres

- section: How a driver gets bound
- relevance: 3 - interacts with the core's default remove
- words: 90

If a driver registers a devres action that calls `hid_hw_stop()`, what usage is
unsafe (with respect to the `remove` callback and to the order devres releases
other resources), and what is correct? Name the in-tree drivers that do this
and how they handle `remove`.

## hid.quirks-reset: Quirks set by a driver

- section: How a driver gets bound
- relevance: 3 - a quirk set at the wrong time is silently lost or sticks
- words: 60

When is `hdev->quirks` recomputed, and so where must a device driver that wants
to add a quirk set it, relative to `hid_parse()` and `hid_hw_start()`? Start
from `hid_lookup_quirk()` and its callers.

# Probe, start and stop

## hid.parse-call: Parsing in probe

- section: The driver's side of probe
- relevance: 4 - the first call in nearly every probe
- words: 80

What does `hid_parse()` do, what state must the device be in, which errors can
it return, may it be called twice, and what does it leave behind on failure?
Start from `hid_open_report()`.

## hid.hw-start: Starting the hardware

- section: The driver's side of probe
- relevance: 5 - after it succeeds the driver is visible to user space
- words: 90

List what `hid_hw_start()` does in order, what it undoes itself when it fails,
what a connect mask of zero means, and what obligation a successful return
places on the driver.

## hid.connect-mask: Connect mask

- section: The driver's side of probe
- relevance: 4 - decides which device nodes appear
- words: 100

What does each `HID_CONNECT_` bit request, how do quirks and the bus type change
the mask inside `hid_connect()`, when does `hid_connect()` fail for lack of
listeners, and what is `HID_CONNECT_DRIVER` for?

## hid.hw-stop: Stopping the hardware

- section: The driver's side of probe
- relevance: 4 - the mirror of start, with one extra step
- words: 70

List what `hid_hw_stop()` does in order, including anything it does about the
input lock, and say whether it is safe to call when `hid_hw_start()` failed or
was never called.

## hid.hw-open-close: Opening from a driver

- section: The driver's side of probe
- relevance: 4 - without an opener some transports deliver nothing
- words: 80

When must a device driver call `hid_hw_open()` itself, what happens to incoming
reports on the USB and I2C transports while nobody has the device open, and
what must balance the call? Name a driver that opens the device in probe.

## hid.io-start-stop: Input lock during probe

- section: The driver's side of probe
- relevance: 4 - a driver that talks to the device in probe needs it
- words: 90

What is `driver_input_lock`, who holds it during probe and remove, what do
`hid_device_io_start()` and `hid_device_io_stop()` do to it, and what happens
to reports that arrive while it is held?

## hid.io-start-usage: Enabling input in probe

- section: The driver's side of probe
- relevance: 3 - unbalanced calls warn or deadlock
- words: 80

What usage of `hid_device_io_start()` and `hid_device_io_stop()` in probe or
remove is unsafe, and what is correct: on the error path after input was
enabled, before `hid_hw_stop()`, and calling either twice? What do the core's
probe and stop paths do about it themselves?

## hid.probe-visibility: Visibility after start

- section: The driver's side of probe
- relevance: 5 - callbacks run before probe has finished
- words: 90

Once `hid_hw_start()` has returned inside probe, which driver callbacks and
which user-space requests can already run, which are still held off and by
what, and so what usage of driver private data around `hid_hw_start()` is
unsafe and what is correct?

## hid.async-teardown-usage: Timers and work at teardown

- section: The driver's side of probe
- relevance: 5 - the commonest use-after-free in device drivers
- words: 90

For a driver that starts timers, work items or LED and power-supply class
devices, what ordering at remove and on the probe error path is unsafe with
respect to `hid_hw_stop()` and devres release, and what is correct? Name an
in-tree driver for each correct form.

## hid.usb-parent-usage: Assuming a USB parent

- section: The driver's side of probe
- relevance: 5 - a device from uhid or another transport crashes the driver
- words: 80

What usage of `hdev->dev.parent` as a USB interface (for example through
`to_usb_interface()` or `hid_to_usb_dev()`) is unsafe, and what is correct for
a driver that only supports USB and for one that supports several transports?
How can a non-USB device carry a USB bus type?

# Events

## hid.input-path: Path of an input report

- section: The input path
- relevance: 5 - the order decides what each hook sees
- words: 120

Trace an input report from `hid_input_report()` to the listeners, in order:
HID-BPF, the driver's `raw_event`, size checks, hiddev, hidraw, field parsing,
the driver's `event` and `report`, and the input layer. Which steps are skipped
when only hidraw has claimed the device, and how do `report_table` and
`usage_table` filter?

## hid.raw-event-return: Raw event return value

- section: The input path
- relevance: 4 - decides whether the core goes on to parse the report
- words: 60

What does the core do for a negative, zero and positive return from a driver's
`raw_event`, and may the callback modify the data it is given? Compare the
code in `__hid_input_report()` with the comment above `struct hid_driver`.

## hid.event-return: Event return value

- section: The input path
- relevance: 4 - decides whether the input layer sees the usage
- words: 60

What does the core do for a negative, zero and positive return from a driver's
`event` callback, and what is logged? Start from `hid_process_event()`.

## hid.callback-context: Context of event callbacks

- section: The input path
- relevance: 5 - sleeping in them works on one transport and crashes on another
- words: 80

In what context do `raw_event`, `event` and `report` run on the USB, I2C,
Bluetooth and uhid transports, so what may a driver that must work on all of
them do in these callbacks, and which locks does it hold?

## hid.requests-from-callbacks: Requests from event callbacks

- section: The input path
- relevance: 4 - the usual reason for a work item in a driver
- words: 80

Which of `hid_hw_request()`, `hid_hw_raw_request()` and `hid_hw_output_report()`
may sleep on the USB transport, and so what usage from `raw_event` or `event` is
unsafe and what do drivers do instead?

## hid.raw-event-size-usage: Indexing raw event data

- section: The input path
- relevance: 5 - the device chooses the length
- words: 80

What does the core guarantee about `size` and about the bytes of `data` when it
calls `raw_event`, so what indexing of `data` is unsafe and what check makes it
correct? Is a report shorter than the descriptor declares dealt with before or
after `raw_event` runs, and how?

## hid.unbound-reports: Reports with no driver bound

- section: The input path
- relevance: 3 - what protects the read path at unbind
- words: 60

What happens to a report that arrives after the driver has been unbound or
while it is being removed, and which field and lock make that safe?

# Requests to the device

## hid.request-kinds: Three ways to send

- section: Sending reports
- relevance: 4 - picking the wrong one changes the channel and the blocking
- words: 100

What is the difference between `hid_hw_request()`, `hid_hw_raw_request()` and
`hid_hw_output_report()`: what each takes, which channel it uses, whether it
waits for the device, what it returns, and what each does when the transport
lacks the matching callback?

## hid.raw-request-buffer-usage: Request buffers

- section: Sending reports
- relevance: 5 - works on one transport, corrupts memory on another
- words: 90

What buffer passed to `hid_hw_raw_request()` or `hid_hw_output_report()` is
unsafe (where it lives, how long it is, what is in its first byte), and what
is correct? What lengths does the core reject before the transport sees them?

## hid.report-buf-helpers: Building a report

- section: Sending reports
- relevance: 3 - the helpers hide a size rule
- words: 80

What do `hid_alloc_report_buf()`, `hid_set_field()` and `hid_output_report()`
do, how big is the buffer the first one returns and why, and what is the widest
field `hid_field_extract()` and its writing counterpart handle?

# Report descriptor fixups

## hid.report-fixup-contract: Fixup contract

- section: Fixing up the descriptor
- relevance: 5 - ownership of the returned pointer
- words: 100

What buffer does the core pass to a driver's `report_fixup`, may the driver
modify it, what may the driver return (the same buffer, a part of it, a static
array, a new allocation), what does the core do with the returned pointer, and
who frees what? Start from `hid_open_report()`.

## hid.report-fixup-alloc-usage: Allocating in a fixup

- section: Fixing up the descriptor
- relevance: 4 - a leak on every probe failure
- words: 80

When a driver builds a replacement descriptor in allocated memory, what usage
leaks or frees too early, and what is correct? Name an in-tree driver that
returns an allocated descriptor and say where it frees it.

## hid.fixup-size-usage: Descriptor size in a fixup

- section: Fixing up the descriptor
- relevance: 4 - the device chooses the descriptor length
- words: 60

What indexing of the descriptor in a `report_fixup` is unsafe, and what check
makes it correct? How does the driver report a changed length?

## hid.fixup-order: Fixup order with HID-BPF

- section: Fixing up the descriptor
- relevance: 3 - two fixups can apply to one device
- words: 60

In what order are a HID-BPF descriptor fixup and the driver's `report_fixup`
applied, which descriptor does each see, and which one does user space read
from sysfs and from hidraw?

# Validating what the device declared

## hid.field-index-usage: Indexing fields

- section: Trusting the descriptor
- relevance: 5 - malicious and fuzzed descriptors reach every driver
- words: 80

What access to `report->field[]` and to a report found through
`report_id_hash[]` or `report_list` is unsafe, and what check makes it correct?
What does the core already guarantee about a report it hands to a callback?

## hid.validate-values: Validation helper

- section: Trusting the descriptor
- relevance: 4 - the helper checks less than its name suggests
- words: 80

What exactly does `hid_validate_values()` check and return, what does an id of
zero mean to it, and what does it not check that a driver still must?

## hid.usage-index-usage: Indexing usages and values

- section: Trusting the descriptor
- relevance: 4 - out-of-bounds access chosen by the device
- words: 70

What access to `field->usage[]` and `field->value[]` is unsafe, and which bound
is the right one to check for each? Does `hid_set_field()` check its offset?

## hid.inputs-list-usage: Assuming an input device

- section: Trusting the descriptor
- relevance: 5 - a recurring crash with descriptors that map no input
- words: 80

What usage of `hdev->inputs`, of `field->hidinput` or of a `struct hid_input`
saved in `input_configured` is unsafe after `hid_hw_start()` has succeeded, and
what check makes it correct? Can `hid_hw_start()` succeed with no input device
registered?

# The input bridge

## hid.hidinput-connect: Connecting the input layer

- section: The input bridge
- relevance: 4 - where input devices come from
- words: 100

List what `hidinput_connect()` does in order, when it declines to create any
input device, how it treats an input device that ended up with no capabilities,
and how it unwinds on failure.

## hid.input-mapping-returns: Mapping callback returns

- section: The input bridge
- relevance: 5 - three-way return that reviewers misread
- words: 80

What does the core do for a negative, zero and positive return from
`input_mapping`, and from `input_mapped`? What state must the driver leave in
the usage and the bit pointer for a positive return to have an effect? Start
from `hidinput_configure_usage()`.

## hid.hide-usage-usage: Hiding a usage

- section: The input bridge
- relevance: 3 - looks like a bug and is not
- words: 60

How does a driver make a usage produce no input capability and no events, which
return values of `input_mapping` achieve it and how do they differ, and what do
`hid_map_usage()` and `hid_map_usage_clear()` do when given a code out of
range?

## hid.input-configured: Input configured callback

- section: The input bridge
- relevance: 3 - the last chance before the device is visible
- words: 60

When is `input_configured` called relative to mapping and to registration of
the input device, how many times for one HID device, and what happens when it
returns an error?

## hid.input-splitting: One input device or several

- section: The input bridge
- relevance: 4 - the wrong quirk splits or merges device nodes
- words: 80

How does `hidinput_connect()` decide how many input devices to create: what do
`HID_QUIRK_MULTI_INPUT` and `HID_QUIRK_INPUT_PER_APP` each do, which wins when
both are set, who sets the second by default, and which applications are kept
together regardless?

## hid.hidinput-disconnect: Disconnecting the input layer

- section: The input bridge
- relevance: 3 - what stop tears down for the driver
- words: 60

What does `hidinput_disconnect()` unregister, free and cancel, and what makes
it safe against a LED request arriving at the same time?

## hid.battery: Battery reporting

- section: The input bridge
- relevance: 3 - the layout changed and the lifetime is devres
- words: 70

How does the core represent batteries a device reports: which structure, how
many per device, what owns their memory and the power supply registration, and
which helper returns one to a driver? Say if this tree has no such support.

# Character devices and user-space transport

## hid.hidraw-lifetime: Raw device lifetime

- section: hidraw and uhid
- relevance: 4 - files stay open across unplug
- words: 90

What is the lifetime of a `struct hidraw`: who creates it, what `exist` and
`open` mean, what `drop_ref()` does in each case, which lock protects the minor
table, and what stops an open file from using the `struct hid_device` after
disconnect?

## hid.hidraw-io: Raw device requests

- section: hidraw and uhid
- relevance: 3 - user space reaches the transport callbacks directly
- words: 80

Which core functions do a write and the get and set feature ioctls on hidraw end
up calling, what sizes are rejected, what is passed as the source for HID-BPF,
and what does revoking a hidraw file do?

## hid.uhid: User-space transport

- section: hidraw and uhid
- relevance: 3 - the transport fuzzers and tests use
- words: 80

How does uhid create a HID device from a write to its character device, in
which context does `hid_add_device()` run and why, what bus can the device
claim, and how does it implement the synchronous `raw_request`?

# HID-BPF

## hid.bpf-attach: Attaching programs

- section: HID-BPF
- relevance: 4 - the attach mechanism has been replaced once already
- words: 90

How is a HID-BPF program attached to a device in this tree: which BPF program
or map type, how the device is named, what `hid_bpf_reg()` checks and limits,
what happens to the device when a descriptor fixup program is attached or
detached, and what happens to attached programs when the device goes away?

## hid.bpf-hooks: Hooks

- section: HID-BPF
- relevance: 4 - each hook has its own return convention and context
- words: 100

Give a table of the hooks in `struct hid_bpf_ops`: where in the core each is
called from, what its return value means, whether it may sleep, and how many
programs per device each allows.

## hid.bpf-kfuncs: Kfuncs

- section: HID-BPF
- relevance: 3 - which are sleepable and which hooks may use them
- words: 80

Which kfuncs does HID-BPF export, which are marked sleepable, which may be
called from which hooks or from a syscall program, and what stops a program
called from a hook from re-entering the same hook? Start from
`drivers/hid/bpf/hid_bpf_dispatch.c`.

## hid.bpf-dispatch-locking: Dispatch and locking

- section: HID-BPF
- relevance: 3 - one list walked under two kinds of read lock
- words: 80

How is the per-device program list protected: which lock for updates, which
read-side protection on the event path and on the request paths and why they
differ, and which buffer does the event path hand to programs and to the rest
of the core afterwards?

## hid.bpf-inject: Injecting reports from BPF

- section: HID-BPF
- relevance: 3 - the input lock is taken differently
- words: 70

What is the difference between `hid_bpf_input_report()` and
`hid_bpf_try_input_report()`, from where may each be called, and how does
`__hid_input_report()` treat the input lock for each?

## hid.bpf-abi: Stability and in-tree programs

- section: HID-BPF
- relevance: 3 - out-of-tree programs depend on part of a kernel header
- words: 70

Which parts of `include/linux/hid_bpf.h` are treated as stable for BPF programs
and which are internal, where do in-tree HID-BPF programs live, and are they
built and loaded by the kernel build?

# Quirks

## hid.quirk-tables: Quirk tables and lookup

- section: Quirks
- relevance: 4 - where a device-specific workaround goes
- words: 90

Which tables does `drivers/hid/hid-quirks.c` hold, in what order does
`hid_lookup_quirk()` consult static tables, dynamic quirks and the transport's
initial quirks, which devices does `hid_ignore()` reject, and when are these
functions called?

## hid.quirk-flags: Quirk flags

- section: Quirks
- relevance: 3 - a dozen bits with terse names
- words: 110

Give a table of the `HID_QUIRK_` flags most likely to appear in a patch, saying
what each changes and which code tests it. Include the ones about input device
splitting, forcing or skipping listeners, polling, output reports and special
drivers.

# Power management

## hid.driver-pm: Driver power management

- section: Power management
- relevance: 3 - the callbacks are not dev_pm_ops
- words: 70

When are a HID driver's `suspend`, `resume` and `reset_resume` called, what is
the difference between the last two, which transports call them, and what does
the generic driver do on reset-resume?

# Changing the implementation

## hid.locks: Locks in the core

- section: What a change must preserve
- relevance: 4 - several are taken from interrupt context
- words: 110

List the locks and similar primitives in the HID core, hid-input, hidraw,
hid-debug, HID-BPF and the quirks code, what each protects, its type, and the
contexts it is taken from. Which may nest, and in what order?

## hid.core-change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - a core change touches every transport and driver
- words: 100

What must a change to the report parser, the input path or the probe and remove
paths keep working: exported function signatures used by transports and
drivers, the HID-BPF operations table, behaviour with malformed descriptors,
the tests that pin current behaviour?

## hid.new-driver-checklist: Adding a device driver

- section: What a change must preserve
- relevance: 3 - the same omissions in most new drivers
- words: 80

Which files does a new HID device driver touch besides its own source, which
registration macro does it use, how does it declare the devices it binds to,
and what must its Kconfig entry depend on?

