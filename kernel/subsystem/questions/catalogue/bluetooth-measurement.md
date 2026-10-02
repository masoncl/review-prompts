# Questions: Bluetooth (measurement set)

- guide: bluetooth.md
- title: Bluetooth Subsystem

A wide set of questions about the Bluetooth core under `net/bluetooth/` (the
HCI device, the queue of synchronous commands, event handling, connections,
advertising, the management interface, L2CAP and the sockets above it), used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 672 words.
Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## bt.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold the HCI device core, the queue of synchronous command
sequences, event handling, connection objects, the HCI sockets, the management
interface and its helpers, L2CAP and its sockets, SMP, SCO, ISO, the vendor
extensions, the self tests and the public headers? A table. Start from
`net/bluetooth/` and `include/net/bluetooth/`.

## bt.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

For each job (a driver hands over a received frame, an event packet is
dispatched, a management command arrives from user space, a sequence of HCI
commands is queued, an ACL data packet reaches L2CAP, a controller is powered
on), which function do you start reading from? A table.

## bt.docs-tests: Documentation and tests

- section: Finding your way
- relevance: 2 - saves looking for what is not there
- words: 60

What documentation of the Bluetooth core and of the management interface is in
the kernel tree, and what tests of it are in the tree? Start from
`net/bluetooth/selftest.c` and `drivers/bluetooth/hci_vhci.c`.

# The HCI device

## bt.hdev-lifecycle: Controller registration and teardown

- section: The controller object
- relevance: 4 - the order of teardown is what use-after-free fixes keep changing
- words: 110

How is a `struct hci_dev` allocated, registered and first powered on, and in
what order does `hci_unregister_dev()` stop work items, clear queued command
sequences, close the device and tell the management interface? Where is the
memory finally freed?

## bt.hdev-flag-sets: Flag words and quirks

- section: The controller object
- relevance: 4 - three bit sets with three sets of accessors, and one of them was renamed
- words: 90

Which separate sets of flag bits does `struct hci_dev` carry, which accessor is
used for each, which of them are visible to user space, and how does a driver
set a quirk in this tree? Start from `include/net/bluetooth/hci.h` and
`hci_dev_test_flag()`.

## bt.hdev-locks: Controller locks

- section: The controller object
- relevance: 5 - which lock covers what decides most races here
- words: 120

Give a table of the locks in or around `struct hci_dev` (the device lock, the
request lock, the locks of the command queue, the unregister lock, the pending
management command lock, the device list lock, the callback list lock): the
type of each, what it protects, and the order in which they nest.

## bt.workqueues: Work queues and work items

- section: The controller object
- relevance: 3 - what runs where decides what may sleep and what is serialised
- words: 90

Which work queues does a controller have, how are they created, and which of
the receive, command, transmit, power-on and queued-command work items runs on
which? What follows from that about two event handlers, or two queued command
sequences, running at once?

## bt.driver-frames: Driver callbacks and frame ownership

- section: The controller object
- relevance: 4 - a double free or a leak in every driver that gets it wrong
- words: 90

Which callbacks must a driver fill in before registering, who frees the skb
when the driver's send callback returns an error and when it returns success,
who owns an skb passed to `hci_recv_frame()`, and which packet types does
`hci_recv_frame()` accept? Start from `hci_send_frame()`.

# Queued command sequences

## bt.cmd-sync-api: Queueing interface

- section: The command queue
- relevance: 5 - the variants differ in when they refuse and whether they run inline
- words: 120

Give a table of the functions that queue or run a callback on the synchronous
command queue (submit, queue, queue once, run, run once, look up, dequeue):
what state the device must be in, what each returns on refusal, and which may
call the callback directly instead of queueing it. Start from
`hci_cmd_sync_submit()`.

## bt.cmd-sync-destroy: Completion callback contract

- section: The command queue
- relevance: 5 - the callback frees the data, so every path must reach it exactly once
- words: 90

When is the destroy callback given to the queueing functions called, with which
error values, holding which locks, and is it called when the entry is dequeued
or the queue is cleared before it ran? What must the caller do with its data
when the queueing call itself fails?

## bt.cmd-sync-return: Return values of synchronous sends

- section: The command queue
- relevance: 4 - callers test the wrong sign or miss the no-data case
- words: 80

What do `__hci_cmd_sync()`, `__hci_cmd_sync_sk()`, `__hci_cmd_sync_status()`
and `hci_cmd_sync_status()` return on success, on a controller error status,
on timeout, on cancellation and when the reply carries no parameters? Which of
them take the request lock themselves?

## bt.cmd-sync-lock-usage: Device lock around synchronous functions

- section: The command queue
- relevance: 5 - a deadlock nothing in the diff shows
- words: 80

What usage of the device lock around functions that send a command and wait
for its reply is unsafe, and why? What do correct queued callbacks do when they
need device state under that lock? Name in-tree code that shows it. Start from
the comment in `include/net/bluetooth/hci_sync.h`.

## bt.cmd-sync-data-usage: Object pointers as callback data

- section: The command queue
- relevance: 5 - the recurring use-after-free class in this code
- words: 100

A queued callback is given a pointer to a connection or to a pending management
command as its data. What usage of that pointer when the callback finally runs
is unsafe, and what do correct callbacks and the code that frees those objects
do about it? Start from `hci_conn_valid()`, `hci_conn_del()` and
`hci_cmd_sync_dequeue()`.

# Events

## bt.event-dispatch: Event dispatch tables

- section: Event handling
- relevance: 4 - where a new event or a length check goes
- words: 100

How are events, command complete replies, command status replies and LE meta
events each dispatched to a handler, what lengths does a table entry declare,
what happens when a packet is shorter or longer than declared, and what has
already been pulled from the skb when the handler runs? Start from
`hci_event_func()`.

## bt.event-parse-usage: Parsing variable-length events

- section: Event handling
- relevance: 5 - the controller is not trusted and the reports are counted arrays
- words: 80

What usage of the fields of an event that carries a counted array or a trailing
data block is unsafe, and what do correct handlers do before touching each
element? Name in-tree handlers that show it. Start from
`hci_le_ext_adv_report_evt()` and `hci_num_comp_pkts_evt()`.

## bt.event-conn-lookup: Connection lookup in handlers

- section: Event handling
- relevance: 4 - the lookup and the use have to be under the same lock
- words: 70

How do event handlers find the connection for a handle or an address, what
protects the list they walk, and what must a handler hold from the lookup until
it has finished using the connection? Start from
`hci_conn_hash_lookup_handle()`.

# Connections

## bt.conn-refs: Connection reference counts

- section: Connection objects
- relevance: 5 - two counters with different meanings, often confused
- words: 90

What do `hci_conn_get()` and `hci_conn_put()` count, what do `hci_conn_hold()`
and `hci_conn_drop()` count, what happens when the second reaches zero, and
which of them keeps the memory valid? Start from the comment above them in
`include/net/bluetooth/hci_core.h`.

## bt.conn-lifecycle: Connection creation and deletion

- section: Connection objects
- relevance: 5 - what deletion cancels and unlinks decides what may still run afterwards
- words: 110

How is a `struct hci_conn` created before the controller has assigned a handle,
how does it get its handle, which lock must be held to add and delete one, and
what does `hci_conn_del()` cancel, unlink and dequeue, in what order?

## bt.conn-types: Link types

- section: Connection objects
- relevance: 3 - the isochronous types were split and old names are gone
- words: 60

Which link types can `conn->type` hold in this tree, which per-type counters
does the connection hash keep, and which types share a controller buffer pool
for flow control?

## bt.conn-abort: Aborting a connection

- section: Connection objects
- relevance: 4 - the right action depends on the state, and it may run inline
- words: 80

How does `hci_abort_conn()` stop a connection: what does it do for a connection
whose create command is still queued, which HCI command is used for each state,
when is the object deleted directly, and how is a second abort of the same
connection handled?

## bt.conn-proto-data: Protocol data and callbacks

- section: Connection objects
- relevance: 4 - the upper layers hang their state here and are told of teardown here
- words: 90

Where do L2CAP, SCO and ISO keep their per-connection state on a
`struct hci_conn`, what protects each of those pointers, and how are the upper
layers told that a connection completed, was disconnected or changed security?
Start from `struct hci_cb`.

# Advertising

## bt.adv-instances: Advertising instance tracking

- section: Advertising
- relevance: 5 - the list does not hold every instance, and instance is not handle
- words: 100

How are advertising instances tracked: which list, which numbers are accepted
by `hci_add_adv_instance()`, how does an entry's instance number relate to the
handle sent to the controller, and how is instance zero represented?

## bt.adv-state-usage: Testing whether advertising is on

- section: Advertising
- relevance: 5 - the wrong indicator breaks pause and resume silently
- words: 100

Code that must know whether one particular advertising instance is enabled in
the controller has `hdev->cur_adv_instance`, the `HCI_LE_ADV` flag and the
per-instance state to choose from. What does each record, which usage of them
for that purpose is unsafe, and which is correct for a listed instance and for
instance zero? Start from `hci_cc_le_set_ext_adv_enable()`.

## bt.adv-pause-resume: Pausing and resuming advertising

- section: Advertising
- relevance: 3 - the consumer of the per-instance state
- words: 70

What do `hci_pause_advertising_sync()` and `hci_resume_advertising_sync()` do
with extended and with legacy advertising, which state do they rely on to know
what to re-enable, and what happens, in the controller and in
`hdev->adv_instances`, to an instance that fails to resume? Follow any command
they send through to the handler of its reply.

# The management interface

## bt.mgmt-handler-table: Command table and length checks

- section: Management commands
- relevance: 4 - the length a handler may assume comes from its table entry
- words: 90

How is a management command routed to its handler, what does a table entry
declare, which flags can it carry and what does each mean, and which length and
index checks have been done before the handler runs? Start from
`hci_mgmt_cmd()` and `mgmt_handlers`.

## bt.mgmt-varlen-usage: Counted arrays from user space

- section: Management commands
- relevance: 4 - the table only guarantees the fixed part
- words: 70

For a management command whose parameters end in a counted array, what usage of
the count and the elements is unsafe, and what check do correct handlers make
first? Name in-tree handlers that show it.

## bt.mgmt-pending-api: Pending command helpers

- section: Pending management commands
- relevance: 5 - each helper differs in list membership, locking and who frees
- words: 120

Give a table of the helpers for `struct mgmt_pending_cmd` (new, add, free,
remove, find, foreach, listed, valid): whether each puts the command on or takes
it off the device's pending list, which lock it takes or expects, and whether it
frees the command. Start from `net/bluetooth/mgmt_util.c`.

## bt.mgmt-pending-complete-usage: Ownership in completion callbacks

- section: Pending management commands
- relevance: 5 - leaks and double frees that every new command can repeat
- words: 110

In the completion callback of a queued management command, what usage of the
pending command is unsafe (on cancellation, after checking that it is still
pending, on error returns), and what do correct callbacks do on every path?
Does it differ for a command that was never put on the pending list? Name
in-tree callbacks of both kinds.

## bt.mgmt-pending-sync-usage: Pending commands in queued functions

- section: Pending management commands
- relevance: 4 - the command can be freed between queueing and running
- words: 80

In the function queued to run a management command, what usage of the pending
command's parameters is unsafe, and what do correct functions do before reading
them? Name in-tree code that shows it. Start from `set_powered_sync()`.

## bt.mgmt-flex-usage: Variable-length parameters on the stack

- section: Pending management commands
- relevance: 4 - sizeof leaves out the flexible array
- words: 80

What usage of a stack copy of a management command structure that ends in a
flexible array is unsafe, and how does correct in-tree code size and fill such
a copy? Which management command structures have a flexible array member?
Start from `include/net/bluetooth/mgmt.h`.

# L2CAP and sockets

## bt.l2cap-locks: L2CAP connection and channel locks

- section: L2CAP
- relevance: 4 - the locks here changed type and order more than once
- words: 100

Which locks protect a `struct l2cap_conn`, its channel list and a
`struct l2cap_chan`, what type is each, in what order do they nest with each
other, with the device lock and with the socket lock, and what do the channel
lookup helpers return holding?

## bt.l2cap-chan-refs: Channel references and timers

- section: L2CAP
- relevance: 4 - a timer that fires after the last put is a use-after-free
- words: 80

How is a `struct l2cap_chan` reference counted, when must a lookup use the form
that fails on zero, and how do the channel timers take and drop references when
they are set, cleared and when they fire? Start from `l2cap_set_timer()`.

## bt.l2cap-rx-usage: Parsing received L2CAP frames

- section: L2CAP
- relevance: 4 - remote input, and the signalling commands are variable length
- words: 80

What usage of the length fields of a received signalling command or data frame
is unsafe, and what do correct handlers check first? How are fragments of one
frame reassembled and what resets a bad reassembly? Start from
`l2cap_sig_channel()` and `l2cap_recv_acldata()`.

## bt.sock-conn-link: Sockets over SCO and ISO connections

- section: Sockets
- relevance: 3 - the socket and the connection can each go away first
- words: 80

How do `struct sco_conn` and `struct iso_conn` tie a socket to a
`struct hci_conn`: what lock and reference count does each have, and what usage
of `conn->sk` or of the connection from the socket side is unsafe without them?

## bt.hci-sock-channels: HCI socket channels

- section: Sockets
- relevance: 3 - each channel has its own privileges and its own view of the device
- words: 80

Which channels can an HCI socket be bound to, what is each for, what does the
user channel do to the rest of the stack's use of that controller, and how does
socket code get from a socket to a controller that may be unregistering? Start
from `net/bluetooth/hci_sock.c`.

# Changing the implementation

## bt.change-checklist: Changing core code

- section: What a change must preserve
- relevance: 3 - the interface has users and tests outside the tree
- words: 80

What must a change to the management interface or to the event and command
handling keep working besides the code itself: the wire format of commands and
events, the monitor channel, the virtual controller, tests that live outside
the kernel tree?
