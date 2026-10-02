# Questions: Bluetooth Subsystem

- guide: bluetooth.md
- title: Bluetooth Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/bluetooth-measurement.md` is the
wider set the readers were measured on and `catalogue/bluetooth-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## bt.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## bt.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the HCI device core; the queue of synchronous command
sequences; event handling; connection objects; the HCI sockets; the management interface and its
helpers; L2CAP and its sockets; SMP; SCO; ISO; the vendor extensions; the self tests; the public
headers. Where a reader is likely to look for something in a file that does not hold it, say so
in the row. Start from `net/bluetooth/` and `include/net/bluetooth/`.

# The controller object

## bt.hdev-flag-sets: Flag words and quirks

- section: The controller object
- relevance: 4 - three bit sets with three sets of accessors, and one of them was renamed

Which accessors go with each set of flag bits in `struct hci_dev`, and which set does user space
see? What checks that a bit passed to an accessor belongs to the set of that accessor? Start from
`include/net/bluetooth/hci.h` and `hci_dev_test_flag()`.

## bt.hdev-quirks: Driver quirks

- section: The controller object
- relevance: 4 - a driver patch has to set a quirk in the way that this tree provides

How does a driver set a quirk of a `struct hci_dev`, and how does the core test one? Start from
`include/net/bluetooth/hci_core.h`.

## bt.hdev-locks: Controller locks

- section: The controller object
- relevance: 5 - which lock covers what decides most races here

What does each lock of `struct hci_dev` protect, and what do `hci_dev_list_lock` and
`hci_cb_list_lock` protect? In what order do these locks nest?

## bt.hdev-lifecycle: Controller registration and teardown

- section: The controller object
- relevance: 4 - the order of teardown is what use-after-free fixes keep changing

In what order does `hci_unregister_dev()` do its steps, and what does each step require the
earlier steps to have done? Where is the `struct hci_dev` freed, and on what condition?

## bt.hdev-work-stop: Stopping controller work items

- section: The controller object
- relevance: 4 - work that is queued again after it was stopped runs on a controller that is going away

With which calls does `hci_unregister_dev()` stop the work items of a `struct hci_dev`, and what
do those calls guarantee about a later attempt to queue the same work?

## bt.driver-frames: Driver callbacks and frame ownership

- section: The controller object
- relevance: 4 - a double free or a leak in every driver that gets it wrong

Who frees the skb after the driver's `send` callback returns an error, and who after it returns
success? Who owns an skb passed to `hci_recv_frame()` once that function returns, for each value
that it can return? What does `hci_recv_frame()` do with a packet type that it does not accept?
Start from `hci_send_frame()`.

# Synchronous command queue

## bt.cmd-sync-api: Queueing interface

- section: Synchronous command queue
- relevance: 5 - the variants differ in when they refuse and whether they run inline

For each of `hci_cmd_sync_submit()`, `hci_cmd_sync_queue()`, `hci_cmd_sync_queue_once()`,
`hci_cmd_sync_run()` and `hci_cmd_sync_run_once()`: in which state of the device does it refuse
and what does it return then, what does it return when a matching entry is already queued, and may
it call the callback directly? Start from `hci_cmd_sync_submit()`.

## bt.cmd-sync-dequeue: Removing queued entries

- section: Synchronous command queue
- relevance: 5 - an entry that stays queued runs later, with data that may be gone by then

What do `hci_cmd_sync_lookup_entry()` and `hci_cmd_sync_dequeue()` match an entry on, and which
lock does each take or expect? How is a queued entry that creates a connection cancelled? Start
from `hci_cmd_sync_dequeue()`.

## bt.cmd-sync-destroy: Completion callback contract

- section: Synchronous command queue
- relevance: 5 - the callback frees the data, so every path must reach it exactly once

With which error value is the `destroy` callback given to a function that queues or runs a
callback on the synchronous command queue, such as `hci_cmd_sync_queue()`, called on each path
that ends an entry, and which locks are held then? What must the caller do with its data on a path
that does not call `destroy`?

## bt.cmd-sync-return: Return values of synchronous sends

- section: Synchronous command queue
- relevance: 4 - callers test the wrong sign or miss the no-data case

What do `__hci_cmd_sync()`, `__hci_cmd_sync_sk()`, `__hci_cmd_sync_status()` and
`hci_cmd_sync_status()` return on success, on a controller error status, on timeout, on
cancellation and when the reply carries no parameters? Which of them take the request lock
themselves?

## bt.cmd-sync-lock-usage: Device lock around synchronous functions

- section: Synchronous command queue
- relevance: 5 - a deadlock nothing in the diff shows

What are the requirements for holding the device lock, taken with `hci_dev_lock()`, around
`__hci_cmd_sync()` and the other functions that send a command and wait for its reply, in order to
assure safe usage? How do callbacks queued with `hci_cmd_sync_queue()` read device state that the
device lock protects? Name in-tree code that shows it. Start from the comment in
`include/net/bluetooth/hci_sync.h`.

## bt.cmd-sync-data-usage: Object pointers as callback data

- section: Synchronous command queue
- relevance: 5 - the recurring use-after-free class in this code

What are the requirements for a callback queued on the synchronous command queue that is given a
`struct hci_conn` or a `struct mgmt_pending_cmd` as its data, in order to assure safe usage of
that pointer when the callback runs? What does the code that frees those objects do about entries
that are still queued? Start from `hci_conn_valid()`, `hci_conn_del()` and
`hci_cmd_sync_dequeue()`.

# Connection objects

## bt.conn-lifecycle: Connection creation and deletion

- section: Connection objects
- relevance: 5 - what deletion cancels and unlinks decides what may still run afterwards

What identifies a `struct hci_conn` before the controller has assigned a handle? Which lock must
be held to add one and to delete one? What does `hci_conn_del()` guarantee, when it returns, about
what may still run for the `struct hci_conn` and what may still point to it?

## bt.conn-handle: Handle assignment

- section: Connection objects
- relevance: 5 - the handle comes from the controller, which is not trusted

What does `hci_conn_set_handle()` check before it gives a `struct hci_conn` the handle that the
controller assigned, and what does it return when a check fails?

## bt.conn-refs: Connection reference counts

- section: Connection objects
- relevance: 5 - two counters with different meanings, often confused

What does a reference taken with `hci_conn_get()` guarantee, and what does one taken with
`hci_conn_hold()` guarantee? What happens when `hci_conn_drop()` releases the last hold? Which of
`hci_conn_put()` and `hci_conn_drop()` is the release when queueing work on a connection fails?
Start from the comment above them in `include/net/bluetooth/hci_core.h`.

## bt.conn-abort: Aborting a connection

- section: Connection objects
- relevance: 4 - the right action depends on the state, and it may run inline

What does `hci_abort_conn()` do and return for a connection in each state that it distinguishes?
When does it delete the `struct hci_conn` itself? How is a second abort of the same connection
handled?

## bt.conn-proto-data: Protocol data and callbacks

- section: Connection objects
- relevance: 4 - the upper layers hang their state here and are told of teardown here

Which lock protects the pointer under which each of L2CAP, SCO and ISO keeps its per-connection
state on a `struct hci_conn`? How are the upper layers told through `struct hci_cb` that a
connection completed, was disconnected or changed security? What must a socket layer that drops
its own lock to take the device lock check again afterwards? Start from `struct hci_cb`.

# Event handling

## bt.event-dispatch: Event dispatch tables

- section: Event handling
- relevance: 4 - where a new event or a length check goes

When `hci_event_func()` calls an event handler, what has it checked about the length of the packet
against the handler's table entry, and what has it pulled from the skb? Which tables hold the
handlers, and which kind of event or reply goes in each? Start from `hci_event_func()`.

## bt.event-conn-lookup: Connection lookup in handlers

- section: Event handling
- relevance: 4 - the lookup and the use have to be under the same lock

How do event handlers find the connection for a handle or an address, what protects the list
they walk, and what must a handler hold from the lookup until it has finished using the
connection? Start from `hci_conn_hash_lookup_handle()`.

## bt.event-parse-usage: Parsing variable-length events

- section: Event handling
- relevance: 5 - the controller is not trusted and the reports are counted arrays

What are the requirements for reading the elements of an event that carries a counted array or a
trailing data block, in order to assure safe usage? Name in-tree handlers that show it. Start from
`hci_le_ext_adv_report_evt()` and `hci_num_comp_pkts_evt()`.

# Management commands

## bt.mgmt-handler-table: Command table and length checks

- section: Management commands
- relevance: 4 - the length a handler may assume comes from its table entry

When `hci_mgmt_cmd()` calls a management command handler, which length and index checks has it
made, and how do the flags of the handler's entry in `mgmt_handlers` change those checks? What
else must be updated when a command or event is added, so that sockets that are not trusted are
served correctly? Start from `hci_mgmt_cmd()` and `mgmt_handlers`.

## bt.mgmt-pending-api: Pending command helpers

- section: Management commands
- relevance: 5 - each helper differs in list membership, locking and who frees

For each of `mgmt_pending_new()`, `mgmt_pending_add()`, `mgmt_pending_free()`,
`mgmt_pending_remove()`, `mgmt_pending_find()`, `mgmt_pending_foreach()`, `mgmt_pending_listed()`
and `mgmt_pending_valid()`: does it put the command on the device's pending list or take it off,
which lock does it take or expect, and does it free the command? Start from
`net/bluetooth/mgmt_util.c`.

## bt.mgmt-varlen-usage: Counted arrays from user space

- section: Management commands
- relevance: 4 - the table only guarantees the fixed part

For a management command whose parameters end in a counted array, what are the requirements for
reading the count and the elements in order to assure safe usage? Name in-tree handlers that show
it.

## bt.mgmt-flex-usage: Variable-length parameters on the stack

- section: Management commands
- relevance: 4 - sizeof leaves out the flexible array

What are the requirements for a stack copy of a management command structure that ends in a
flexible array, in order to assure safe usage? How does in-tree code size and fill such a copy?
Name two such structures and say how to find the rest. Start from `include/net/bluetooth/mgmt.h`.

## bt.mgmt-pending-complete-usage: Ownership in completion callbacks

- section: Management commands
- relevance: 5 - leaks and double frees that every new command can repeat

In the completion callback of a queued management command, what are the requirements for using and
freeing the `struct mgmt_pending_cmd` in order to assure safe usage? Do the requirements differ
for a command that was never put on the pending list? Name in-tree callbacks of both kinds.

## bt.mgmt-pending-sync-usage: Pending commands in queued functions

- section: Management commands
- relevance: 4 - the command can be freed between queueing and running

In a function queued to run a management command, what are the requirements for reading the
parameters or the socket of the `struct mgmt_pending_cmd` in order to assure safe usage, and which
lock covers the read? Name in-tree code that shows it. Start from `set_powered_sync()`.

# Advertising

## bt.adv-instances: Advertising instance tracking

- section: Advertising
- relevance: 5 - the list does not hold every instance, and instance is not handle

Which instance numbers does `hci_add_adv_instance()` accept, and what does it return for the
others? How does the instance number of an entry in `hdev->adv_instances` relate to the handle
that each command sends to the controller? How is instance zero represented?

## bt.adv-state-usage: Testing whether advertising is on

- section: Advertising
- relevance: 5 - the wrong indicator breaks pause and resume silently

What does each of `hdev->cur_adv_instance`, the `HCI_LE_ADV` flag and the `enabled` member of
`struct adv_info` record? What are the requirements for code that tests whether one advertising
instance is enabled in the controller, for a listed instance and for instance zero, in order to
assure safe usage? Which reply handlers maintain the state for instance zero? Start from
`hci_cc_le_set_ext_adv_enable()`.

## bt.adv-pause-resume: Pausing and resuming advertising

- section: Advertising
- relevance: 3 - the consumer of the per-instance state

Which state do `hci_pause_advertising_sync()` and `hci_resume_advertising_sync()` read to know
which advertising to re-enable, and what does that state mean between a pause and a resume? What
happens, in the controller and in `hdev->adv_instances`, to an instance that fails to resume?
Follow any command they send through to the handler of its reply.

# L2CAP

## bt.l2cap-locks: L2CAP connection and channel locks

- section: L2CAP
- relevance: 4 - the locks here changed type and order more than once

Which locks protect a `struct l2cap_conn`, its channel list and a `struct l2cap_chan`? In what
order do they nest with each other, with the device lock and with the socket lock? What do the
channel lookup helpers, such as `l2cap_get_chan_by_scid()`, return holding?

## bt.l2cap-chan-refs: Channel references and timers

- section: L2CAP
- relevance: 4 - a timer that fires after the last put is a use-after-free

How is a `struct l2cap_chan` reference counted, and when must a lookup take its reference with
`l2cap_chan_hold_unless_zero()`? How do the channel timers take and drop references when they are
set, when they are cleared and when they fire? Start from `l2cap_set_timer()`.

## bt.l2cap-rx-usage: Parsing received L2CAP frames

- section: L2CAP
- relevance: 4 - remote input, and the signalling commands are variable length

What are the requirements for using the length fields of a received signalling command or data
frame in order to assure safe usage? How does `l2cap_recv_acldata()` reassemble the fragments of
one frame, and what does an unexpected start or continuation fragment do to a reassembly in
progress? Start from `l2cap_sig_channel()` and `l2cap_recv_acldata()`.

# Model gaps

## bt.model-gaps: Other mistakes models make

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
