# Questions: I2C (measurement set)

- guide: i2c.md
- title: I2C Subsystem

A wide set of questions about the I2C core under `drivers/i2c/` and
`include/linux/i2c.h`: the objects, the path of a transfer, message buffers
and DMA, SMBus and its emulation, bus locking with multiplexers, atomic and
suspended transfers, how clients are created, probed and looked up, adapter
registration and removal, target mode, and what a change to the core has to
keep working. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written
guide it will replace is 566 words and is only about message buffers and DMA,
so most of what is asked here cannot be in the built guide; the point is to
find which few things must be. Individual bus drivers, I3C and regmap are not
covered. The trimmed set a guide is built from is `../i2c.md`. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## i2c.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold the core proper, the SMBus layer, the device tree and ACPI
parts, target mode, the character device, the multiplexer core and the address
translator core, the component prober, SMBus alert and SPD handling, the test
backends and the stub, the generic algorithms, and the bus and multiplexer
drivers? Which header is internal to the core? A table. Start from
`drivers/i2c/Makefile`.

## i2c.objects: Core objects and headers

- section: Finding your way
- relevance: 4 - every patch is phrased in these
- words: 100

What are `struct i2c_adapter`, `struct i2c_algorithm`, `struct i2c_client`,
`struct i2c_driver`, `struct i2c_msg` and `struct i2c_device_id`, how do they
point at each other, and which header defines each? Start from
`include/linux/i2c.h` and what it includes.

## i2c.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules live only there
- words: 70

Which files under `Documentation/i2c/` are the authority on DMA and message
buffers, on error codes, on functionality bits, on creating devices, on
multiplexer topologies and their locking, and on target mode?

# What this tree calls things

## i2c.algorithm-callbacks: Algorithm callback names

- section: Names
- relevance: 4 - the names have been changing and both spellings compile
- words: 70

What does `struct i2c_algorithm` call its callbacks for an I2C transfer, for
the atomic variant, for SMBus, and for registering and unregistering a client
the adapter answers to as a target? Which spellings are aliases of which, how
is the aliasing done, and which does the kerneldoc say to use?

## i2c.driver-callbacks: Driver callback signatures

- section: Names
- relevance: 4 - old signatures still appear in out-of-tree code and in memory
- words: 70

What are the signatures of the probe, remove and shutdown callbacks in
`struct i2c_driver`, and how does a probe function obtain the matching
`struct i2c_device_id` entry or the driver data that goes with whichever table
matched? Which other fields does the structure have?

# Transfers

## i2c.transfer-path: Path of a transfer

- section: Transfers
- relevance: 5 - where every check and retry happens
- words: 100

What does the core do between a call to `i2c_transfer()` and the adapter's
callback, in order: which lock, which checks that can fail before the hardware
is touched and what each returns, tracing, and the retry loop with what ends
it? Start from `__i2c_transfer()`.

## i2c.transfer-returns: Transfer return values

- section: Transfers
- relevance: 5 - callers compare against the wrong number
- words: 80

What do `i2c_transfer()`, `i2c_master_send()`, `i2c_master_recv()` and the
SMBus read and write helpers such as `i2c_smbus_read_byte_data()` and
`i2c_smbus_read_block_data()` each return on success and on failure,
what is an adapter's transfer callback expected to return, and what can a
caller learn about a transfer that failed part of the way through?

## i2c.msg-flags: Message flags and functionality

- section: Transfers
- relevance: 4 - a flag the adapter does not implement is silently ignored or fails
- words: 90

Which `struct i2c_msg` flags may be used with any adapter and which need a
functionality bit, and which bit? How does a client driver find out what an
adapter supports? A table. Start from `include/uapi/linux/i2c.h` and
`i2c_check_functionality()`.

## i2c.recv-len: Length-prefixed reads

- section: Transfers
- relevance: 3 - the buffer size rule is not in the flag's name
- words: 60

For a read message whose length is supplied by the device in its first byte,
what must the caller put in the message length and how large must its buffer
be, what does the adapter driver do to the length field, and what limits the
length the device may announce? Start from `I2C_M_RECV_LEN`.

## i2c.quirks: Adapter quirks

- section: Transfers
- relevance: 4 - the way a limited controller says what it cannot do
- words: 80

How does an adapter driver declare that its hardware cannot do every legal I2C
transfer, which limits and flags can it declare, where are they enforced, and
what does the caller of a transfer that breaks one see? Start from
`struct i2c_adapter_quirks` and `i2c_check_for_quirks()`.

## i2c.fault-codes: Fault codes

- section: Transfers
- relevance: 3 - reviewers ask for the documented code
- words: 80

Which error code is an adapter driver expected to return when the address is
not acknowledged, when arbitration is lost, when the transfer times out, when
the operation or the message is not supported, and when the adapter is
suspended, and where is that written down? Which of them does the core act on?

# Buffers and DMA

## i2c.dma-buffer-rule: Message buffers and DMA

- section: Buffers and DMA
- relevance: 5 - the rule differs from SPI and USB and is often misquoted
- words: 80

Does the buffer of a `struct i2c_msg` have to be safe for DMA? If an adapter
driver uses DMA and is handed a buffer that is not marked safe, what in the
tree, if anything, makes the transfer safe, and whose job is it? Start from
`Documentation/i2c/dma-considerations.rst`.

## i2c.dma-safe-flag: DMA-safe flag

- section: Buffers and DMA
- relevance: 5 - a promise made by the caller that nothing checks
- words: 80

What does `I2C_M_DMA_SAFE` on a message assert, does anything verify it, which
client-facing functions set it for their caller, and where does the core set
it on messages it builds itself? May userspace set it?

## i2c.dma-helpers: Bounce buffer helpers

- section: Buffers and DMA
- relevance: 5 - the contract an adapter driver relies on
- words: 100

What exactly do `i2c_get_dma_safe_msg_buf()` and `i2c_put_dma_safe_msg_buf()`
do: every reason the first returns NULL and what the driver does then, when it
returns the message's own buffer, when it allocates and how the allocation is
filled, what the second does with its last argument, what it does when handed
NULL, and from which context they may be called?

## i2c.dma-adapter-patterns: DMA in adapter drivers

- section: Buffers and DMA
- relevance: 5 - decides whether an ordinary buffer is ever mapped for DMA
- words: 100

Do all adapter drivers under `drivers/i2c/busses/` that use DMA obtain their
buffer through the core's bounce buffer helpers? Describe the different ways
in-tree adapter drivers decide what memory to map, naming one driver for each,
and say for each what happens to a message whose buffer is on the caller's
stack.

## i2c.dma-client-usage: DMA-safe variants in client drivers

- section: Buffers and DMA
- relevance: 5 - the subject of the hand-written guide
- words: 90

What usage of `i2c_master_send_dmasafe()`, `i2c_master_recv_dmasafe()` or a
hand-set `I2C_M_DMA_SAFE` by a client driver is unsafe, and what that looks
similar is correct, including a buffer that is a member of an allocated
structure? Is passing a stack buffer to `i2c_transfer()` or to the ordinary
send and receive functions correct? Name in-tree code that shows the correct
forms.

## i2c.dma-adapter-usage: Helper pairing in adapter drivers

- section: Buffers and DMA
- relevance: 4 - leaks and lost read data on error paths
- words: 80

What usage of the bounce buffer helpers in an adapter driver's transfer path
is unsafe, and what that looks similar is correct? Cover the error paths, the
value passed for whether data was transferred, the threshold, and atomic
transfers. Name an in-tree driver that shows the correct form.

## i2c.smbus-emulation-buffers: SMBus emulation buffers

- section: Buffers and DMA
- relevance: 4 - the core's own messages mix stack and heap buffers
- words: 80

When the core emulates an SMBus transaction with I2C messages, where do the
message buffers live, for which transaction types are they allocated and
marked DMA-safe, what happens when that allocation fails, and who frees them?
Start from `i2c_smbus_xfer_emulated()`.

## i2c.userspace-buffers: Character device buffers

- section: Buffers and DMA
- relevance: 3 - the one place user data becomes a message buffer
- words: 70

How does the combined read and write ioctl of the I2C character device turn
user buffers into message buffers, which flag does it add, what limits does it
put on the number of messages and on each length, and how does it treat a
length-prefixed read? Start from `i2cdev_ioctl_rdwr()`.

# SMBus

## i2c.smbus-block: SMBus block transfers

- section: SMBus
- relevance: 4 - buffer overruns hide in the length byte
- words: 90

How large must the buffer a caller passes to `i2c_smbus_read_block_data()` be,
what do the I2C block read and write helpers do with a length above the SMBus
maximum, which block lengths does the core reject before the adapter is
called and with which error, and what is returned when a device announces a
block longer than the maximum? Start from `__i2c_smbus_xfer()`.

## i2c.smbus-native-fallback: Native SMBus and emulation

- section: SMBus
- relevance: 4 - which callback runs is not obvious from the caller
- words: 70

When does the core call the adapter's SMBus callback and when does it emulate
the transaction with I2C messages, which return value from the callback makes
it fall back to emulation, and how is packet error checking done in each case?

# Locking and context

## i2c.bus-locking: Bus locks

- section: Locking and context
- relevance: 5 - every transfer takes one and drivers may take it by hand
- words: 100

Which locks does `struct i2c_adapter` carry, of what type, what do the flags
`I2C_LOCK_ROOT_ADAPTER` and `I2C_LOCK_SEGMENT` select, what is
`struct i2c_lock_operations` for and who replaces the default, and which flag
do `i2c_transfer()` and `i2c_smbus_xfer()` lock with?

## i2c.unlocked-usage: Unlocked transfer functions

- section: Locking and context
- relevance: 4 - a missing or doubled lock deadlocks or races
- words: 80

What usage of `__i2c_transfer()` and `__i2c_smbus_xfer()` is unsafe, and what
that looks similar is correct? Say which lock call must surround them and with
which flag, and name in-tree code outside the core that uses them correctly.

## i2c.mux-locking: Mux-locked and parent-locked multiplexers

- section: Locking and context
- relevance: 4 - picking the wrong kind deadlocks the select callback
- words: 100

What is the difference between a mux-locked and a parent-locked multiplexer:
which lock operations and which transfer functions does the multiplexer core
give each, which kind may use ordinary locked transfers on the parent from its
select callback, and what can other traffic on the parent bus do between
select and the transfer? Start from `i2c_mux_alloc()` and
`Documentation/i2c/i2c-topology.rst`.

## i2c.atomic-transfers: Atomic transfers

- section: Locking and context
- relevance: 4 - a late PMIC access must not sleep
- words: 80

When does the core consider a transfer to be in atomic mode, how is the bus
lock taken then and what is returned if it is busy, which adapter callbacks
are used, and what happens when the adapter has none? Start from
`i2c_in_atomic_xfer_mode()` and `__i2c_lock_bus_helper()`.

## i2c.suspended-adapter: Transfers to a suspended adapter

- section: Locking and context
- relevance: 3 - the helper is optional and the error is specific
- words: 60

How does an adapter driver tell the core that it is suspended, under which
lock is that state changed, what does a transfer attempted in that state
return and log, and is using the mechanism mandatory? Start from
`i2c_mark_adapter_suspended()`.

# Devices and adapters

## i2c.instantiation: Ways to create a client

- section: Devices and adapters
- relevance: 4 - each way has different ownership
- words: 100

In which ways does an `i2c_client` come to exist (firmware description, board
files, a call from another driver, probing a list of addresses, userspace,
detection by a driver), which function does each go through, who is expected
to unregister the result, and what is the state of class-based detection in
this tree?

## i2c.client-create-checks: Creating a client

- section: Devices and adapters
- relevance: 4 - the failure value and the address checks are easy to get wrong
- words: 90

What does `i2c_new_client_device()` check before registering the device
(address validity, whether the address is in use and how far across a
multiplexer tree it looks, two creations of the same address at once), what
does it return on failure, and what may a caller pass to
`i2c_unregister_device()`?

## i2c.probe-sequence: Probe and remove sequence

- section: Devices and adapters
- relevance: 4 - what is already set up when the driver's probe runs
- words: 100

What does the bus do in `i2c_device_probe()` before it calls the driver's
probe, in order, and what does `i2c_device_remove()` undo after the driver's
remove returns? When are device-managed resources of the client released
relative to the driver's remove callback, including ones acquired after probe
finished?

## i2c.lookup-refs: Lookup references

- section: Devices and adapters
- relevance: 4 - each lookup needs a different put
- words: 80

Which references do `i2c_find_device_by_fwnode()`,
`i2c_find_adapter_by_fwnode()`, `i2c_get_adapter_by_fwnode()` and
`i2c_get_adapter()` take on what they return, and which call releases each?
What do the device tree wrappers around them add?

## i2c.adapter-lifetime: Adapter registration and removal

- section: Devices and adapters
- relevance: 5 - the adapter structure is embedded in driver data
- words: 110

What must an adapter driver fill in before `i2c_add_adapter()`, how is the bus
number chosen, what does registration create and which clients does it
instantiate, and what does `i2c_del_adapter()` do in order, including what it
waits for and what it does to the embedded device afterwards? What does that
imply for where the structure may live and for the order of teardown in the
driver's remove?

## i2c.target-mode: Target mode

- section: Devices and adapters
- relevance: 3 - a second, smaller API with its own rules
- words: 90

How does a backend driver make an adapter answer to an address as a target:
which function, which client flag, which lock is taken around the adapter's
callback, which events is the backend called with and in what context, and how
is such a client marked in a device tree? Start from `i2c_slave_register()`.

# Changing the implementation

## i2c.change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - the core is built in more configurations than a developer tests
- words: 90

What must a change to `drivers/i2c/i2c-core-base.c` or `include/linux/i2c.h`
keep working besides the default build: kernels without I2C, without target
mode, without device tree or ACPI, nested multiplexers under lockdep, the
userspace header, the tracepoints, and which in-tree drivers or modules exist
only to test the core? Say where each lives.
