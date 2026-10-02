# What the i2c measurement found

Three models were asked the 33 questions in `i2c-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 6.18) and needed the fewest corrections, reader A
was close behind it (6.8 to 6.15), and reader B was narrower (6.10 to 6.12),
much less sure of itself, and had several rules backwards and a handful of
names it made up. The hand-written guide was never checked against current
sources, so differences between it and the built guide are expected and are
noted near the end.

Readers A and C know this code well: the file map, the message flags and their
functionality bits, that a message buffer need not be DMA-safe, what
`I2C_M_DMA_SAFE` promises and where the core sets it, the i2c-dev buffers, the
lookup functions and their puts, the two kinds of multiplexer, the path of a
transfer. What all three get wrong is smaller and sharper: which adapter
drivers do what with an unmarked buffer, the block length check that now sits
in front of every SMBus path, a header that moved, and a set of details in
probe, registration and the configuration stubs. Reader B gets the DMA rules
themselves wrong in ways that would change a review verdict, so the build set
keeps those questions even though two readers answer them.

## What all three readers got wrong

- **Which adapter drivers bounce, which do PIO, which map as is.** Every reader
  put at least one driver in the wrong class. Reader A had `i2c-stm32f7.c`
  mapping the message buffer directly and left out the drivers that use DMA
  only for marked messages; reader C had `i2c-at91-master.c` mapping directly;
  reader B named i2c-designware (no DMA path) and i2c-rk3x (does not use the
  helpers) and said a stack buffer is rescued by swiotlb. In the tree:
  `i2c-sh_mobile.c`, `i2c-at91-master.c`, `i2c-stm32f7.c`, `i2c-mt65xx.c`,
  `i2c-mxs.c`, `i2c-qcom-geni.c`, `i2c-imx-lpi2c.c`, `i2c-amd-mp2-plat.c` and
  `i2c-virtio.c` go through `i2c_get_dma_safe_msg_buf()`; `i2c-rcar.c` and
  `i2c-imx.c` use DMA only when `I2C_M_DMA_SAFE` is set and PIO otherwise;
  `i2c-tegra.c` copies through its own coherent buffer; `i2c-qup.c` maps
  `msg->buf` as it is and avoids DMA only for vmalloc addresses.
- **`__i2c_smbus_xfer()` checks block lengths itself.** For I2C block reads and
  writes, block process calls and block writes it returns `-EINVAL` when
  `block[0]` is 0 or above `I2C_SMBUS_BLOCK_MAX`, before the tracepoints and
  before the native callback or the emulation. Reader C said it does no
  check, reader A that only the emulation checks and was unsure about 0,
  reader B that a length outside 1 to 32 gives `-EPROTO`. The `-EPROTO` is
  only in `i2c_smbus_xfer_emulated()`, only for a device that announces more
  than the maximum; on the native path the adapter driver checks.
- **Who checks a length-prefixed read.** Every reader said an announced count
  outside 1 to 32 is rejected. That is left to each adapter driver, and they
  differ: `i2c-algo-bit.c` rejects 0 with `-EPROTO`, `i2c-imx.c` accepts 0,
  `i2c-designware-master.c` substitutes 1.
- **`struct i2c_device_id` is in `include/linux/device-id/i2c.h`**, which
  `include/linux/i2c.h` includes directly; `mod_devicetable.h` only includes
  it. All three said `mod_devicetable.h`.
- **Probe and remove.** The interrupt is looked up with
  `fwnode_irq_get_byname()` and `fwnode_irq_get()`, not the device tree calls
  all three named. `i2c_device_remove()` does not detach the PM domain; probe
  attaches with `PD_FLAG_DETACH_POWER_OFF` and the driver core detaches. A
  per-client debugfs directory is created before probe and removed after
  remove.
- **Who replaces the lock operations.** Not only the multiplexer core:
  `i2c-atr.c`, `i2c-gpio.c`, `i2c-cht-wc.c`, `i2c-designware-amdpsp.c` and
  several DRM drivers set `lock_ops`; the default is installed only when it
  is NULL.
- **Class-based detection.** `I2C_CLASS_HWMON` and `I2C_CLASS_DEPRECATED` are
  the only classes left. Reader A still had I2C_CLASS_SPD, reader C made up
  client flags for user-created and detected clients, reader B called
  detection merely discouraged.
- **`i2c_register_adapter()` checks only `name` and `algo`.** Readers listed
  the transfer callback and `functionality` as required; `functionality` is
  called unchecked.
- **The configuration stubs.** No reader could say which parts of
  `include/linux/i2c.h` have stubs for a kernel without I2C (only
  `i2c_verify_client()` and the fwnode lookups), that target-mode functions
  are declared unguarded while the file is built only with `CONFIG_I2C_SLAVE`,
  or that there are three tracepoint headers (`i2c.h`, `smbus.h`,
  `i2c_slave.h`).

## What readers A and B got wrong as well

- **Atomic mode.** Both gave the wrong condition (reader B: system state not
  running, or an oops in progress). It is `system_state > SYSTEM_RUNNING`
  together with not preemptible, or interrupts disabled when there is no
  preempt count. The warning for a missing atomic callback is a plain `WARN()`
  on every transfer, and only when both atomic callbacks are absent.
- **The bounce helpers.** Reader A said both helpers allocate with
  `GFP_KERNEL`; only the get does, and `i2c-stm32f7.c` calls the put from a
  DMA completion callback. A zero length returns NULL whatever the threshold.
  Reader B said the read bounce buffer is left uninitialised (it is zeroed)
  and did not know NULL also means the allocation failed.

## What reader B got wrong as well

- **The rule for message buffers.** It said the documentation tells adapter
  drivers not to assume buffers are safe and that the adapter must bounce. The
  document says DMA safety is not mandatory for callers, recommends it for
  larger messages, and says host drivers that were not updated risk unsafe
  DMA; bouncing, PIO and a private buffer are all in use.
- **Who sets `I2C_M_DMA_SAFE`.** It said the core never sets the flag on its
  own messages and that i2c-dev strips it. `i2c_smbus_try_get_dmabuf()` sets
  it on the heap buffers of emulated block transfers, and `i2cdev_ioctl_rdwr()`
  sets it on every message after `memdup_user()`. It also said a failed
  allocation in the emulation returns `-ENOMEM`; the stack buffer is used
  instead and the transfer goes ahead.
- **The callback names.** It called `master_xfer` current and said `reg_slave`
  was renamed with no alias. `struct i2c_algorithm` pairs `xfer`/`master_xfer`,
  `xfer_atomic`/`master_xfer_atomic`, `reg_target`/`reg_slave` and
  `unreg_target`/`unreg_slave` in anonymous unions, and the kerneldoc marks the
  older spellings deprecated, though the core still calls through them.
- **Return values.** It said the block read helpers return the value read; they
  return the byte count. Reader C said every call returns a negative errno on
  failure; `i2c_transfer_buffer_flags()` passes a short message count from
  `i2c_transfer()` through unchanged, so `i2c_master_send()` can return 0.
- There is an error code document, `Documentation/i2c/fault-codes.rst`; the
  block helpers clamp the length to 32; emulation calls `__i2c_transfer()`,
  not the locked form; both kinds of multiplexer take the parent's `mux_lock`;
  `i2c_mux_alloc()` takes flags, not a bool, and `i2c_mux_add_adapter()`
  installs the lock operations; the busy check walks up and down the
  multiplexer tree; `addrs_in_instantiation` stops two creations of one
  seven-bit address; `i2c_slave_register()` only warns when the client flag is
  missing; a kernel without I2C has no stub for `i2c_transfer()`.
- Names it made up: i2c-core-prober.c, i2c-core-spd.c, i2c_add_mux_adapter(),
  i2c_sysfs_new_device(), a lock_key field in the adapter.

## What the readers already knew

The file map (A and C), message flags and functionality bits, the rule that a
message buffer need not be DMA-safe and what the flag promises (A and C), the
SMBus emulation and i2c-dev buffers (A and C), the references each lookup
takes, mux-locked against parent-locked, the suspended-adapter helper, the
quirks structure, that `i2c_new_client_device()` returns an `ERR_PTR()` and
`i2c_unregister_device()` takes one, the order of `i2c_del_adapter()` and that
it waits for the last reference.

## Where the hand-written guide is stale

`i2c.md` says that when an adapter needs DMA "the core automatically allocates
a temporary bounce buffer" and that controller drivers that use DMA "must call"
`i2c_get_dma_safe_msg_buf()`. Neither is so. The helpers are optional, the
documentation says a driver is free to do its own handling, and in the tree
`i2c-rcar.c` and `i2c-imx.c` never bounce (unmarked messages go by PIO),
`i2c-tegra.c` has its own buffer and `i2c-qup.c` maps whatever it is given. So
"a stack buffer passed to an ordinary transfer is never a bug" holds for the
core's contract but says nothing about what a given adapter will do with it.
It says the helper returns NULL for a message under the threshold; it also does
so for a zero length and when the allocation fails. It names the adapter
callback `master_xfer`; the tree's name is `xfer` and `master_xfer` is a
deprecated alias. It does not say that the get must be called from process
context, that SMBus emulation and i2c-dev set the flag themselves, or that the
in-tree users of the DMA-safe variants that pass a structure member align it.
Its `REPORT as bugs` list is kept as two "unsafe usage" questions. It was never
onboarded to the drift checker.

## What was left out of the build set and why

The hand-written guide is 566 words and only about buffers and DMA, so the
built guide is sized to 600 words, the floor for a built guide (480 to 720),
and no question is budgeted under 40: a first build with 30 to 55 words a
question came out as fragments that meant nothing without the question beside
them. Eleven questions fit, the same eleven as in that first build, with 540
words of budget where there were 455. The extra words went to the four answers
that had been held under 40 (the file table, the callback names, the DMA-safe
flag and the change checklist) and to the ones that carry several facts at once
(the bounce helpers, the return values, the block lengths); a twelfth question
at 40 words would have pushed the guide towards the top of its range, so none
was added back. Six of the eleven are the DMA questions, because that is the
guide's subject, one reader is wrong about all of it and no reader can classify
the adapter drivers. Three more are the facts outside DMA most likely to change
a verdict: the callback names, the transfer return values, and the block length
checks that every reader got wrong. The file table is cut to what a file's name
does not say, and the change checklist is kept because all three were weak.
Left to the source: the path of a transfer, message flags, quirks and fault
codes (known or documented in one place); bus locking, the unlocked transfer
functions and multiplexers (readers A and C fair, and
`Documentation/i2c/i2c-topology.rst` covers it); atomic transfers and the
suspended adapter (one function each in `drivers/i2c/i2c-core.h`);
instantiation, the checks on creating a client, probe order, lookups, adapter
lifetime and target mode (real errors, listed above, but each confined to one
function a reviewer of such a patch will open anyway).

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A           46        22%     12      5   6.8 to 6.15
reader-B          101        68%      1     31   6.10 to 6.12
reader-C           37        15%     18      2   6.12 to 6.18

question                         reader-A      reader-B      reader-C   verdict
i2c.core-files                    0% ( 0)      11% ( 5)       0% ( 0)   all fair: drop, or shrink to a pointer
i2c.objects                       3% ( 1)      50% ( 4)       5% ( 1)   weak: reader-B
i2c.docs                         20% ( 1)      44% ( 1)      24% ( 0)   weak: reader-B
i2c.algorithm-callbacks          38% ( 2)      82% ( 2)       5% ( 1)   weak: reader-B
i2c.driver-callbacks             18% ( 2)      51% ( 1)      21% ( 2)   weak: reader-B
i2c.transfer-path                12% ( 1)      64% ( 5)       3% ( 1)   weak: reader-B
i2c.transfer-returns             25% ( 1)      54% ( 2)      40% ( 1)   weak: reader-B, reader-C
i2c.msg-flags                     0% ( 0)      24% ( 2)       0% ( 0)   middling
i2c.recv-len                     22% ( 1)      56% ( 2)      34% ( 2)   weak: reader-B
i2c.quirks                       36% ( 1)      72% ( 2)      13% ( 1)   weak: reader-B
i2c.fault-codes                  35% ( 1)      52% ( 3)      12% ( 2)   weak: reader-B
i2c.dma-buffer-rule               0% ( 2)      85% ( 1)       1% ( 1)   weak: reader-B
i2c.dma-safe-flag                 0% ( 0)      77% ( 5)       9% ( 1)   weak: reader-B
i2c.dma-helpers                  58% ( 2)      65% ( 1)      12% ( 1)   weak: reader-A, reader-B
i2c.dma-adapter-patterns         43% ( 2)      81% ( 2)      32% ( 2)   weak: reader-A, reader-B
i2c.dma-client-usage             34% ( 2)      75% ( 5)       0% ( 0)   weak: reader-B
i2c.dma-adapter-usage            17% ( 2)      68% ( 4)       0% ( 0)   weak: reader-B
i2c.smbus-emulation-buffers       0% ( 0)      88% ( 4)       0% ( 0)   weak: reader-B
i2c.userspace-buffers            10% ( 1)      78% ( 4)       0% ( 0)   weak: reader-B
i2c.smbus-block                  48% ( 3)      85% ( 4)      39% ( 2)   weak: reader-A, reader-B
i2c.smbus-native-fallback        46% ( 2)      79% ( 3)      34% ( 2)   weak: reader-A, reader-B
i2c.bus-locking                  11% ( 1)      78% ( 5)      17% ( 3)   weak: reader-B
i2c.unlocked-usage               28% ( 1)      80% ( 2)      19% ( 1)   weak: reader-B
i2c.mux-locking                  11% ( 1)      75% ( 4)       0% ( 0)   weak: reader-B
i2c.atomic-transfers             24% ( 2)      78% ( 2)       4% ( 1)   weak: reader-B
i2c.suspended-adapter            14% ( 1)      85% ( 2)      19% ( 0)   weak: reader-B
i2c.instantiation                17% ( 2)      56% ( 6)      33% ( 3)   weak: reader-B
i2c.client-create-checks         29% ( 2)      88% ( 4)      17% ( 2)   weak: reader-B
i2c.probe-sequence               21% ( 2)      84% ( 2)      28% ( 2)   weak: reader-B
i2c.lookup-refs                   0% ( 0)      59% ( 1)       0% ( 0)   weak: reader-B
i2c.adapter-lifetime             29% ( 1)      70% ( 3)      10% ( 1)   weak: reader-B
i2c.target-mode                  28% ( 1)      73% ( 3)      20% ( 1)   weak: reader-B
i2c.change-checklist             51% ( 5)      78% ( 5)      45% ( 3)   all weak
```

In the build set `i2c.core-files`, `i2c.algorithm-callbacks` and
`i2c.smbus-block` are worded more narrowly than they were measured, and one
wildcard helper name in `i2c.transfer-returns` was replaced with two real ones
after the measurement. Smaller differences: `i2c.dma-buffer-rule` opens by
asking what the tree requires of a message buffer where the measured question
asked whether the buffer has to be DMA-safe, because a build answered the
yes-or-no form with a bullet that did not say what it was about;
`i2c.dma-safe-flag` leaves out userspace and asks where, if anywhere, the core
sets the flag; `i2c.dma-adapter-patterns` asks for a table; `i2c.core-files`
says to leave out a topic the tree has no file for; and `i2c.change-checklist`
asks for configuration symbols written in full, after a build abbreviated them.
The ids are unchanged.

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `i2c.objects`, `i2c.driver-callbacks`, `i2c.transfer-path`, `i2c.quirks`, `i2c.smbus-emulation-buffers`, `i2c.smbus-native-fallback`, `i2c.bus-locking`, `i2c.unlocked-usage`, `i2c.mux-locking`, `i2c.atomic-transfers`, `i2c.instantiation`, `i2c.client-create-checks`, `i2c.probe-sequence`, `i2c.lookup-refs`, `i2c.adapter-lifetime`.

## Questions reorganised

- Subjects now: message buffers and DMA; transfers and SMBus; bus locking and context; clients,
  drivers and adapters; other builds of the core. 28 questions became 27; every other id is kept.
- Dropped: `i2c.objects`. What the structures are is the overview, and the one header every reader
  had wrong (`struct i2c_device_id`) is a row of `i2c.core-files`.
- Asked twice, now once: where the core sets the DMA-safe flag (`i2c.smbus-emulation-buffers`, out
  of `i2c.dma-safe-flag`); a stack buffer to an ordinary transfer (`i2c.dma-buffer-rule`, out of
  `i2c.dma-client-usage`). Checklists cut to two or three asks, order of steps inside a function gone.
