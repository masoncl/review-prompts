# What the hid measurement found

Three models were asked the 89 questions in `hid-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C said they assumed
kernels around 6.12 and knew the subject well in outline: the bus, the parser's
structures, the three-way returns of the mapping callbacks, the descriptor
fixup contract and the usual probe and remove sequence came back almost
untouched, and reader C needed the fewest corrections. Reader B said 6.10 to
6.12 but answered from something older and was wrong about fundamentals. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted near the end.

What the two current readers got wrong is mostly what moved in the last few
releases: the buffer size that now travels down the input path, what the core
does about the input lock at stop and on a failed probe, where the HID-BPF
descriptor fixup runs, and the battery list.

## What all three readers got wrong

Reader B is wrong in its own way on most of these; where it matters the bullet
says who said what.

- **The safe input entry point and short reports.** None knew
  `hid_safe_input_report()`: two said so and one doubted it exists. Readers A
  and C said a report shorter than the descriptor declares is always zero
  padded (reader A, that the padding overruns the buffer), and reader B that it
  is clamped and processed. `hid_report_raw_event()` now takes the buffer size
  as well as the data size: it returns `-EINVAL` when the buffer is smaller
  than the report the descriptor declares and pads only when the buffer is
  large enough. `hid_input_report()` passes the data size for both, so a short
  report that comes in through it is dropped. usbhid, i2c-hid and uhid call the
  safe form; every other transport calls the old one. The same mistake leaked
  into each reader's answers on the input path, on `raw_event` and on the
  change checklist. This one changes a verdict.
- **The input lock at stop and on a failed probe.** Readers A and C said
  `hid_hw_stop()` does nothing about `driver_input_lock` and that a driver which
  called `hid_device_io_start()` must call `hid_device_io_stop()` itself before
  failing probe; reader B had a mutex that the core toggles around the
  callbacks. `hid_hw_stop()` calls `hid_device_io_stop()` when `io_started` is
  set, before `hid_disconnect()`, and `__hid_device_probe()` does the same on
  failure before `devres_release_group()`. Nothing else in the core starts or
  stops input for the driver.
- **Where the HID-BPF descriptor fixup runs.** All three put it in
  `hid_open_report()`, and reader A in `hid_add_device()` as well. It is
  `call_hid_bpf_rdesc_fixup()` in `__hid_device_probe()`, run while `bpf_rsize`
  is 0 (the first probe, and again after `hid_bpf_reconnect()` has reset it),
  before the match; `hid_open_report()` starts from `bpf_rdesc` and copies only
  when the driver has a `report_fixup`, so `rdesc` may be the same pointer as
  `bpf_rdesc` or `dev_rdesc`.
- **Reports while nobody has the device open.** Readers A and C said
  `HID_QUIRK_ALWAYS_POLL` keeps USB reports flowing. The URB keeps polling but
  `hid_irq_in()` drops each report while `HID_OPENED` is clear. Reader A said
  i2c-hid delivers while closed and reader B that it leaves the device asleep;
  `i2c_hid_get_input()` reads the report and drops it unless `I2C_HID_STARTED`
  is set.
- **Assuming an input device.** All three offered `list_empty(&hdev->inputs)` as
  the check, and two said `field->hidinput` is NULL for a field that was not
  mapped. `hdev->inputs` is initialised only inside `hidinput_connect()`, so on
  a device that never connected hid-input the test reads a zeroed list head,
  and `hidinput_configure_usage()` sets `field->hidinput` for every input and
  output field before it decides to ignore the usage. The test is
  `HID_CLAIMED_INPUT`. `hid_hw_start()` can succeed with no input device when
  hidraw, hiddev, `HID_CONNECT_DRIVER` or a `raw_event` callback is there.
- **What is unsafe in remove.** Readers A and C blamed `raw_event` arriving
  during `remove`. `hid_device_remove()` holds `driver_input_lock`, so
  `__hid_input_report()` returns `-EBUSY`; what can still reach driver state
  until `hid_hw_stop()` are the callbacks of the listeners (input, LED,
  hidraw, `on_hid_hw_close`). Readers A and B cited `hidpp_remove()` for
  cancelling work before the stop; it stops first and cancels after.
- **KUnit tests.** Two listed only the uclogic files and one said there are
  none. `CONFIG_HID_KUNIT_TEST` also builds `hid-input-test.c`, included from
  `hid-input.c`, and `hid-uclogic-core-test.c`; hid-roccat-kone and hid-hyperv
  have options of their own.
- **Force feedback and the force bits.** All three had `ff_init` running once
  input is claimed or when force-feedback usages are present. It is called
  inside `hidinput_connect()` for the first input device, before it is
  registered, when `HID_CONNECT_FF` is set. Readers A and B had
  `HID_CONNECT_HIDINPUT_FORCE` creating an input device regardless; it only
  skips the test for an input application collection, an input device with no
  capabilities is still dropped, and `HID_QUIRK_HIDINPUT_FORCE` adds only that
  bit.
- **Power management callers.** i2c-hid never calls `hid_driver_resume()`, only
  `hid_driver_reset_resume()`, and surface-hid is the third caller; readers A
  and B missed both and reader C listed intel-thc-hid, which calls none of the
  helpers. A missing `may_wakeup` falls back to `device_may_wakeup()` on the
  parent, or false; reader A said true and reader B that the device cannot
  wake.
- **Locks.** Nobody listed `hid_bpf_input_report()` or the debugfs descriptor
  file as sleepers on `driver_input_lock`, and nobody had the nesting
  `driver_input_lock`, then `minors_rwsem`, then `ll_open_lock`.

## What only some readers got wrong

Readers A and B:

- Where quirk bits are tested. `HID_QUIRK_NO_OUTPUT_REPORTS_ON_INTR_EP` is tested
  in `hidraw_send_report()`, not in usbhid; `HID_QUIRK_SKIP_OUTPUT_REPORTS` only
  in `hid-input.c`; `HID_QUIRK_NOGET` in `__usbhid_submit_report()`.
  HID_QUIRK_NO_EMPTY_INPUT, which reader A listed, is gone.
- `hid_is_usb()` is a static inline. It is declared extern in
  `include/linux/hid.h` and defined in `drivers/hid/usbhid/hid-core.c`, so a
  driver that calls it has to depend on `USB_HID`.
- One battery per device, stored in fields of `struct hid_device`, no helper.
  The tree has `struct hid_battery`, a `batteries` list with one entry per
  report id, devres ownership, and `hid_get_battery()`. Reader C knew the list
  and got the helper's name wrong.
- `hid_alloc_report_buf()` allocates `hid_report_len()` plus 7. It adds one more
  byte when the report id is 0, which `__hid_request()` uses as the id byte.
- Only `struct hid_bpf_ctx` is above the "HID internal" marker in
  `include/linux/hid_bpf.h`; `struct hid_bpf_ops` is below it.
- A dynamic quirk replaces the static tables and the transport's
  `initial_quirks`; it is not ORed with them.
- A negative `input_configured` fails. Any nonzero return unwinds every input
  device.

Readers A and C:

- Only hidp and greybus register a `struct hid_ll_driver` outside
  `drivers/hid/`; reader B named hidp alone. The tree also has
  `drivers/platform/x86/asus-tf103c-dock.c`,
  `drivers/platform/x86/tuxedo/nb04/wmi_ab.c` and `sound/soc/sdca/sdca_hid.c`.
- `__hid_input_report()` with `lock_already_taken` skips locking. It still
  calls `down_trylock()`, and if that succeeds it releases the lock and
  returns `-EINVAL`.
- The list `hid_have_special_driver` only stops the generic driver.
  `hid_set_group()` also skips `hid_scan_report()` for a device on it.

Reader A: `HID_QUIRK_INPUT_PER_APP` wins over `HID_QUIRK_MULTI_INPUT`. The
second is tested first. Reader C: `on_hid_hw_open` fires on the same transition
as the transport's `open`. It is also called when that `open` failed. Reader C
also offered `uclogic_probe()` as the correct way to free an allocated
descriptor; its failure path does not free it.

Reader B, and nobody else: `driver_input_lock` is a mutex, or a spinlock; HID-BPF
attaches tracing programs to hook functions and has a jump table file; a
driver with no `remove` gets no `hid_hw_stop()`; a positive return from
`raw_event` stops processing; `report_table` filters by report id;
`HID_QUIRK_MULTI_INPUT` splits by application; `HID_MAX_BUFFER_SIZE` is 4096;
`hid_parse_report()` builds the report tree; the documentation and
`hid_hw_open()` agree about nesting; a new driver must add its ids to
`hid_have_special_driver`; open hidraw files hold a reference on the device;
and a dozen fields, locks and hooks that do not exist.

## What the readers already knew

All three: which file holds what, and where to start reading for each job.
Readers A and C, with little or nothing to correct: the steps of
`hid_hw_start()`, the returns of `raw_event` and `event`, how the field arrays
are sized and that a main item without usages makes no field, what
`hidinput_disconnect()` does, when `input_configured` runs, checking the size in
a descriptor fixup, the context of the event callbacks (reader C), and which
request calls sleep (reader C).

## Where the hand-written guide is stale

Most of what `hid.md` says about the API is still true in this tree: the
`-EINVAL` and `-ENODEV` from `hid_add_device()`, the open count under
`ll_open_lock`, the devres group around probe, the default remove, the three-way
return of `input_mapping`, the copy the core makes of a fixed-up descriptor,
and the dummy `remove` that goes with a devres stop (`hid-mcp2221.c` and
`hid-google-hammer.c` do it). Its `uclogic_probe()` example of a leaked
descriptor is still how that function reads. What is off:

- It states "call `hid_hw_stop()` before cancelling workers" as an absolute.
  `mt_remove()`, `logi_dj_remove()`, `uclogic_remove()` and `sony_remove()` stop
  their timers and work first and are correct, because each makes sure nothing
  can re-arm them (a flag, `timer_shutdown_sync()`, or the input lock the core
  holds during `remove`); the question asks for both orders and the condition.
- It says the I/O lock is released by `hid_device_io_start()`, "automatically
  called by the core after probe returns". The core releases the semaphore
  itself and never calls that function, and the guide says nothing about
  `hid_hw_stop()` and the failed-probe path taking the lock back.
- It tells transports to prefer `hid_safe_input_report()` without the reason
  that now matters: through `hid_input_report()` a short report is dropped.
- It lists BPF among the non-USB transports a driver may be bound to. HID-BPF
  is not a transport; uhid is how a non-USB device arrives with `BUS_USB`.
- It says the device model keeps the `struct hid_device` allocated while
  hidraw nodes exist. `hidraw_disconnect()` destroys the node; an open file
  keeps only the `struct hidraw`, and is kept off the device by the `exist`
  test under `minors_rwsem`.
- It repeats the documentation's "asynchronous" for `output_report`;
  `usbhid_output_report()` is a blocking `usb_interrupt_msg()`.
- Its `REPORT as bugs` lines and "Do NOT report" tell a reviewer what to
  report. The questions ask for unsafe usage and the correct usage that looks
  like it.
- It has no map of the files, nothing on quirks, locks, HID-BPF or the tests.

## What was left out of the build set and why

The hand-written guide is 2,350 words, so forty questions fit. Because reader B
was wrong about fundamentals, they were chosen by importance and by what the
old guide was for, not only by dropping what readers A and C know.

- Left out because readers A and C needed little or no correction: entry
  points, the structures and how field arrays are sized, the limits, the steps
  of `hid_hw_start()`, the returns of `raw_event` and `event`, the parse call,
  the validation helper, `input_configured`, hiding a usage, the size check in
  a fixup, `hidinput_disconnect()`, and which requests sleep.
- Left out for room although readers were wrong: registering a device and the
  registration checks (the transport documentation covers them), the raw
  request and output report contracts (the report id question and the buffer
  question carry the parts that bite), transport power management and driver
  power management, groups and matching, the battery list, uhid, the hidraw
  request paths, the HID-BPF kfuncs, dispatch locking, injection and ABI, the
  quirk flag table, and the two checklists for new code.
- The file table and the tests are kept, short, as pointers.
- The question on `raw_event` data was reworded after the measurement: it
  asked when the zero padding of short reports happens, which presupposes that
  they are padded.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          176        28%     28     30   6.12 to 6.12
reader B          255        76%      2     87   6.10 to 6.12
reader C          140        21%     37     12   6.12 to 7.0

question                          reader A      reader B      reader C   verdict
hid.core-files                     0% ( 2)       9% ( 4)       0% ( 1)   all fair: drop, or shrink to a pointer
hid.layers                        21% ( 1)      57% ( 2)      15% ( 1)   weak: reader B
hid.entry-points                   2% ( 1)       2% ( 1)       5% ( 2)   all fair: drop, or shrink to a pointer
hid.docs                          50% ( 3)      55% ( 1)       2% ( 1)   weak: reader A, reader B
hid.tests                         55% ( 2)      88% ( 2)      37% ( 3)   weak: reader A, reader B
hid.device-struct                 21% ( 8)      78% ( 3)      33% ( 4)   weak: reader B
hid.rdesc-copies                  52% ( 3)      92% ( 2)      35% ( 1)   weak: reader A, reader B
hid.report-structs                 1% ( 0)      64% ( 1)      35% ( 1)   weak: reader B
hid.field-arrays                   0% ( 0)      84% ( 1)      20% ( 1)   weak: reader B
hid.padding-fields                 9% ( 0)      82% ( 1)      11% ( 1)   weak: reader B
hid.report-id-byte                32% ( 3)      87% ( 4)      21% ( 1)   weak: reader B
hid.limits                         3% ( 1)      54% ( 4)      12% ( 2)   weak: reader B
hid.groups                        59% ( 4)      87% ( 2)      20% ( 2)   weak: reader A, reader B
hid.driver-callbacks              10% ( 2)      48% ( 3)      31% ( 4)   weak: reader B
hid.ll-register                   26% ( 3)      74% ( 6)       0% ( 0)   weak: reader B
hid.add-device-checks             20% ( 1)      88% ( 1)       7% ( 1)   weak: reader B
hid.destroy-device                77% ( 3)      86% ( 2)       5% ( 1)   weak: reader A, reader B
hid.ll-free-usage                  4% ( 1)      89% ( 1)       0% ( 0)   weak: reader B
hid.ll-teardown-order             31% ( 1)      80% ( 1)      29% ( 2)   weak: reader B
hid.ll-callbacks                   5% ( 3)      55% ( 7)       6% ( 1)   weak: reader B
hid.ll-parse                      28% ( 2)      60% ( 4)      11% ( 1)   weak: reader B
hid.ll-open-close                 40% ( 1)      92% ( 2)      22% ( 1)   weak: reader A, reader B
hid.ll-raw-request                24% ( 1)      79% ( 1)      14% ( 1)   weak: reader B
hid.ll-output-report              20% ( 1)      80% ( 2)      12% ( 1)   weak: reader B
hid.ll-request-wait               42% ( 3)      78% ( 2)      38% ( 1)   weak: reader A, reader B
hid.ll-input-report               78% ( 4)      85% ( 9)      65% ( 7)   all weak
hid.ll-input-context              48% ( 1)      75% ( 4)      18% ( 1)   weak: reader A, reader B
hid.ll-sync-responses             35% ( 1)      74% ( 1)      15% ( 1)   weak: reader B
hid.ll-pm                         69% ( 1)      73% ( 1)      43% ( 1)   all weak
hid.hid-is-usb                    60% ( 1)      82% ( 1)      17% ( 0)   weak: reader A, reader B
hid.match-flow                     3% ( 3)      86% ( 3)      34% ( 4)   weak: reader B
hid.have-special-driver           29% ( 1)      82% ( 2)      20% ( 1)   weak: reader B
hid.probe-sequence                 5% ( 1)      84% ( 2)      13% ( 2)   weak: reader B
hid.probe-failure                 27% ( 2)      83% ( 1)      14% ( 1)   weak: reader B
hid.remove-sequence               18% ( 1)      77% ( 1)      11% ( 0)   weak: reader B
hid.remove-usage                  38% ( 4)      87% ( 6)      35% ( 6)   weak: reader B
hid.devres-group                  14% ( 1)      82% ( 1)      35% ( 1)   weak: reader B
hid.devres-stop-usage             16% ( 1)      74% ( 2)      48% ( 2)   weak: reader B, reader C
hid.quirks-reset                  52% ( 1)      80% ( 1)      41% ( 1)   all weak
hid.parse-call                    43% ( 3)      80% ( 7)      21% ( 4)   weak: reader A, reader B
hid.hw-start                       0% ( 0)      62% ( 2)       0% ( 0)   weak: reader B
hid.connect-mask                  11% ( 2)      79% ( 5)       6% ( 2)   weak: reader B
hid.hw-stop                       24% ( 2)      84% ( 3)      29% ( 1)   weak: reader B
hid.hw-open-close                 44% ( 4)      76% ( 3)      32% ( 3)   weak: reader A, reader B
hid.io-start-stop                 25% ( 6)      82% ( 9)       2% ( 4)   weak: reader B
hid.io-start-usage                68% ( 1)      87% ( 2)      47% ( 2)   all weak
hid.probe-visibility              31% ( 1)      82% ( 1)       5% ( 1)   weak: reader B
hid.async-teardown-usage          69% ( 1)      77% ( 2)      24% ( 1)   weak: reader A, reader B
hid.usb-parent-usage              27% ( 1)      76% ( 1)      25% ( 1)   weak: reader B
hid.input-path                    42% ( 4)      90% (10)      52% ( 5)   all weak
hid.raw-event-return               0% ( 0)      65% ( 1)      24% ( 1)   weak: reader B
hid.event-return                   2% ( 0)      75% ( 1)       0% ( 0)   weak: reader B
hid.callback-context              24% ( 1)      74% ( 2)       0% ( 0)   weak: reader B
hid.requests-from-callbacks       33% ( 1)      69% ( 1)       0% ( 0)   weak: reader B
hid.raw-event-size-usage          20% ( 1)      68% ( 1)      25% ( 1)   weak: reader B
hid.unbound-reports               11% ( 0)      85% ( 2)      16% ( 1)   weak: reader B
hid.request-kinds                 21% ( 2)      79% ( 6)       0% ( 0)   weak: reader B
hid.raw-request-buffer-usage       5% ( 1)      76% ( 1)      25% ( 2)   weak: reader B
hid.report-buf-helpers            43% ( 4)      83% ( 2)      15% ( 1)   weak: reader A, reader B
hid.report-fixup-contract          3% ( 2)      69% ( 5)      28% ( 1)   weak: reader B
hid.report-fixup-alloc-usage       0% ( 0)      80% ( 1)      30% ( 1)   weak: reader B
hid.fixup-size-usage               0% ( 0)      55% ( 1)      26% ( 1)   weak: reader B
hid.fixup-order                   16% ( 2)      59% ( 2)      18% ( 1)   weak: reader B
hid.field-index-usage             13% ( 1)      78% ( 5)      21% ( 1)   weak: reader B
hid.validate-values               13% ( 1)      64% ( 3)       0% ( 0)   weak: reader B
hid.usage-index-usage             53% ( 1)      79% ( 1)      17% ( 1)   weak: reader A, reader B
hid.inputs-list-usage             52% ( 2)      84% ( 3)      65% ( 4)   all weak
hid.hidinput-connect              15% ( 5)      89% ( 1)      15% ( 3)   weak: reader B
hid.input-mapping-returns         24% ( 1)      84% ( 1)      11% ( 1)   weak: reader B
hid.hide-usage-usage              34% ( 1)      87% ( 1)       0% ( 0)   weak: reader B
hid.input-configured               2% ( 1)      88% ( 1)       0% ( 0)   weak: reader B
hid.input-splitting               14% ( 2)      75% ( 2)      10% ( 1)   weak: reader B
hid.hidinput-disconnect            0% ( 0)      88% ( 1)       0% ( 0)   weak: reader B
hid.battery                       80% ( 1)      86% ( 1)      12% ( 1)   weak: reader A, reader B
hid.hidraw-lifetime               21% ( 3)      75% ( 4)      43% ( 1)   weak: reader B, reader C
hid.hidraw-io                     24% ( 2)      78% ( 6)      29% ( 1)   weak: reader B
hid.uhid                          48% ( 1)      86% ( 1)      39% ( 2)   weak: reader A, reader B
hid.bpf-attach                    41% ( 7)      90% ( 9)      26% ( 1)   weak: reader A, reader B
hid.bpf-hooks                     23% ( 2)      73% ( 5)       9% ( 1)   weak: reader B
hid.bpf-kfuncs                    38% ( 2)      93% ( 4)      29% ( 1)   weak: reader B
hid.bpf-dispatch-locking          13% ( 1)      87% ( 2)      11% ( 1)   weak: reader B
hid.bpf-inject                    52% ( 2)      91% ( 1)      66% ( 1)   all weak
hid.bpf-abi                       46% ( 1)      77% ( 2)      19% ( 1)   weak: reader A, reader B
hid.quirk-tables                  49% ( 4)      75% ( 7)      25% ( 5)   weak: reader A, reader B
hid.quirk-flags                   47% ( 8)      64% ( 6)      17% ( 3)   weak: reader A, reader B
hid.driver-pm                     49% ( 4)      76% ( 6)      21% ( 3)   weak: reader A, reader B
hid.locks                         57% ( 7)      78% ( 9)      51% ( 5)   all weak
hid.core-change-checklist         41% ( 3)      84% ( 4)      40% ( 3)   all weak
hid.new-driver-checklist          38% ( 1)      69% ( 3)      55% ( 2)   weak: reader B, reader C
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `hid.layers`, `hid.device-struct`, `hid.report-structs`, `hid.field-arrays`, `hid.ll-register`, `hid.add-device-checks`, `hid.ll-free-usage`, `hid.ll-teardown-order`, `hid.ll-parse`, `hid.ll-raw-request`, `hid.ll-output-report`, `hid.ll-input-context`, `hid.match-flow`, `hid.devres-group`, `hid.parse-call`, `hid.hw-start`, `hid.raw-event-return`, `hid.event-return`, `hid.requests-from-callbacks`, `hid.request-kinds`, `hid.fixup-size-usage`, `hid.validate-values`, `hid.hidinput-connect`.

## Questions reorganised

- Subjects now: transport callbacks; device lifetime in a transport; probe and start; stop, remove
  and teardown; the input path and event callbacks; sending reports; report descriptors and fixups;
  trusting the device and the descriptor; the input bridge and hidraw; quirks; HID-BPF; core locks
  and other users. 65 questions became 61.
- Merged: `hid.match-flow` + `hid.have-special-driver` to `hid.generic-match`; `hid.raw-event-return`
  + `hid.event-return` to `hid.event-callback-returns`.
- Dropped: `hid.layers` and `hid.report-structs`, both the overview again; transports outside the
  directory go to the core checklist, the bounds that matter to the indexing questions.
