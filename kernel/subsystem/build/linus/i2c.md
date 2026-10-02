# I2C Subsystem

## Main structures

### Objects and how they relate

- `i2c_bus_type`: holds adapters as well as clients; `i2c_register_adapter()`
  puts the adapter's device on it with type `i2c_adapter_type`, clients have
  `i2c_client_type`.
- Iterating `i2c_bus_type` or an adapter's children yields both kinds (and
  mux child adapters among the children); `i2c_verify_client()` and
  `i2c_verify_adapter()` tell them apart by `dev->type`.
- Target mode outside `struct i2c_algorithm`: only slave spellings exist:
  `i2c_slave_register()`, `i2c_slave_event()`, `enum i2c_slave_event`,
  `I2C_CLIENT_SLAVE`, `slave_cb`, `CONFIG_I2C_SLAVE`. The core has no
  target-named functions, events or client flags.
- SMBus emulation, outside atomic mode: `__i2c_smbus_xfer()` emulates when
  `smbus_xfer` is NULL, and also when `smbus_xfer` returns `-EOPNOTSUPP` and
  `master_xfer` is set.
- `i2c_smbus_xfer_emulated()`: calls `__i2c_transfer()`, not
  `i2c_transfer()`; `i2c_smbus_xfer()` already holds the lock.
- `i2c_transfer()` on a mux-locked child (`i2c_mux_lock_ops`): holds only
  `parent->mux_lock` around `select`; the parent's lock is taken later, inside
  the `i2c_transfer()` on the parent.
- Mux child adapter's `dev.parent`: the parent adapter, set in
  `i2c_mux_add_adapter()`. The mux device (`muxc->dev`) is not the
  `dev.parent`; it is linked by the `mux_device` and `channel-%u` sysfs
  symlinks.
- `struct i2c_atr` (`drivers/i2c/i2c-atr.c`, API in
  `include/linux/i2c-atr.h`): an address translator. Like a mux it creates one
  child adapter per channel, but a transfer rewrites message addresses to
  aliases valid on the parent bus instead of selecting a channel.
- `struct i2c_atr` differs from `struct i2c_mux_core` in three relations:
  - child adapter's `dev.parent` is `desc->parent`, or the ATR device when
    that is NULL, not the parent adapter;
  - `i2c_atr_lock_ops` takes `atr->lock`, one mutex shared by all channels,
    and touches no parent lock;
  - aliases are attached and detached from a notifier on `i2c_bus_type`
    (`i2c_atr_bus_notifier_call()`) when a client is added to or removed from
    a child adapter.
- `i2c_parent_is_i2c_adapter()`: looks only at the direct `dev.parent`;
  `i2c_adapter_depth()` walks every ancestor. They disagree for an adapter
  whose parent is a client device, as under an ATR.
- Address uniqueness: `i2c_check_addr_busy()` compares
  `i2c_encode_flags_to_addr()` values, so a client with `I2C_CLIENT_SLAVE` or
  `I2C_CLIENT_TEN` does not collide with a plain 7-bit client of the same
  number.
- `struct i2c_client` creation: not reserved to the core; whoever calls
  `i2c_new_client_device()` gets the pointer and passes it to
  `i2c_unregister_device()` later. Chip drivers do this for secondary
  addresses with `i2c_new_dummy_device()` or `i2c_new_ancillary_device()`.
- `struct i2c_client` memory of a registered client: freed in
  `i2c_client_dev_release()`, the `release` of `i2c_client_type`;
  `i2c_unregister_device()` does not free it, it ends in
  `device_unregister()`.
- Unregistered `struct i2c_client`: `i2cdev_open()` in
  `drivers/i2c/i2c-dev.c` and `i2c_detect()` build one with `kzalloc_obj()`
  and never register it; its `dev` is all zeroes. The `detect` callback gets
  such a client.
- Core-tracked clients: only `i2c_detect_address()` (onto `driver->clients`)
  and `new_device_store()` (onto `adap->userspace_clients`) link a client
  through `client->detected`. Clients created any other way are on neither
  list.

## Where to look

### Core files

| Job | File | Easy to miss |
|---|---|---|
| Definition of `struct i2c_device_id` | `include/linux/device-id/i2c.h` | Not in `include/linux/mod_devicetable.h`, which gets it only through its `#include "device-id/i2c.h"`. `include/linux/i2c.h` includes `<linux/device-id/i2c.h>` directly and has no include of `mod_devicetable.h`. `I2C_NAME_SIZE` and `I2C_MODULE_PREFIX` are defined in the same file. |
| SMBus alert, creating the ARA client | `drivers/i2c/i2c-core-smbus.c` | `i2c_new_smbus_alert_device()` is here and is built into `i2c-core.o` unconditionally. `i2c_setup_smbus_alert()` is here too, under `IS_ENABLED(CONFIG_I2C_SMBUS)`. |
| SMBus alert, the "smbus_alert" driver and `i2c_handle_smbus_alert()` | `drivers/i2c/i2c-smbus.c` | Built by `CONFIG_I2C_SMBUS`. |
| SPD handling | `drivers/i2c/i2c-smbus.c` | Under `IS_ENABLED(CONFIG_DMI)`, in a file built by `CONFIG_I2C_SMBUS`. `i2c_register_spd()` is `static` and takes `bool write_disabled`. Callers use `i2c_register_spd_write_disable()` or `i2c_register_spd_write_enable()`. |
| Component prober | `drivers/i2c/i2c-core-of-prober.c` | Linked into `i2c-core.o` by `CONFIG_OF_DYNAMIC`. `include/linux/i2c-of-prober.h` declares the functions only under `IS_ENABLED(CONFIG_OF_DYNAMIC)` and has no stubs for the other case. |
| Core's internal helpers | `drivers/i2c/i2c-core.h` | Not included by `drivers/i2c/i2c-core-of-prober.c`; included by `drivers/i2c/i2c-boardinfo.c`. `i2c_check_7bit_addr_validity_strict()` and `i2c_dev_irq_from_resources()` are not exported, so code outside `i2c-core.o` that is built as a module cannot call them. |

## Message buffers and DMA

**DMA rule for message buffers**

- Models have this right; see `__i2c_transfer()` in
  `drivers/i2c/i2c-core-base.c`, which hands `msgs` to the adapter untouched.

**DMA-safe flag**

- `i2cdev_ioctl_rdwr()` in `drivers/i2c/i2c-dev.c`: ORs `I2C_M_DMA_SAFE` into
  every message after `memdup_user()`; it neither rejects nor clears a flag
  value that came from user space.
- `i2cdev_read()` and `i2cdev_write()`: pass heap buffers to
  `i2c_master_recv()` and `i2c_master_send()`, so those messages are unflagged.
- `dma_map_single_attrs()` in `include/linux/dma-mapping.h`: warns once and
  returns `DMA_MAPPING_ERROR` for a vmalloc address, with or without
  `CONFIG_DMA_API_DEBUG`; with `CONFIG_VMAP_STACK` that covers a stack buffer.
- `check_for_stack()` in `kernel/dma/debug.c`: reports a mapped stack buffer,
  built only with `CONFIG_DMA_API_DEBUG`.

**SMBus emulation buffers**

- `msgbuf0` and `msgbuf1` in `i2c_smbus_xfer_emulated()`: on-stack arrays, of
  `I2C_SMBUS_BLOCK_MAX+3` and `I2C_SMBUS_BLOCK_MAX+2` bytes; every message
  starts out pointing at them, unflagged.
- Heap buffer with `I2C_M_DMA_SAFE`, from `i2c_smbus_try_get_dmabuf()`:

| Transaction | Message re-pointed |
|---|---|
| `I2C_SMBUS_BLOCK_DATA` read | `msg[1]` |
| `I2C_SMBUS_BLOCK_DATA` write | `msg[0]` |
| `I2C_SMBUS_BLOCK_PROC_CALL` | `msg[0]` and `msg[1]` |
| `I2C_SMBUS_I2C_BLOCK_DATA` read | `msg[1]` |
| `I2C_SMBUS_I2C_BLOCK_DATA` write | `msg[0]` |

- `msg[0]` of a block read: the command byte stays in `msgbuf0` on the stack,
  unflagged.
- Allocation failure in `i2c_smbus_try_get_dmabuf()`: no error is returned;
  the message keeps its stack array without the flag and `__i2c_transfer()`
  runs as usual.

**Bounce buffer helpers**

- `i2c_put_dma_safe_msg_buf()`: calls only `memcpy()` and `kfree()`, nothing
  that sleeps; `stm32f7_i2c_dma_callback()` calls it from a dmaengine
  completion callback.
- `i2c_get_dma_safe_msg_buf()` on a zero-length message: returns NULL whatever
  the threshold, including a threshold of 0.
- `i2c_put_dma_safe_msg_buf()` reads `msg->buf`, `msg->len` and `msg->flags`
  at put time: `buf == msg->buf` is the only test for "not a bounce buffer",
  and the copy-back length is the current `msg->len`, not the length at get.
- NULL after the driver has already chosen DMA by length: means the allocation
  failed; `mxs_i2c_xfer_msg()` returns `-ENOMEM` there instead of using PIO.

**DMA in adapter drivers**

- `drivers/i2c/busses/i2c-rcar.c` and `drivers/i2c/busses/i2c-imx.c`: call
  neither helper; they are the flag-gated pattern below.
- **Unsafe usage**: mapping `msg->buf` for DMA when `I2C_M_DMA_SAFE` is clear.
  An unflagged buffer may be a stack array, as `msgbuf0` in
  `i2c_smbus_xfer_emulated()` is; `dma_map_single_attrs()` returns
  `DMA_MAPPING_ERROR` for a vmalloc address.
  - Safe: bounce through `i2c_get_dma_safe_msg_buf()`, map the returned
    pointer, use PIO on NULL, as `lpi2c_imx_dma_xfer()` with its caller
    `lpi2c_imx_xfer_common()` in `drivers/i2c/busses/i2c-imx-lpi2c.c` and
    `start_ch()` with `sh_mobile_i2c_xfer_dma()` in
    `drivers/i2c/busses/i2c-sh_mobile.c` do.
  - Safe: use DMA only when the flag is set and PIO otherwise, as
    `rcar_i2c_dma()` and `i2c_imx_xfer_common()` do; an unflagged message
    never gets DMA on these adapters.
  - Safe: copy into a driver-owned DMA buffer, as `tegra_i2c_xfer_msg()` does
    with `i2c_dev->dma_buf` from `dma_alloc_coherent()`.

**DMA-safe variants in client drivers**

- In-tree clients, for example: `ad5110_read()` in
  `drivers/iio/potentiometer/ad5110.c` uses both `i2c_master_send_dmasafe()`
  and `i2c_master_recv_dmasafe()`; `st1232_ts_read_data()` in
  `drivers/input/touchscreen/st1232.c` sets `I2C_M_DMA_SAFE` by hand.
- `ARCH_DMA_MINALIGN` is what defines the alignment needed for DMA of a
  buffer embedded in a struct; `____cacheline_aligned` aligns to
  `SMP_CACHE_BYTES`, which on arm64 is 64 against an `ARCH_DMA_MINALIGN` of
  128.
- **Unsafe usage**: flagging a buffer that is on the stack, in vmalloc memory,
  or shares an `ARCH_DMA_MINALIGN` block with other data. `rcar_i2c_dma()` and
  `i2c_imx_dma_xfer()` then pass `msg->buf` to `dma_map_single()`, and
  `i2c_get_dma_safe_msg_buf()` returns `msg->buf` itself, with no copy.
  - Safe: a separate heap allocation, as `ts->read_buf` from `devm_kzalloc()`
    in `drivers/input/touchscreen/st1232.c`; `struct devres` aligns `data[]`
    to `ARCH_DMA_MINALIGN`.
  - Safe: a member with `__aligned(IIO_DMA_MINALIGN)` placed last in the
    `iio_priv()` struct, as `buf` in `struct ad5110_data`;
    `iio_device_alloc()` aligns the private area to `IIO_DMA_MINALIGN`, and
    `IIO_DMA_MINALIGN` in `include/linux/iio/iio.h` is at least
    `ARCH_DMA_MINALIGN`.
  - Safe: leaving the flag off the message whose buffer does not qualify, as
    `st1232_ts_read_data()` does for the on-stack `reg` in its first message.

**Helper pairing in adapter drivers**

- Reference for the pairing: `lpi2c_imx_dma_xfer()` in
  `drivers/i2c/busses/i2c-imx-lpi2c.c`; every exit after a non-NULL get
  reaches one put, with `xferred` false on any error.
- Put after a NULL get: optional; `i2c_put_dma_safe_msg_buf()` returns at once
  for NULL.
- Atomic transfers: `start_ch()` in `drivers/i2c/busses/i2c-sh_mobile.c`
  returns before the get when `pd->atomic_xfer`; `lpi2c_imx_xfer_common()`
  takes the PIO branch when `atomic`.
- `pd->stop_after_dma` in `drivers/i2c/busses/i2c-sh_mobile.c`: set to true
  only by `sh_mobile_i2c_dma_callback()`, so the put copies back only when
  the DMA completed.
- **Unsafe usage**: calling `i2c_put_dma_safe_msg_buf()` while the bounce
  buffer is still mapped or the DMA engine may still access it; the put frees
  it with `kfree()`.
  - Safe: terminate and unmap first on failure, unmap first on success, then
    put, as `lpi2c_imx_dma_xfer()` does through `lpi2c_cleanup_dma()` and
    `lpi2c_dma_unmap()`.
- **Unsafe usage**: getting a bounce buffer for an unflagged `I2C_M_RECV_LEN`
  read and then growing `msg->len`; the get allocated the old `msg->len`
  bytes, and the put copies the new `msg->len` bytes out of it.
  - Safe: no DMA for such a message, as `is_use_dma()` in
    `drivers/i2c/busses/i2c-imx-lpi2c.c` returns false on `I2C_M_RECV_LEN`.

## Transfers and SMBus

**Algorithm callback names**

- `master_xfer` and `master_xfer_atomic`: still members of
  `struct i2c_algorithm` in `include/linux/i2c.h`, each in an anonymous union
  with `xfer` and `xfer_atomic`, the same way `reg_slave` and `unreg_slave`
  pair with `reg_target` and `unreg_target`.
- The core calls and tests through the old spellings only: `master_xfer` and
  `master_xfer_atomic` in `__i2c_transfer()`, `__i2c_lock_bus_helper()` and
  `__i2c_smbus_xfer()`; `reg_slave` and `unreg_slave` in
  `i2c_slave_register()` and `i2c_slave_unregister()`.
- `i2c_mux_add_adapter()` and `i2c_atr_new()`: test the parent through
  `master_xfer` and fill the child through `xfer`.
- Searching for the new spelling finds no call site; every direct call of the
  callback in this tree, inside or outside `drivers/i2c`, is spelled
  `master_xfer` or `master_xfer_atomic`.
- Adapter drivers here use either spelling in their initialisers; both are
  valid.

**Transfer return values**

- `__i2c_transfer()`: returns the callback's value unchanged, so a callback
  that returns 0 or a positive count below `num` hands exactly that to the
  caller of `i2c_transfer()`; the core neither converts it to an errno nor
  rounds it up.
- `i2c_transfer_buffer_flags()`: passes any value other than 1 through, so
  `i2c_master_send()` and `i2c_master_recv()` can return 0.
- SMBus block helpers that take a length: can also fail with `-EINVAL` from
  the core before the adapter is called; see "SMBus block transfers".
- The rest is as models expect; see `i2c_transfer_buffer_flags()` in
  `drivers/i2c/i2c-core-base.c` and the helpers in
  `drivers/i2c/i2c-core-smbus.c`.

**Transfer checks and retries**

- Order for `i2c_transfer()`, each step returning before the adapter is called:
  1. `__i2c_lock_bus_helper()`: in atomic mode a failed `i2c_trylock_bus()`
     returns `-EAGAIN`.
  2. `__i2c_transfer()`, `master_xfer` is NULL: `-EOPNOTSUPP`.
  3. `WARN_ON(!msgs || num < 1)`: `-EINVAL`.
  4. `__i2c_check_suspended()` in `drivers/i2c/i2c-core.h`: `-ESHUTDOWN`.
  5. `adap->quirks` set and `i2c_check_for_quirks()` fails: `-EOPNOTSUPP`.
- Steps 2 to 5 are in `__i2c_transfer()`, so a caller that holds the lock and
  calls it directly, as `__i2c_mux_master_xfer()` does, gets them too.
- Step 1 `-EAGAIN`: comes from outside the retry loop and is never retried.
- Step 2 tests `master_xfer` only; an adapter that sets only
  `master_xfer_atomic` fails every transfer with `-EOPNOTSUPP`.
- The adapter pointer is not tested; `__i2c_transfer()` dereferences it first.
- `retries`: the core never gives it a default. Of `retries` and `timeout`,
  `i2c_register_adapter()` defaults only `timeout` (to `HZ` when 0).
- `retries` of 0: one attempt, so `-EAGAIN` from the callback goes straight
  back to the caller.
- `retries` is set by whoever fills in the adapter; search for `retries =`.
  For example the `I2C_RETRIES` ioctl in `drivers/i2c/i2c-dev.c` sets it,
  `__i2c_bit_add_bus()` in `drivers/i2c/algos/i2c-algo-bit.c` overwrites it
  with 3, and `i2c_mux_add_adapter()` and `i2c_atr_add_adapter()` copy the
  parent's.
- `timeout` in the core: compared only after a callback has returned
  `-EAGAIN`; the core does not bound one callback invocation with it.

**Adapter quirks**

- `i2c_check_for_quirks()`: one caller, `__i2c_transfer()`. The atomic
  callback is chosen after the check, so atomic transfers are checked too.
- `I2C_AQ_NO_CLK_STRETCH` and `I2C_AQ_NO_REP_START`: `i2c_check_for_quirks()`
  tests neither, and no code in this tree reads either flag; adapter drivers
  only set them.
- `max_comb_1st_msg_len`, `max_comb_2nd_msg_len`, `I2C_AQ_COMB_WRITE_FIRST`,
  `I2C_AQ_COMB_READ_SECOND`, `I2C_AQ_COMB_SAME_ADDR`: tested only when
  `I2C_AQ_COMB` is set and `num == 2`.
- In that same case `max_read_len` and `max_write_len` are not tested.
- `I2C_AQ_COMB` with `num` above 2: fails as "too many messages", whatever
  `max_num_msgs` says.
- `I2C_M_RECV_LEN` message: only the `len` the caller passed is compared with
  `max_read_len`; the bytes the device adds are not.
- Mux and ATR children: `i2c_mux_add_adapter()` and `i2c_atr_add_adapter()`
  copy the parent's `quirks` pointer, so a transfer on a child is checked on
  the child and again on the parent.

**Native SMBus and emulation**

- `__i2c_smbus_xfer()` starts with `__i2c_check_suspended()`: `-ESHUTDOWN`,
  neither the callback nor the emulation runs.
- Callback choice in atomic mode (`i2c_in_atomic_xfer_mode()`):
  - `smbus_xfer_atomic` set: it is called.
  - `smbus_xfer_atomic` NULL, `master_xfer_atomic` set: the native callback is
    skipped and the transaction is emulated, even if `smbus_xfer` is set.
  - both NULL: the non-atomic `smbus_xfer` is called if set, as outside
    atomic mode.
- Fallback to `i2c_smbus_xfer_emulated()`: only when the native callback
  returned `-EOPNOTSUPP` and `master_xfer` is non-NULL; with `master_xfer`
  NULL the `-EOPNOTSUPP` is returned.
- The fallback test runs after the retry loop; a native `-EAGAIN` that
  outlasts the retries is returned, not emulated.
- `I2C_FUNC_SMBUS_PEC`: the core never tests it. With `I2C_CLIENT_PEC` set the
  emulation adds and checks PEC whatever the adapter advertises, except for
  `I2C_SMBUS_QUICK` and `I2C_SMBUS_I2C_BLOCK_DATA`, and the native callback
  just receives the flag.
- Emulated block read with PEC: the read message reaches the adapter with
  `len` 2 and `I2C_CLIENT_PEC` still set in its `flags`.
- `i2c_smbus_check_pec()` takes the byte at the final `msg->len - 1` as the
  PEC, so the adapter must leave `msg->len` at count byte + data + PEC;
  for example `aspeed_i2c_master_irq()` in `drivers/i2c/busses/i2c-aspeed.c`
  tests `I2C_CLIENT_PEC` to do so.

**SMBus block transfers**

- `__i2c_smbus_xfer()` checks the caller's length itself: `data->block[0]` of
  0 or above `I2C_SMBUS_BLOCK_MAX` returns `-EINVAL`.
- The check covers `I2C_SMBUS_I2C_BLOCK_DATA` in both directions,
  `I2C_SMBUS_BLOCK_PROC_CALL`, and `I2C_SMBUS_BLOCK_DATA` writes; an
  `I2C_SMBUS_BLOCK_DATA` read is exempt because `block[0]` is output there.
- The check runs after `__i2c_check_suspended()` and before the tracepoints,
  the native callback and the emulation, so the adapter never sees such a
  length on either path.
- It also covers callers that skip the helpers: `i2c_smbus_xfer()`, the
  `I2C_SMBUS` ioctl in `drivers/i2c/i2c-dev.c`, and direct callers of
  `__i2c_smbus_xfer()`.

| Helper | Length above 32 | Length 0 |
|---|---|---|
| `i2c_smbus_write_block_data()` | clamped to 32, returns 0 on success | `-EINVAL` |
| `i2c_smbus_read_i2c_block_data()` | clamped to 32 | `-EINVAL` |
| `i2c_smbus_write_i2c_block_data()` | clamped to 32, returns 0 on success | `-EINVAL` |

- The helpers do not test for 0 themselves; the `-EINVAL` in the table comes
  from `__i2c_smbus_xfer()`.
- `i2c_smbus_xfer_emulated()`: static, one caller, `__i2c_smbus_xfer()`; the
  lengths its own "Invalid block ... size" tests reject have already been
  rejected, so those tests are not what a caller hits.
- Device-announced length, emulated path: after the transfer the core tests
  only `msg[1].buf[0] > I2C_SMBUS_BLOCK_MAX` (`-EPROTO`).
- An announced count of 0 passes the core, and
  `i2c_smbus_read_block_data()` then returns 0, unless the adapter's transfer
  callback rejected it; for example `readbytes()` in
  `drivers/i2c/algos/i2c-algo-bit.c` returns `-EPROTO` for 0.

## Bus locking and context

**Bus locks**

- Drivers install their own `struct i2c_lock_operations` too, by setting
  `lock_ops` before they register the adapter; search for `lock_ops = &`. For
  example `i2c_gpio_lock_ops` in `drivers/i2c/busses/i2c-gpio.c` and
  `drm_dp_i2c_lock_ops` in `drivers/gpu/drm/display/drm_dp_helper.c`.
- `i2c_atr_lock_ops` in `drivers/i2c/i2c-atr.c`: set on each ATR child
  adapter; takes only the `lock` mutex of `struct i2c_atr`, ignores the flag
  and never locks the parent, so `I2C_LOCK_ROOT_ADAPTER` on an ATR child does
  not lock the root adapter.
- `bus_lock` is not the bus lock of every adapter: `drm_dp_i2c_lock_ops`
  takes `hw_mutex` of `struct drm_dp_aux`, `gmbus_lock_ops` and
  `i2c_atr_lock_ops` take a mutex of their own. Code outside an adapter's own
  lock ops has to lock through `i2c_lock_bus()`.
- What each flag takes, per lock ops:

| `lock_ops` | `I2C_LOCK_SEGMENT` | `I2C_LOCK_ROOT_ADAPTER` |
|---|---|---|
| `i2c_adapter_lock_ops` (default) | own `bus_lock` | own `bus_lock` |
| `i2c_mux_lock_ops` (mux-locked child) | parent's `mux_lock` only | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag |
| `i2c_parent_lock_ops` (parent-locked child) | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag | parent's `mux_lock`, then `i2c_lock_bus()` on the parent with the same flag |

- Flag test: among the lock ops in `drivers/i2c/`, only `i2c_mux_lock_ops`
  tests the flag; `i2c_parent_lock_ops` forwards it unchanged and the others
  ignore it.
- Mux child's own `bus_lock`: taken by neither mux lock ops.

**Mux-locked and parent-locked multiplexers**

- `I2C_MUX_LOCKED` passed to `i2c_mux_alloc()`: makes the mux mux-locked;
  without it `mux_locked` starts as 0, which is parent-locked.
- `mux_locked` in `struct i2c_mux_core`: this is what `i2c_mux_add_adapter()`
  reads. `i2c_mux_gpio_probe()`, `i2c_mux_pinctrl_probe()` and `i2c_mux_probe()`
  in `drivers/i2c/muxes/i2c-mux-gpmux.c` call `i2c_mux_alloc()` with flags 0
  and then set the field directly, so a search for `I2C_MUX_LOCKED` does not
  find every mux-locked mux.
- Lock held by a mux-locked mux: `mux_lock` in the parent's
  `struct i2c_adapter`. `struct i2c_mux_core` has no lock of its own.
- Parent's `mux_lock`: taken first by both kinds, so a transfer through any
  mux child of the same parent, of either kind, is locked out for the whole
  select, transfer, deselect.
- Lock held by a parent-locked mux: the parent's `mux_lock` plus the parent
  locked with `I2C_LOCK_SEGMENT` (see the table in "Bus locks"). This reaches
  the root's bus lock only when every adapter between the mux and the root is
  a parent-locked child.
- Parent-locked mux below a mux-locked one: the lock chain stops at a
  `mux_lock` and the root is not locked, so traffic to devices directly on
  the root can run between select and the transfer.
- Parent-locked select that calls into gpio, pinctrl or regmap: any transfer
  those cause on the locked parent must be unlocked too, or it deadlocks; see
  PL2 in `Documentation/i2c/i2c-topology.rst`. `i2c_mux_gpio_probe()` avoids
  this by choosing mux-locked when every GPIO sits behind the same root
  adapter as the mux.

**Atomic transfers**

- Context test in `i2c_in_atomic_xfer_mode()`: `!preemptible()` only with
  `CONFIG_PREEMPT_COUNT`; without it the test is `irqs_disabled()` alone, so a
  context with preemption disabled and interrupts on is not atomic mode.
- `SYSTEM_SUSPEND` is above `SYSTEM_RUNNING`: the interrupts-off part of
  suspend and hibernation is atomic mode too, not only halt, power-off and
  restart; see `suspend_enter()` in `kernel/power/suspend.c`.
- Adapter with no atomic callback: `__i2c_lock_bus_helper()` issues a `WARN()`
  and continues; `__i2c_transfer()` then calls the sleeping `master_xfer`. The
  missing atomic callback does not give `-EOPNOTSUPP`; `__i2c_transfer()`
  returns that when `master_xfer` is NULL.
- The `WARN()` fires only when both `master_xfer_atomic` and
  `smbus_xfer_atomic` are NULL: an adapter with only `smbus_xfer_atomic` gets
  no warning from `i2c_transfer()` in atomic mode and still runs
  `master_xfer`.
- `__i2c_transfer()` and `__i2c_smbus_xfer()` called directly: they pick the
  atomic callback, but the `WARN()` and the trylock are only in
  `__i2c_lock_bus_helper()`, so such callers get neither.

**Unlocked transfer functions**

- **Potentially unsafe usage**: calling `__i2c_transfer()` or
  `__i2c_smbus_xfer()` from outside the core.
  - Unsafe: when the calling task does not hold the bus lock of the adapter it
    passes while another task can transfer on that adapter; neither function
    locks that adapter, so two `master_xfer` calls run at once.
  - Unsafe: on `muxc->parent` from the select or deselect of a mux-locked mux
    that has not locked the parent itself; the core holds only the parent's
    `mux_lock` there, not its bus lock.
  - Safe: between `i2c_lock_bus(adap, I2C_LOCK_SEGMENT)` and
    `i2c_unlock_bus()` on the same adapter, as `regmap_sccb_read()` in
    `drivers/base/regmap/regmap-sccb.c` and `iic_tpm_read()` in
    `drivers/char/tpm/tpm_i2c_infineon.c` do; this is the lock
    `i2c_transfer()` takes around `__i2c_transfer()`.
  - Safe: on `muxc->parent` from the select or deselect of a parent-locked
    mux when the mux core calls it; `i2c_parent_lock_bus()` or
    `i2c_parent_trylock_bus()` has locked the parent before
    `__i2c_mux_master_xfer()` or `__i2c_mux_smbus_xfer()` runs.
    `pca954x_select_chan()` and `mlxcpld_mux_select_chan()` do this.
  - Safe: the same callback or its helper called by the driver itself,
    outside a child transfer, after the driver locks the parent with
    `i2c_lock_bus()`: `idle_state_store()` in
    `drivers/i2c/muxes/i2c-mux-pca954x.c` and `pca9541_probe()`.
- `pca954x_reg_write()` in `drivers/i2c/muxes/i2c-mux-pca954x.c`: calls
  `__i2c_smbus_xfer()`; that file has no call to `__i2c_transfer()`, and there
  is no pca954x_regw() here.
- `drivers/media/dvb-frontends/rtl2830.c`: the regmap bus callbacks, for
  example `rtl2830_regmap_read()`, call `__i2c_transfer()` with no locking of
  their own; wrappers such as `rtl2830_update_bits()` take the lock, and
  `rtl2830_select()` calls regmap bare because the core already holds it.
- `drivers/media/dvb-frontends/rtl2832.c`: a mux-locked mux; it calls neither
  `i2c_lock_bus()` nor `__i2c_transfer()`.
- `drivers/mfd/88pm860x-i2c.c`: takes the bus lock but calls
  `adap->algo->master_xfer()` directly, so it skips the suspend check, the
  quirk check and the retry loop of `__i2c_transfer()`; it is not an example
  of the unlocked functions.

## Clients, drivers and adapters

**Driver callback signatures**

- Models have the helpers right; see `i2c_client_get_device_id()` and
  `i2c_get_match_data()` in `drivers/i2c/i2c-core-base.c`.
- Client without a firmware node (sysfs `new_device`, board info) bound
  through `of_match_table` (`CONFIG_OF`): `i2c_of_match_device()` falls back
  to `i2c_of_match_device_sysfs()` in `drivers/i2c/i2c-core-of.c`, which
  compares `client->name` with the compatible strings, with and without the
  vendor prefix.
- For such a client `i2c_get_match_data()` never returns the
  `of_match_table` `.data`: `device_get_match_data()` gives NULL, so the result
  is the `id_table` `driver_data` for that name, or NULL when `id_table` is
  absent or lacks the name.

**Ways to create a client**

- Every registered client is created by `i2c_new_client_device()`; the rows
  below are the ones easy to miss.

| Way | Goes through | Who unregisters |
|---|---|---|
| SMBus alert, automatic | `i2c_setup_smbus_alert()` from `i2c_register_adapter()`, when the parent has interrupt name "smbus_alert" or property "smbalert-gpios" (`CONFIG_I2C_SMBUS`) | core, in `i2c_deregister_clients()` |
| Host-notify target | `i2c_new_slave_host_notify_device()` in `drivers/i2c/i2c-smbus.c` | caller, with `i2c_free_slave_host_notify_device()`, which also unregisters the slave callback and frees the platform data |
| Extra ACPI I2cSerialBus resource | `i2c_acpi_new_device_by_fwnode()` | caller, with `i2c_unregister_device()` |

- Detected clients: kept on `driver->clients`; sysfs clients: kept on
  `adap->userspace_clients`; both linked through `client->detected`. There are
  no I2C_CLIENT_AUTO or I2C_CLIENT_USER flags.
- `i2c_deregister_clients()`: unregisters every child client of the adapter,
  caller-owned ones included; clients named "dummy" go in the second pass.
- Static board info: scanned whenever `adap->nr` is below
  `__i2c_first_dynamic_bus_num`; that includes adapters numbered by a DT
  "i2c" alias through `i2c_add_adapter()`.
- `i2c_detect()` runs for each adapter and driver pair, from
  `__process_new_adapter()` and `__process_new_driver()`, and probes only when
  all hold:
  - the driver has both `detect` and `address_list`;
  - `adapter->class` is not exactly `I2C_CLASS_DEPRECATED`;
  - `adapter->class & driver->class` is non-zero.
- `I2C_CLASS_HWMON` is the only class bit defined besides
  `I2C_CLASS_DEPRECATED`.
- Mux channel adapters: `i2c_mux_add_adapter()` in `drivers/i2c/i2c-mux.c`
  never sets `class`, so they are not probed.
- `i2c_detect()` makes no functionality test of its own; the presence probe is
  `i2c_default_probe()`, run by the core in `i2c_detect_address()` before
  `driver->detect` is called. It picks its method with
  `i2c_check_functionality()` and reports nothing present when the adapter
  supports no suitable method.

**Client creation checks**

- `i2c_check_addr_validity()` is the only address validity test: 7-bit 0x00 or
  above 0x7f, and 10-bit above 0x3ff, give -EINVAL.
- Reserved 7-bit addresses (0x01-0x07, 0x78-0x7f) are accepted without a
  warning; `i2c_new_client_device()` does not call
  `i2c_check_7bit_addr_validity_strict()`.
- `I2C_CLIENT_TEN` on an adapter without `I2C_FUNC_10BIT_ADDR`: accepted;
  `drivers/i2c/i2c-core-base.c` never tests that bit.
- `i2c_lock_addr()`: -EBUSY when the same number is being instantiated on the
  same adapter; it returns without the "Failed to register" message.
- `i2c_lock_addr()` covers every request without `I2C_CLIENT_TEN`,
  `I2C_CLIENT_SLAVE` included, and keys on the raw `addr`, not the encoded
  one.
- `i2c_lock_addr()` bit is held until `device_register()` returns, so across a
  synchronous driver probe of the new client.
- `i2c_check_addr_busy()` upward: only clients attached directly to each
  ancestor adapter, for as long as `i2c_parent_is_i2c_adapter()` finds a
  parent adapter.
- `i2c_check_addr_busy()` downward: the clients of the adapter and,
  recursively, of its child adapters; `i2c_check_mux_children()` descends only
  into a child whose `dev->type` is `i2c_adapter_type`, so an adapter that
  hangs under a client device, as the ATR channels of
  `drivers/misc/ti_fpc202.c` do, is not reached.
- Sibling branches of a mux are not checked; the same address on two channels
  is accepted.
- Without `CONFIG_I2C_MUX`, `i2c_parent_is_i2c_adapter()` returns NULL and
  there is no upward walk.

**Unregistering a failed client**

- Models have this right; see `i2c_unregister_device()` in
  `drivers/i2c/i2c-core-base.c`.

**Probe and remove sequence**

- `client->irq`: reloaded from `client->init_irq` at the start of every probe;
  the lookup runs only when that is 0.
- OF IRQ lookup: `fwnode_irq_get_byname()` for "irq", then `fwnode_irq_get()`
  index 0 when that returned -EINVAL or -ENODATA.
- Wake IRQ setup: keyed on `I2C_CLIENT_WAKE` in `client->flags`, not on a
  property read in probe; the ACPI IRQ lookup can set the flag during probe.
- `client->debugfs`: directory created under `client->adapter->debugfs` just
  before the driver's probe.
- `dev_pm_domain_attach()`: called with `PD_FLAG_DETACH_POWER_OFF`.
- `i2c_device_remove()` does not call `dev_pm_domain_detach()`;
  `device_unbind_cleanup()` in `drivers/base/dd.c` does, after
  `devres_release_all()`, on unbind and on failed probe.
- `i2c_device_remove()` after the driver's remove, in order:
  1. `debugfs_remove_recursive()` on `client->debugfs`;
  2. `devres_release_group()` on `client->devres_group_id`;
  3. `dev_pm_clear_wake_irq()`, then `device_init_wakeup()` with false;
  4. `client->irq = 0`;
  5. `pm_runtime_put()` on the adapter if `I2C_CLIENT_HOST_NOTIFY`.
- Device-managed resources: released inside `i2c_device_remove()`, in step 2,
  after the driver's remove returns, before the wake IRQ is cleared and before
  the driver core detaches the PM domain.
- Failed driver probe: `i2c_device_probe()` undoes steps 1 to 3 and the
  adapter runtime PM reference, but leaves `client->irq` set.

**Lookup references**

- Models have this right; see `i2c_get_adapter_by_fwnode()` and
  `i2c_put_adapter()` in `drivers/i2c/i2c-core-base.c`, and the wrappers in
  `include/linux/i2c.h`.

**Adapter registration and removal**

- `i2c_del_adapter()` start: replaces the adapter's `i2c_adapter_idr` slot with
  NULL, so `i2c_get_adapter()` fails from then on; the number is freed only
  after the wait.
- `memset()` of `adap->dev` after the wait also clears `dev.parent`, the
  firmware node pointers and the drvdata: `i2c_get_adapdata()` returns NULL
  after `i2c_del_adapter()`, and `dev.parent` is NULL on a re-add unless the
  driver sets it again.
- Adapter memory must be zeroed before the first registration: the core never
  initialises `addrs_in_instantiation`, and a stale bit makes
  `i2c_lock_addr()` return -EBUSY for that address.
- **Potentially unsafe usage**: registering the adapter with
  `devm_i2c_add_adapter()`.
  - Unsafe: when the driver's remove callback disables something the transfer
    path needs (clock, IRQ, runtime PM, reset); `devm_i2c_del_adapter()` runs
    only after remove returns, and client remove callbacks inside
    `i2c_del_adapter()` still transfer.
  - Safe: when no remove callback tears down anything the transfer path needs,
    because all of it was acquired through devres before
    `devm_i2c_add_adapter()`, as `hisi_i2c_probe()` in
    `drivers/i2c/busses/i2c-hisi.c` does (that driver has no remove
    callback); `release_nodes()` in `drivers/base/devres.c` releases in
    reverse order, so the adapter goes first.
  - Safe: `i2c_add_adapter()` with `i2c_del_adapter()` as the first step of
    remove, as `meson_i2c_remove()` in `drivers/i2c/busses/i2c-meson.c` does;
    `i2c_deregister_clients()` runs the client removes there.

**Adapter registration checks**

- There is no __i2c_add_numbered_adapter() here; `i2c_allocate_adapter_id()` in
  `drivers/i2c/i2c-core-base.c` allocates the number, called from
  `i2c_register_adapter()`.
- `i2c_add_adapter()`: overwrites `adapter->nr` with the "i2c" alias id or -1,
  then calls `i2c_register_adapter()`; a number preset by the driver is lost.
- `devm_i2c_add_adapter()` goes through `i2c_add_adapter()`, so it cannot take
  a number preset by the driver.
- Checks at the start of `i2c_register_adapter()`, in order:

| Check | Result |
|---|---|
| `is_registered` false (core not initialised) | -EAGAIN, `WARN_ON()` |
| `adap->name[0]` empty | -EINVAL, `WARN()` |
| `adap->algo` NULL | -EINVAL, `pr_err()` |

- Transfer callbacks (`xfer`, `smbus_xfer`): no test and no warning.
- `algo->functionality`: not tested, but called during registration by
  `i2c_setup_host_notify_irq_domain()`; NULL oopses inside
  `i2c_register_adapter()`.
- `retries`, `owner`, `dev.parent`, `class`, `quirks`: neither checked nor
  defaulted; only `lock_ops` and `timeout` get defaults.
- `i2c_allocate_adapter_id()`: runs after the field checks and the host-notify
  domain setup; failure is logged with `pr_err()`.
- `i2c_allocate_adapter_id()` with a fixed `nr` already taken: -EBUSY; the
  -ENOSPC from `idr_alloc()` is translated only when `nr` is not -1.
- `i2c_init_recovery()`: only -EPROBE_DEFER fails registration; its -EINVAL
  for incomplete `bus_recovery_info` is ignored and the pointer is set to NULL.
- `i2c_setup_smbus_alert()` failure (`CONFIG_I2C_SMBUS`): fails registration
  after `device_add()`; already created clients are removed with
  `i2c_deregister_clients()`.
- Failures before `i2c_allocate_adapter_id()` return without touching
  `i2c_adapter_idr`; later ones remove the id.

## Core build configurations

**Stubs, target-mode guards and tests**

- `include/linux/i2c.h` has three `#if IS_ENABLED(CONFIG_I2C)` blocks; in
  them only these names have an `#else` stub, all returning `NULL`:
  `i2c_verify_client()`, `i2c_find_device_by_fwnode()`,
  `i2c_find_adapter_by_fwnode()`, `i2c_get_adapter_by_fwnode()`.
- `i2c_get_adapter()`, `i2c_put_adapter()`: prototypes inside the guard, no
  stub.
- `module_i2c_driver()`, `builtin_i2c_driver()`, `i2c_add_driver()`: defined
  inside the guard, so they do not exist without `CONFIG_I2C`.
- Inline helpers inside the guard, absent without `CONFIG_I2C`: for example
  `i2c_8bit_addr_from_msg()`, `i2c_check_functionality()`,
  `i2c_check_quirks()`, `i2c_client_has_driver()`, `i2c_master_send()`.
- Inline helpers outside any guard: for example `i2c_get_clientdata()`,
  `i2c_lock_bus()`, `i2c_mark_adapter_suspended()`.
- Unguarded prototypes with no stub, which compile without `CONFIG_I2C` and
  fail at link: `i2c_verify_adapter()`, `i2c_match_id()`,
  `i2c_get_match_data()`, `i2c_recover_bus()`, `i2c_generic_scl_recovery()`,
  `i2c_for_each_dev()`, and the externs `i2c_bus_type`, `i2c_adapter_type`,
  `i2c_client_type`.
- `i2c_of_match_device()`: not in `include/linux/i2c.h`; it is in
  `drivers/i2c/i2c-core.h` under `#ifdef CONFIG_OF`, stub returns `NULL`.
- OF block: guard is `IS_ENABLED(CONFIG_OF)` alone, with no test of
  `CONFIG_I2C`.
- `of_i2c_get_board_info()`: with `CONFIG_OF` on it is a bare prototype,
  defined in `drivers/i2c/i2c-core-of.c`; with `CONFIG_OF` on and
  `CONFIG_I2C` off a caller fails at link.
- ACPI block: guard is `IS_REACHABLE(CONFIG_ACPI) && IS_REACHABLE(CONFIG_I2C)`,
  the only `IS_REACHABLE()` guard in the header.
- `i2c_acpi_new_device_by_fwnode()` stub: returns `ERR_PTR(-ENODEV)`;
  `i2c_acpi_find_adapter_by_handle()` stub: returns `NULL`.
- `CONFIG_I2C_BOARDINFO`: a promptless bool with `default y` inside `if I2C`
  in `drivers/i2c/Kconfig`; the header tests it with `#ifdef`.
- `i2c_slave_register()`, `i2c_slave_unregister()`, `i2c_slave_event()`:
  prototypes are unguarded and have no stub; a caller built with
  `CONFIG_I2C_SLAVE` off compiles and fails at link.
- `enum i2c_slave_event` and the `i2c_slave_cb_t` typedef: unguarded.
- `i2c_detect_slave_mode()`: the only target-mode function in
  `include/linux/i2c.h` with a stub; under
  `#if IS_ENABLED(CONFIG_I2C_SLAVE)`, the `#else` stub returns `false`.
- `slave_cb` in `struct i2c_client`: exists only under
  `#if IS_ENABLED(CONFIG_I2C_SLAVE)`.
- `drivers/i2c/i2c-core-slave.c`: added by `i2c-core-$(CONFIG_I2C_SLAVE)` in
  `drivers/i2c/Makefile`, so it is linked into `i2c-core.o`, not built as its
  own module.
- **Potentially unsafe usage**: a bus driver setting `reg_slave`,
  `unreg_slave`, `reg_target` or `unreg_target` in its
  `struct i2c_algorithm`.
  - Unsafe: when the initialisers can be compiled with `CONFIG_I2C_SLAVE`
    off; the members do not exist and the build fails.
  - Safe: the driver's Kconfig entry has `select I2C_SLAVE`, as `I2C_RCAR` in
    `drivers/i2c/busses/Kconfig`; `drivers/i2c/busses/i2c-rcar.c` has no
    `#if` around its initialisers.
  - Safe: the initialisers and callbacks are inside
    `#if IS_ENABLED(CONFIG_I2C_SLAVE)`, as in
    `drivers/i2c/busses/i2c-aspeed.c`.
  - Safe: the initialisers and callbacks are inside `#ifdef` of a driver
    option that has `select I2C_SLAVE`, as `CONFIG_I2C_PXA_SLAVE` in
    `drivers/i2c/busses/i2c-pxa.c`.
  - Safe: the initialisers are in a file that the Makefile builds only for a
    driver option that has `select I2C_SLAVE`, as
    `drivers/i2c/busses/i2c-at91-slave.c` for
    `CONFIG_I2C_AT91_SLAVE_EXPERIMENTAL`.
- `CONFIG_I2C_STUB`: has `depends on m`, so `drivers/i2c/i2c-stub.c` is never
  built in.
- KUnit: no suite under `drivers/i2c/`, but KUnit tests elsewhere fill in
  `struct i2c_adapter` and `struct i2c_algorithm` themselves, for example
  `drivers/gpu/drm/tests/drm_connector_test.c` and
  `drivers/gpu/drm/amd/display/amdgpu_dm/tests/amdgpu_dm_hdcp_test.c`.
- `drivers/of/unittest.c`: fills in its own `struct i2c_adapter`,
  `struct i2c_algorithm` and `struct i2c_driver` under
  `IS_BUILTIN(CONFIG_I2C)` and `CONFIG_OF_OVERLAY`.
- Rust: `rust/bindings/bindings_helper.h` includes `include/linux/i2c.h`;
  `rust/kernel/i2c.rs` is compiled only for `CONFIG_I2C = "y"` and writes
  `struct i2c_driver` members by name; `SAMPLE_RUST_DRIVER_I2C` and
  `SAMPLE_RUST_I2C_CLIENT` in `samples/rust/Kconfig` have `depends on I2C=y`.
- `include/trace/events/i2c_slave.h`: third tracepoint header of the I2C
  core, instantiated with `CREATE_TRACE_POINTS` in
  `drivers/i2c/i2c-core-slave.c`, so it is compiled only with
  `CONFIG_I2C_SLAVE`.
- `include/trace/events/i2c_slave.h` names the `enum i2c_slave_event` values
  in three places: the `TRACE_DEFINE_ENUM()` lines, `show_event_type()`, and
  the `switch` in `TP_fast_assign()` that decides whether `val` is copied; a
  new value falls to `default` and records no byte.
- `include/trace/events/smbus.h`: repeats the `I2C_SMBUS_*` protocol table in
  each of its four events and sizes `buf` as `I2C_SMBUS_BLOCK_MAX + 2` in
  three of them.

## Conventions

**Conventions for new code**

These are conventions that the maintainers of the I2C subsystem ask for. No
code in a kernel tree states them, so they are kept by hand and inserted as
they are.

- A driver must declare an initialized array of `struct i2c_device_id` const.
- New or changed entries of such an array should use named initializers.
  Positional entries in existing tables are not bugs.

## Model gaps

### Other mistakes models make

- Models do not know that `i2c_new_client_device()` takes its own reference
  on `info->fwnode` with `fwnode_handle_get()`. `i2c_unregister_device()`
  drops it, except for a software node, which `device_remove_software_node()`
  releases.
- Models do not know `client->debugfs`: the core removes the directory
  recursively in `i2c_device_remove()` and on a failed probe, so a driver
  need not remove what it created there.
- Models do not know that `i2c_device_shutdown()` calls `disable_irq()` on
  `client->irq` when the bound driver has no `shutdown` callback and
  `client->irq` is above 0.
- Models take `i2c_register_spd_write_disable()` to instantiate every SPD
  type. It does not instantiate `spd5118` devices; see `i2c_register_spd()`
  in `drivers/i2c/i2c-smbus.c`.
- Models do not know that `struct i2c_board_info` has no `of_node` member: a
  device tree node is passed in `fwnode`, as `of_i2c_get_board_info()` does
  with `of_fwnode_handle()`.
- Models do not know that `drivers/i2c/i2c-atr.c` exports into the `"I2C_ATR"`
  namespace and `drivers/i2c/i2c-core-of-prober.c` into `"I2C_OF_PROBER"`: a
  module that calls them needs the matching `MODULE_IMPORT_NS()`.
- Models do not know `kzalloc_obj()`, `kzalloc_flex()` and `kmalloc_objs()`,
  which code in `drivers/i2c/` uses to allocate; they are defined in
  `include/linux/slab.h`.
- Models do not know `trace_call__i2c_slave()`, which `i2c_slave_event()`
  calls after testing `trace_i2c_slave_enabled()`; `include/linux/tracepoint.h`
  generates it for each tracepoint.
