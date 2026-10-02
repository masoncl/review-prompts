# Questions: HID Subsystem

- guide: hid.md
- title: HID Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/hid-measurement.md` is the wider
set the readers were measured on and `catalogue/hid-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## hid.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## hid.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the HID bus and report parser; the bridge to the input
layer; the raw character device; the legacy USB character device; the user-space transport; the
generic driver; the quirk tables; the device id constants; the debugfs support; HID-BPF; the USB
and I2C transports; the headers drivers include. Where no single file in this tree does the job,
say so in the row. Start from `drivers/hid/` and `include/linux/hid.h`.

## hid.tests: KUnit suites and selftests

- section: Finding your way
- relevance: 3 - a core change is expected to pass them

What do the KUnit suites built from `drivers/hid/` cover, and what do the selftests under
`tools/testing/selftests/hid/` cover? How do the selftests create devices without hardware?

# Transport callbacks

## hid.ll-callbacks: Mandatory and optional callbacks

- section: Transport callbacks
- relevance: 5 - which are mandatory and what each must do

Which callbacks in `struct hid_ll_driver` must a transport supply, which does the core call
without checking for NULL, and what does the core do when an optional one is missing?

## hid.ll-parse: Parse callback

- section: Transport callbacks
- relevance: 4 - a parse that succeeds can still fail registration

What must a transport's `parse` callback do with the report descriptor it reads, what happens
if it returns success without doing it, and how often is it called for one device?

## hid.ll-raw-request: Raw request contract

- section: Transport callbacks
- relevance: 5 - buffer layout and return value are easy to get wrong

What must a transport's `raw_request` callback do with the buffer for a get and for a set, and
what must it return? What has `__hid_hw_raw_request()` already checked before it calls the
callback? Start from `__hid_hw_raw_request()` and `usbhid_raw_request()`.

## hid.ll-raw-request-sleep: Raw request calling context

- section: Transport callbacks
- relevance: 5 - decides from which contexts a driver may send a request

May a transport's `raw_request` callback sleep? Name in-tree code that shows it. Start from
`__hid_hw_raw_request()` and `usbhid_raw_request()`.

## hid.ll-output-report: Output report contract

- section: Transport callbacks
- relevance: 4 - "asynchronous" in the documentation is not "non-blocking"

May a transport's `output_report` callback sleep, what does the core return when the callback
is absent, and how do callers fall back? Start from `__hid_hw_output_report()`,
`usbhid_output_report()` and `hidraw_send_report()`.

## hid.ll-open-close: Open and close counting

- section: Transport callbacks
- relevance: 4 - the documentation and the code may differ

When several users open one HID device (input handlers, hidraw, a driver), how many times is the
transport's `open` callback called, and who counts and serialises the calls? Say whether
`Documentation/hid/hid-transport.rst` and `hid_hw_open()` agree.

# Device lifetime in a transport

## hid.ll-register: Registering a device

- section: Device lifetime in a transport
- relevance: 5 - the sequence every transport follows

What must a transport driver have set in a `struct hid_device` before it registers it, and from
which moment may the core call the transport's callbacks? Start from `usbhid_probe()` and
`Documentation/hid/hid-transport.rst`.

## hid.add-device-checks: Registration checks

- section: Device lifetime in a transport
- relevance: 4 - each failure has its own error code

Which checks in `hid_add_device()` can fail registration before `device_add()`, and with which
error? Which of those errors is normal and should not be logged by the transport?

## hid.destroy-device: Destroying a device

- section: Device lifetime in a transport
- relevance: 5 - leaks and use-after-free on unplug

When is the memory of a `struct hid_device` actually freed and by which function, and what can
still hold a reference after `hid_destroy_device()` returns? Start from `hiddev_free()`.

## hid.ll-teardown-order: Transport teardown order

- section: Device lifetime in a transport
- relevance: 4 - in-flight I/O against a device that is going away

On disconnect, in what order must a transport stop its own I/O, call `hid_destroy_device()` and
free its private data, and what does the core guarantee about transport callbacks once
`hid_destroy_device()` has returned? Start from `usbhid_disconnect()` and
`i2c_hid_core_remove()`.

## hid.ll-free-usage: Freeing a transport's device

- section: Device lifetime in a transport
- relevance: 4 - the structure embeds a refcounted device

What are the requirements for a transport driver that releases a `struct hid_device` it got from
`hid_allocate_device()`, after a failed `hid_add_device()` and on removal, in order to assure safe
usage? Name an in-tree transport that shows it.

# Probe and start

## hid.generic-match: Generic and specific drivers

- section: Probe and start
- relevance: 4 - explains why the generic driver does or does not bind

How does `hid_generic_match()` decide to leave a device to a specific driver? Does a specific
driver need an entry in `hid_have_special_driver` in `drivers/hid/hid-quirks.c` in order to bind?
What does the core do with a device bound to the generic driver when a specific driver registers
later? Start from `hid_check_device_match()` and `hid_generic_match()`.

## hid.generic-forced-bind: Forcing the generic driver

- section: Probe and start
- relevance: 4 - explains why a specific driver does not bind

What makes `hid_generic_match()` claim a device that a specific driver also matches, and what does
`hid_check_device_match()` then return for the specific driver? Start from
`hid_check_device_match()` and `hid_generic_match()`.

## hid.probe-sequence: Core work around probe

- section: Probe and start
- relevance: 5 - what a probe callback may assume

What has the core done, and which lock does it hold, by the time it calls the `probe` of a driver?
What does the core do when the driver has no `probe`, and from which point does it deliver
incoming reports to the driver? Start from `hid_device_probe()` and `__hid_device_probe()`.

## hid.devres-group: Devres in device drivers

- section: Probe and start
- relevance: 4 - what devm on the HID device is tied to

What lifetime do `devm_` allocations made against `&hdev->dev` have in a HID device driver:
during probe, after probe has returned, and across an unbind and rebind? What happens to them if
they are made against the parent device instead?

## hid.parse-call: Parsing in probe

- section: Probe and start
- relevance: 4 - the first call in nearly every probe

What state must the device be in for `hid_parse()`, may it be called twice, and what does it
leave behind on failure? Start from `hid_open_report()`.

## hid.connect-mask: Connect mask

- section: Probe and start
- relevance: 4 - decides which device nodes appear

How do quirks and the bus type change the connect mask inside `hid_connect()`, and when does
`hid_connect()` fail because nothing claimed the device? What do `HID_CONNECT_DRIVER` and
`HID_CONNECT_HIDINPUT_FORCE` each change?

## hid.hw-start: Starting the hardware

- section: Probe and start
- relevance: 5 - after it succeeds the driver is visible to user space

What does `hid_hw_start()` undo itself when it fails, what does a connect mask of zero mean, and
what obligation does a successful return place on the driver?

## hid.io-start-stop: Input lock during probe

- section: Probe and start
- relevance: 4 - a driver that talks to the device in probe needs it

Who holds `driver_input_lock` during probe and remove, and what does the core do with a report
that arrives while it is held? What undoes `hid_device_io_start()` when probe then fails or the
hardware is stopped?

## hid.hw-open-close: Opening from a driver

- section: Probe and start
- relevance: 4 - without an opener some transports deliver nothing

When must a device driver call `hid_hw_open()` itself, what happens to incoming reports on the
USB and I2C transports while nobody has the device open, and what must balance the call? Name a
driver that opens the device in probe.

## hid.probe-failure: Probe failure cleanup

- section: Probe and start
- relevance: 5 - decides which error paths leak

When the `probe` of a driver returns an error, what does `__hid_device_probe()` undo by itself,
and what must the driver have undone before it returns?

## hid.probe-visibility: Callbacks during probe

- section: Probe and start
- relevance: 5 - callbacks run before probe has finished

Once `hid_hw_start()` has returned inside probe, which driver callbacks and which user-space
requests can already run, and which are still held off and by what? What are the requirements for
the private data of a driver at the time the driver calls `hid_hw_start()`, in order to assure
safe usage?

# Stop, remove and teardown

## hid.remove-sequence: Core work around remove

- section: Stop, remove and teardown
- relevance: 5 - the order decides what is freed while still in use

What does `hid_device_remove()` do when the driver has no `remove` callback, when are devres
resources released relative to the callback, and what does it hold meanwhile that keeps input
reports away from the driver?

## hid.hw-stop: Stopping the hardware

- section: Stop, remove and teardown
- relevance: 4 - the mirror of start, with one extra step

What does `hid_hw_stop()` do about the input lock and about the listeners, and in what order? Is
it safe to call when `hid_hw_start()` failed or was never called?

## hid.remove-usage: Stopping hardware in remove

- section: Stop, remove and teardown
- relevance: 5 - a missing stop leaves listeners pointing at freed data

What are the requirements for the `remove` callback of a driver with respect to `hid_hw_stop()`,
in order to assure safe usage? Name in-tree drivers that show it.

## hid.devres-stop-usage: Stopping hardware from devres

- section: Stop, remove and teardown
- relevance: 3 - interacts with the core's default remove

What are the requirements for a driver that registers a devres action that calls `hid_hw_stop()`,
in order to assure safe usage? Name in-tree code that shows it.

## hid.async-teardown-usage: Timers and work at teardown

- section: Stop, remove and teardown
- relevance: 5 - the commonest use-after-free in device drivers

What are the requirements for the order in which a driver stops its own deferred work, unregisters
the class devices it registered and calls `hid_hw_stop()`, at remove and on the probe error path,
in order to assure safe usage? Name in-tree code that shows it.

# The input path and event callbacks

## hid.ll-input-report: Feeding input reports

- section: The input path and event callbacks
- relevance: 5 - the size the core trusts decides whether it reads past the buffer

What is the difference between `hid_input_report()` and `hid_safe_input_report()` in the sizes
each passes down, and what does `hid_report_raw_event()` check and do when the data is shorter
than the report the descriptor declares? What must a transport know about its buffer in order to
call `hid_safe_input_report()`?

## hid.ll-input-context: Input path context and errors

- section: The input path and event callbacks
- relevance: 4 - called from interrupt handlers

In which contexts may a transport call `hid_input_report()`, which lock does the function take and
how, and what does it return when no driver is bound, when a probe or remove is in progress, and
when the report id is unknown? Start from `__hid_input_report()`.

## hid.input-path: Path of an input report

- section: The input path and event callbacks
- relevance: 5 - the order decides what each hook sees

In what order does an input report reach HID-BPF, the driver's `raw_event`, the size check,
hiddev and hidraw, field parsing, the driver's `event` and `report`, and the input layer? Which
steps are skipped when only hidraw has claimed the device, and how do `report_table` and
`usage_table` filter? Start from `hid_input_report()`.

## hid.callback-context: Context of event callbacks

- section: The input path and event callbacks
- relevance: 5 - sleeping in them works on one transport and crashes on another

In which contexts may the core call the `raw_event`, `event` and `report` callbacks of a driver,
and which locks does the core hold when it calls them? What may a driver that must work on every
transport do in these callbacks? Name the transport that shows the most restrictive context.

## hid.event-callback-returns: Event callback return values

- section: The input path and event callbacks
- relevance: 4 - decides whether the core goes on to parse the report and the input layer sees it

What does the core do for a negative, zero and positive return from a driver's `raw_event`, and
from its `event` callback, and what is logged? May `raw_event` modify the data it is given?
Compare the code in `__hid_input_report()` and `hid_process_event()` with the comment above
`struct hid_driver`.

## hid.raw-event-size-usage: Indexing raw event data

- section: The input path and event callbacks
- relevance: 5 - the device chooses the length

What does the core guarantee about `size` and about the bytes of `data` when it calls `raw_event`,
and what must the driver check before it indexes `data`? Is a report that is shorter than the
descriptor declares dealt with before or after `raw_event` runs, and how?

# Sending reports

## hid.request-kinds: Request, raw request, output report

- section: Sending reports
- relevance: 4 - picking the wrong one changes the channel and the blocking

Which of `hid_hw_request()`, `hid_hw_raw_request()` and `hid_hw_output_report()` is used when:
which channel does each use, does it wait for the device, and what does each return or do when
the transport lacks the matching callback?

## hid.report-id-byte: Report id byte

- section: Sending reports
- relevance: 4 - off-by-one in every buffer a driver builds

When does a report buffer start with a report id byte: for numbered and unnumbered reports on
the input path, in the buffer passed to `hid_hw_raw_request()`, and in the length
`hid_report_len()` returns? Start from `hid_get_report()` and `__hid_request()`.

## hid.requests-from-callbacks: Requests from event callbacks

- section: Sending reports
- relevance: 4 - the usual reason for a work item in a driver

Which of `hid_hw_request()`, `hid_hw_raw_request()` and `hid_hw_output_report()` may sleep on the
USB transport? What are the requirements for calling each of them from the `raw_event` or `event`
callback of a driver, in order to assure safe usage? Name in-tree code that shows it.

## hid.raw-request-buffer-usage: Request buffers

- section: Sending reports
- relevance: 5 - works on one transport, corrupts memory on another

What are the requirements for buffers passed into `hid_hw_raw_request()` or
`hid_hw_output_report()` in order to assure safe usage? What lengths does the core reject before
the transport sees them?

# Report descriptors and fixups

## hid.rdesc-copies: Report descriptor copies

- section: Report descriptors and fixups
- relevance: 4 - three pointers with three owners

How many copies of the report descriptor does a `struct hid_device` point at and who owns each,
when may two of the pointers be equal, and where is each freed? Start from `hid_parse_report()`,
`hid_open_report()` and `hid_close_report()`.

## hid.report-fixup-contract: Fixup contract

- section: Report descriptors and fixups
- relevance: 5 - ownership of the returned pointer

May the `report_fixup` of a driver modify the buffer the core passes it, and what are the
requirements for the pointer it returns? What does the core do with the returned pointer? Start
from `hid_open_report()`.

## hid.fixup-size-usage: Descriptor size in a fixup

- section: Report descriptors and fixups
- relevance: 4 - the device chooses the descriptor length

What does the core guarantee about the size and the bytes of the descriptor when it calls the
`report_fixup` of a driver, and what must the driver check before it indexes the descriptor? How
does the driver report a changed length?

## hid.report-fixup-alloc-usage: Allocating in a fixup

- section: Report descriptors and fixups
- relevance: 4 - a leak on every probe failure

What are the requirements for the lifetime of a replacement descriptor that the `report_fixup` of
a driver returns in allocated memory, in order to assure safe usage? Name an in-tree driver that
returns an allocated descriptor and say where it frees it.

# Trusting the device and the descriptor

## hid.device-struct: Ownership of device fields

- section: Trusting the device and the descriptor
- relevance: 4 - most driver code reads these fields

Which members of `struct hid_device` does the transport own and which does the bound device driver
own, among the private data pointers, `quirks` and `claimed`? What are the requirements for a
device driver that reads or writes a member the transport owns, in order to assure safe usage?

## hid.field-arrays: Field array sizes

- section: Trusting the device and the descriptor
- relevance: 4 - decides which index checks are enough

How many entries do the `usage`, `value` and `new_value` arrays of a `struct hid_field` have,
relative to the field's report count and the number of usages the descriptor declared? Start
from `hid_add_field()` and `hid_register_field()`.

## hid.validate-values: hid_validate_values checks

- section: Trusting the device and the descriptor
- relevance: 4 - the helper checks less than its name suggests

What exactly does `hid_validate_values()` check and return, what does an id of zero mean to it,
and what does it not check that a driver still must?

## hid.field-index-usage: Indexing fields

- section: Trusting the device and the descriptor
- relevance: 5 - malicious and fuzzed descriptors reach every driver

What are the requirements for code that indexes `report->field[]`, or that uses a report it found
through `report_id_hash[]` or `report_list`, in order to assure safe usage? What does the core
guarantee about a report it hands to a callback?

## hid.usage-index-usage: Indexing usages and values

- section: Trusting the device and the descriptor
- relevance: 4 - out-of-bounds access chosen by the device

What are the requirements for an index into `field->usage[]` and for an index into
`field->value[]`, in order to assure safe usage, and which member of `struct hid_field` bounds
each? Does `hid_set_field()` check its offset?

## hid.inputs-list-usage: Inputs list and hidinput pointers

- section: Trusting the device and the descriptor
- relevance: 5 - a recurring crash with descriptors that map no input

What are the requirements for code that reads `hdev->inputs`, `field->hidinput` or a `struct
hid_input` it saved in `input_configured`, after `hid_hw_start()` has succeeded, in order to
assure safe usage? Can `hid_hw_start()` succeed with no input device registered?

## hid.hid-is-usb: USB transport test

- section: Trusting the device and the descriptor
- relevance: 3 - where it is defined decides what a driver must depend on

What exactly does `hid_is_usb()` test, in which module is it defined, and what does that mean
for the Kconfig dependencies of a driver that calls it?

## hid.usb-parent-usage: Parent as a USB interface

- section: Trusting the device and the descriptor
- relevance: 5 - a device from uhid or another transport crashes the driver

What are the requirements for a driver that uses `hdev->dev.parent` as a USB interface, for
example through `to_usb_interface()` or `hid_to_usb_dev()`, in order to assure safe usage, for a
driver that supports only USB and for one that supports several transports? Can a device that did
not come from the USB transport have `BUS_USB` as its bus type, and how?

# The input bridge and hidraw

## hid.input-mapping-returns: Mapping callback returns

- section: The input bridge and hidraw
- relevance: 5 - three-way return that reviewers misread

What does the core do for a negative, zero and positive return from `input_mapping`, and from
`input_mapped`? What state must the driver leave in the usage and the bit pointer for a positive
return to have an effect? Start from `hidinput_configure_usage()`.

## hid.input-splitting: Input splitting quirks

- section: The input bridge and hidraw
- relevance: 4 - the wrong quirk splits or merges device nodes

What do `HID_QUIRK_MULTI_INPUT` and `HID_QUIRK_INPUT_PER_APP` each make `hidinput_connect()` split
by, and which wins when both are set? Which applications share one input device in spite of
`HID_QUIRK_INPUT_PER_APP`?

## hid.hidinput-connect: Connecting the input layer

- section: The input bridge and hidraw
- relevance: 4 - where input devices come from

When does `hidinput_connect()` decline to create any input device, how does it treat an input
device that ended up with no capabilities, and what does it unwind when a driver callback made
during it fails?

## hid.hidraw-lifetime: hidraw device lifetime

- section: The input bridge and hidraw
- relevance: 4 - files stay open across unplug

What keeps a `struct hidraw` alive while files are open across an unplug, and what do `exist`
and `open` mean to `drop_ref()`? What stops an open file from using the `struct hid_device`
after disconnect, and under which lock?

# Quirks

## hid.quirk-tables: Quirk tables and lookup

- section: Quirks
- relevance: 4 - where a device-specific workaround goes

In what order does `hid_lookup_quirk()` consult the static tables, the dynamic quirks and the
initial quirks of the transport, and does a later source add to an earlier one or replace it? What
does an entry in `hid_ignore_list` do that an entry in the quirk table of
`drivers/hid/hid-quirks.c` does not?

## hid.quirks-reset: Quirks set by a driver

- section: Quirks
- relevance: 3 - a quirk set at the wrong time is silently lost or sticks

When is `hdev->quirks` recomputed, and so where must a device driver that wants to add a quirk
set it, relative to `hid_parse()` and `hid_hw_start()`? Start from `hid_lookup_quirk()` and its
callers.

# HID-BPF

## hid.bpf-attach: Attaching programs

- section: HID-BPF
- relevance: 4 - the attach mechanism has been replaced once already

Through which BPF program type or map type is a HID-BPF program attached to a device in this tree,
and how does the program name the device? What does `hid_bpf_reg()` refuse?

## hid.bpf-device-lifetime: Programs and device lifetime

- section: HID-BPF
- relevance: 4 - attaching a program can reconnect the device, and the device can go away under a program

What does the core do to the device when a HID-BPF program that changes the report descriptor is
attached or detached, and what does it do with the attached programs when the device goes away?
Start from `hid_bpf_reconnect()` and `hid_bpf_destroy_device()`.

## hid.bpf-hooks: HID-BPF hooks

- section: HID-BPF
- relevance: 4 - each hook has its own return convention and context

A table of the hooks in `struct hid_bpf_ops`, to choose between: where in the core each is
called from, what its return value means, whether it may sleep, and how many programs per device
each allows.

# Core locks and other users

## hid.locks: Locks in the core

- section: Core locks and other users
- relevance: 4 - several are taken from interrupt context

Which of the locks in the HID core, hid-input, hidraw and HID-BPF are taken from interrupt
context, which paths sleep on `driver_input_lock`, and in what order do the ones that nest nest?

## hid.core-change-checklist: Changing the core

- section: Core locks and other users
- relevance: 4 - a core change touches every transport and driver

Which search finds every `struct hid_ll_driver` in the tree, those outside `drivers/hid/`
included? What does HID-BPF require of the functions of the HID core that it calls through `struct
hid_ops` in `include/linux/hid_bpf.h`? Which KUnit suites and which selftests under
`tools/testing/selftests/hid/` feed the core malformed descriptors?

# Model gaps

## hid.model-gaps: Other mistakes models make

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
