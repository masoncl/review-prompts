# Questions: I2C Subsystem

- guide: i2c.md
- title: I2C Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/i2c-measurement.md` is the wider
set the readers were measured on and `catalogue/i2c-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## i2c.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## i2c.core-files: Core files

- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the core's internal helpers; SMBus alert; SPD handling;
the component prober; the address translator core; the test backends; the definitions of
`struct i2c_msg` and of `struct i2c_device_id`. Leave out a file that is named after its job.
Where a reader is likely to look for a file that does not exist in this tree, say so in the row.
Start from `drivers/i2c/Makefile` and what `include/linux/i2c.h` includes.

# Message buffers and DMA

## i2c.dma-buffer-rule: DMA rule for message buffers

- section: Message buffers and DMA
- relevance: 5 - the rule differs from SPI and USB and is often misquoted

What does this tree require of the buffer of a `struct i2c_msg` as far as DMA is concerned, and
is a stack buffer passed to `i2c_transfer()` or to the ordinary send and receive functions
correct by that rule? If an adapter driver uses DMA and is handed a buffer that is not marked
safe, what in the tree, if anything, makes the transfer safe, and whose job is it? Start from
`Documentation/i2c/dma-considerations.rst`.

## i2c.dma-safe-flag: DMA-safe flag

- section: Message buffers and DMA
- relevance: 5 - a promise made by the caller that nothing checks

What does `I2C_M_DMA_SAFE` on a message assert, and does anything verify it? Which
client-facing functions set it on their caller's behalf, and what does that require of the buffer
they are given?

## i2c.smbus-emulation-buffers: SMBus emulation buffers

- section: Message buffers and DMA
- relevance: 4 - the core's own messages mix stack and heap buffers

When the core emulates an SMBus transaction with I2C messages, where do the message buffers
live, for which transactions are they allocated and marked DMA-safe, and what happens to the
transfer when that allocation fails? Start from `i2c_smbus_xfer_emulated()`.

## i2c.dma-helpers: Bounce buffer helpers

- section: Message buffers and DMA
- relevance: 5 - the contract an adapter driver relies on

When does `i2c_get_dma_safe_msg_buf()` return NULL, when the message's own buffer and when a
fresh allocation, and what must the driver do in each case? What does the last argument of
`i2c_put_dma_safe_msg_buf()` decide, and from which context may each of the two be called?

## i2c.dma-adapter-patterns: DMA in adapter drivers

- section: Message buffers and DMA
- relevance: 5 - decides whether an ordinary buffer is ever mapped for DMA

What does the tree require of an adapter driver under `drivers/i2c/busses/` that maps the buffer
of a `struct i2c_msg` for DMA when the message lacks `I2C_M_DMA_SAFE`? Name an in-tree driver that
shows it.

## i2c.dma-client-usage: DMA-safe variants in client drivers

- section: Message buffers and DMA
- relevance: 5 - the subject of the hand-written guide

What are the requirements for the buffer that a client driver passes to
`i2c_master_send_dmasafe()` or `i2c_master_recv_dmasafe()`, or puts in a message on which it sets
`I2C_M_DMA_SAFE`, in order to assure safe usage? Name in-tree code that shows it.

## i2c.dma-adapter-usage: Helper pairing in adapter drivers

- section: Message buffers and DMA
- relevance: 4 - leaks and lost read data on error paths

What are the requirements for an adapter driver that calls `i2c_get_dma_safe_msg_buf()` and
`i2c_put_dma_safe_msg_buf()` in its transfer path in order to assure safe usage? Name an in-tree
driver that shows it.

# Transfers and SMBus

## i2c.algorithm-callbacks: Algorithm callback names

- section: Transfers and SMBus
- relevance: 4 - the names have been changing and both spellings compile

What does `struct i2c_algorithm` call its callbacks for an I2C transfer, for the atomic variant,
and for registering and unregistering a client the adapter answers to as a target? Does it keep
older spellings of any of these, and if so how, which does the kerneldoc say to use, and which
does the core itself call through?

## i2c.transfer-returns: Transfer return values

- section: Transfers and SMBus
- relevance: 5 - callers compare against the wrong number

What do `i2c_transfer()`, `i2c_master_send()`, `i2c_master_recv()` and the SMBus read and write
helpers such as `i2c_smbus_read_byte_data()` and `i2c_smbus_read_block_data()` each return on
success and on failure? What is an adapter's transfer callback expected to return, and what can
a caller learn about a transfer that failed part of the way through?

## i2c.transfer-path: Transfer checks and retries

- section: Transfers and SMBus
- relevance: 5 - where every check and retry happens

Which checks can fail an `i2c_transfer()` before the hardware is touched, and what does each
return? What does the core's retry loop retry on, and what ends it? Start from
`__i2c_transfer()`.

## i2c.quirks: Adapter quirks

- section: Transfers and SMBus
- relevance: 4 - the way a limited controller says what it cannot do

Where are the limits an adapter driver declares in `struct i2c_adapter_quirks` enforced, on
which paths into the adapter are they not, and what does the caller of a transfer that breaks
one see? Start from `i2c_check_for_quirks()`.

## i2c.smbus-native-fallback: Native SMBus and emulation

- section: Transfers and SMBus
- relevance: 4 - which callback runs is not obvious from the caller

When does the core call the adapter's SMBus callback and when does it emulate the transaction
with I2C messages, which return value from the callback makes it fall back to emulation, and how
is packet error checking done in each case?

## i2c.smbus-block: SMBus block transfers

- section: Transfers and SMBus
- relevance: 4 - buffer overruns hide in the length byte

How large must the buffer a caller passes to `i2c_smbus_read_block_data()` be? What do the block
helpers and the core do with a caller's length of zero or above the SMBus maximum: clamp or
reject, with which error, before or after the adapter is called? Who checks the length a device
announces, on the native path and on the emulated one? Start from `__i2c_smbus_xfer()` and
`i2c_smbus_xfer_emulated()`.

# Bus locking and context

## i2c.bus-locking: Bus locks

- section: Bus locking and context
- relevance: 5 - every transfer takes one and drivers may take it by hand

What do `I2C_LOCK_ROOT_ADAPTER` and `I2C_LOCK_SEGMENT` select when a bus is locked, and which of
them do `i2c_transfer()` and `i2c_smbus_xfer()` take? Who installs an adapter's
`struct i2c_lock_operations`: only the core and the multiplexer core, or drivers too, and when
is the default used?

## i2c.mux-locking: Mux-locked and parent-locked multiplexers

- section: Bus locking and context
- relevance: 4 - picking the wrong kind deadlocks the select callback

Which lock does a mux-locked multiplexer hold across select, transfer and deselect, and which does
a parent-locked one hold? Which transfer functions may the select callback of each kind call on
the parent adapter? What can other traffic on the parent bus do between select and the transfer in
each kind? Start from `i2c_mux_alloc()` and `Documentation/i2c/i2c-topology.rst`.

## i2c.atomic-transfers: Atomic transfers

- section: Bus locking and context
- relevance: 4 - a late PMIC access must not sleep

When does the core consider a transfer to be in atomic mode, what does it return then if the bus
lock is busy, and what happens when the adapter has no atomic callback? Start from
`i2c_in_atomic_xfer_mode()` and `__i2c_lock_bus_helper()`.

## i2c.unlocked-usage: Unlocked transfer functions

- section: Bus locking and context
- relevance: 4 - a missing or doubled lock deadlocks or races

What are the requirements for a caller of `__i2c_transfer()` and `__i2c_smbus_xfer()` in order to
assure safe usage? Name in-tree code outside the core that shows it.

# Clients, drivers and adapters

## i2c.driver-callbacks: Driver callback signatures

- section: Clients, drivers and adapters
- relevance: 4 - old signatures still appear in out-of-tree code and in memory

How does a probe function of a `struct i2c_driver` obtain the matching `struct i2c_device_id`
entry, or the driver data that goes with whichever table matched?

## i2c.instantiation: Ways to create a client

- section: Clients, drivers and adapters
- relevance: 4 - each way has different ownership

A table of the ways a `struct i2c_client` comes to exist, to choose between: for each, the
function it goes through and who is expected to unregister the result. For which adapters does
`i2c_detect()` probe addresses?

## i2c.client-create-checks: Client creation checks

- section: Clients, drivers and adapters
- relevance: 4 - the failure value and the address checks are easy to get wrong

Which requests does `i2c_new_client_device()` refuse before it registers the device, and how far
across a multiplexer tree does its check for an address in use look? What does it return on
failure?

## i2c.unregister-argument: Unregistering a failed client

- section: Clients, drivers and adapters
- relevance: 4 - decides whether an error path may pass on what client creation returned

Which values other than a pointer to a registered client may a caller pass to
`i2c_unregister_device()`, and what does the function do with each?

## i2c.probe-sequence: Probe and remove sequence

- section: Clients, drivers and adapters
- relevance: 4 - what is already set up when the driver's probe runs

What has `i2c_device_probe()` set up for a client before it calls the driver's probe? Which of
that does `i2c_device_remove()` undo after the driver's remove returns? When are device-managed
resources of the client released relative to the remove callback?

## i2c.lookup-refs: Lookup references

- section: Clients, drivers and adapters
- relevance: 4 - each lookup needs a different put

Which references do `i2c_find_device_by_fwnode()`, `i2c_find_adapter_by_fwnode()`,
`i2c_get_adapter_by_fwnode()` and `i2c_get_adapter()` take on what they return, and which call
releases each? What do the device tree wrappers around them add?

## i2c.adapter-lifetime: Adapter registration and removal

- section: Clients, drivers and adapters
- relevance: 5 - the adapter structure is embedded in driver data

What does `i2c_del_adapter()` wait for, and what does it do to the adapter's embedded `struct
device` afterwards? What are the requirements for the memory that holds the `struct i2c_adapter`,
and for the order of teardown in the driver's remove, in order to assure safe usage?

## i2c.adapter-register-checks: Adapter registration checks

- section: Clients, drivers and adapters
- relevance: 5 - a field that the core does not check is used as the driver left it

Which fields that the driver filled in does `i2c_register_adapter()` check, and what does it
return when a check fails? Start from `i2c_add_adapter()`.

# Core build configurations

## i2c.change-checklist: Stubs, target-mode guards and tests

- section: Core build configurations
- relevance: 4 - the core is built in more configurations than a developer tests

Which declarations in `include/linux/i2c.h` have a stub for a kernel built without I2C and which
have none, and how are the target-mode functions and their source file guarded? Which test modules
and tracepoint headers depend on the structures in `include/linux/i2c.h`? Write configuration
symbols in full.

# Conventions

## i2c.conventions: Conventions for new code

- section: Conventions
- verbatim: ../verbatim/i2c-conventions.md

# Model gaps

## i2c.model-gaps: Other mistakes models make

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
