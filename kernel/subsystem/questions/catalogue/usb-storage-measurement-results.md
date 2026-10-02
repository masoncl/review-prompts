# What the usb-storage measurement found

Three models were asked the 38 questions in `usb-storage-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and
C; which models they were does not matter here. Reader C was the most current
and the most accurate (it assumed kernels from 6.12 to 6.15), reader A close
behind it (6.8 to 6.15), and reader B older (about 6.10) and wrong about
fundamentals: it invented a spinlock in `struct us_data`, state bits and
handler names that do not exist, and had the order of the layers backwards.
The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

Readers A and C know the one thing the hand-written guide is about. Both place
the redundant-override check in `get_device_info()`, know it is skipped for the
generic class entries, that it is a `dev_notice()` and that
`US_FL_NEED_OVERRIDE` silences it. What the readers get wrong, each of the
following by at least two of them, is further out: which driver reads which
quirk flag, what an entry matches, who is asked for what when an entry is
submitted, how uas and usb-storage divide devices, and, inside the core, which
paths cancel a transfer and which reset handler does what.

## What all three readers got wrong

- **Order inside `usb_stor_probe2()`.** Readers A and C put the runtime-PM get
  after `scsi_add_host()`; it comes before, and the `HostAddErr` label drops
  it. Reader B started the control thread after the host was added; it is
  started in `usb_stor_acquire_resources()`, before.
- **The completion call.** The control thread finishes a command with
  `scsi_done_direct()`, after clearing `us->srb` and releasing both the host
  lock and `dev_mutex`. Readers A and B said `scsi_done()`, A under the host
  lock; reader C was unsure which.
- **Sub-driver private data.** No reader said the destructor can be called
  with a NULL `extra` (`init_realtek_cr()` clears the pointer on failure and
  leaves the destructor set), or that `datafab.c`, `jumpshot.c` and `sddr55.c`
  allocate `us->extra` lazily in their transport function on the first
  command. Reader A had `realtek_cr_destructor()` calling timer_delete_sync();
  it calls `timer_shutdown_sync()`, because the timer re-arms itself. Reader B
  offered del_timer_sync(), which no longer exists.
- **Who is asked for what.** The header of `unusual_devs.h` asks for the
  submitter's email address above the entry, the contents of
  `/sys/kernel/debug/usb/devices`, and the patch sent to linux-usb only.
  `unusual_uas.h` asks for lsusb -v output, sent to Hans de Goede with
  linux-usb in copy. Reader A added the usb-storage maintainer as a recipient
  and put the submitter's name above the entry, reader C added the usb-storage
  list (that address is only in the text of the notice), reader B offered lsusb
  for both. `COMPLIANT_DEV()` is only for an
  entry whose sole purpose is `US_FL_CAPACITY_OK`; A and B made it wider.
- **The uas reset handler.** Readers A and C named
  uas_eh_device_reset_handler(); the template installs
  `uas_eh_host_reset_handler()` as `eh_host_reset_handler` and there is no
  device reset handler. Reader B had the abort handler returning SUCCESS; it
  always returns FAILED.

## What two readers got wrong

- **Disconnect does not stop the transport** (A and B). Both said
  `usb_stor_stop_transport()` is called on disconnect, which is what the long
  comment at the top of `transport.c` still says. Its only caller is
  `command_abort_matching()`. `usb_stor_msg_common()` tests only
  `US_FLIDX_ABORTING` before submitting, not the disconnecting bit, and it sets
  `US_FLIDX_URB_ACTIVE` after `usb_submit_urb()` succeeds, not before as both
  had it. Reader C had this right and said the USB core ends the transfers,
  which holds for an unplug; the drivers set `soft_unbind`.
- **There is no per-interface entry.** Readers A and C both described an
  UNUSUAL_VENDOR_INTF() macro that limits an entry to one interface and said
  `unusual_devs.h` contains one. Nothing of that name is in the tree. An
  `UNUSUAL_DEV()` entry is `USB_DEVICE_VER()`: vendor, product and revision
  range, nothing else, so it captures every interface of the device, storage
  or not.
- **Which driver reads which flag** (A and B). usb-storage never tests
  `US_FL_NO_REPORT_OPCODES`, `US_FL_NO_REPORT_LUNS`, `US_FL_NO_SAME` or
  `US_FL_MAX_SECTORS_240`: it sets `no_report_opcodes`, `no_write_same` and
  `no_report_luns` for every device and its template has `max_sectors` 240.
  Reader A had the last two as read by both and was unsure of the second;
  reader B had usb-storage acting on all four, and had uas ignoring
  `US_FL_FIX_CAPACITY`, `US_FL_CAPACITY_HEURISTICS`, `US_FL_NO_WP_DETECT` and
  `US_FL_ALWAYS_SYNC`, all of which `uas_sdev_configure()` acts on. Reader A
  listed a flag NO_UAS that does not exist and did not know `US_FL_IGNORE_UAS`
  is what makes usb-storage bind, through `storage_probe()` calling
  `uas_use_uas_driver()`. The list of letters in `kernel-parameters.txt` is
  no help here: it marks `US_FL_NO_ATA_1X` "uas only", and `queuecommand_lck()`
  in `scsiglue.c` honours it too.
- **The flag word** (A in one answer, B throughout). `fflags` in `struct
  us_data` and `flags` in `struct uas_dev_info` are `u64`; both said unsigned
  long. `driver_info` is `kernel_ulong_t`, 32 bits on a 32-bit kernel, and all
  32 values up to `US_FL_SENSE_AFTER_SYNC` are taken. Reader B thought two or
  three were free. Reader C said none are free without adding that bits 32 to
  63 of the word are.
- **Where the codes are** (A and B). `USB_SC_*` and `USB_PR_*` are in
  `include/linux/usb/storage.h`. Reader A put them under include/uapi; reader
  B spelled them US_SC_ and US_PR_ and put them in `include/linux/usb_usual.h`.
- **The checks coded in `uas-detect.h`** (A and B). Reader A gave the ASMedia
  devices the wrong flags and the 32-stream case `US_FL_NO_ATA_1X`; that flag
  is for every Seagate (vendor 0x0bc2) device, 32 streams means
  `US_FL_IGNORE_UAS`, and `bMaxPower` of zero means leave it alone. Neither
  knew the HIKSEMI MD202 string check or the bus `sg_tablesize` test, and
  reader A had `unusual_uas.h` included from `usual-tables.c`; it is included
  from `unusual_devs.h`, so it reaches both `usual-tables.c` and `usb.c`.
- **Error handlers** (A and B). `bus_reset()` only calls
  `usb_stor_port_reset()`; reader A had it abort the running command first,
  which is what `device_reset()` does. `US_FLIDX_RESETTING` is set and cleared
  in the error tail of `usb_stor_invoke_transport()`; both had a reset routine
  doing it. A port reset is refused with -EPERM for a `USB_QUIRK_RESET`
  device; neither knew.
- **Vendor heuristics** (A; B named no vendors). Nokia, Nikon, Pentax and
  Motorola disks get `US_FL_CAPACITY_HEURISTICS` in `sdev_configure()`, not
  `US_FL_FIX_CAPACITY`.

## What reader B got wrong as well

- The override notice is logged at info level and "suppressed" by
  `USB_SC_DEVICE`; it is `dev_notice()`, and only `US_FL_NEED_OVERRIDE`
  suppresses it.
- The per-device callbacks are slave_alloc and slave_configure; the tree has
  `sdev_init()` and `sdev_configure()`, the second taking a `struct
  queue_limits *`. The template has no queue depth; it is `can_queue` 1.
- `delay_use` is in whole seconds; it is kept in milliseconds and takes an
  `ms` suffix (`parse_delay_str()`).
- The highest LUN is capped at 7; `US_BULK_MAX_LUN_LIMIT` is 0x0f, and eight
  or more raises the host's `max_lun`.
- A `quirks=` entry patches single bits; it replaces every flag in the mask.
  Dynamic ids come from `quirks=`; they come from sysfs `new_id` and get
  `for_dynamic_ids`.
- Handler and helper names that do not exist: usb_stor_abort_command(),
  usb_stor_ATAPI_command(), usb_stor_CBI_transport(), UNUSUAL_UAS_DEV(), the
  bits US_FLIDX_GONE, US_FLIDX_DONT_SCAN and US_FLIDX_RUNNING.
- uas takes its queue depth from the block layer tag and is 1 without streams;
  it scans `devinfo->cmnd[]` for a free slot, the depth is 32 below
  SuperSpeed, and both `can_queue` and the device depth are the depth minus 2.

## What a reader said it did not recognise

Reader A could not name a second place that expands `US_DO_ALL_FLAGS`
(`show_info()` in `scsiglue.c`) or the flag that is dropped by connection speed
(`US_FL_GO_SLOW`, cleared unless the device is high speed). Reader B could not
recall which devices are special-cased in `uas_use_uas_driver()` or where
`unusual_uas.h` is included. Reader C was unsure of the timer helper names and
of whether the flags still travel in `driver_info` now that the word is 64
bits; they do.

## What the readers already knew

Which file holds what (all three, apart from the header for the codes); the
argument order of `UNUSUAL_DEV()` and that `useProtocol` holds a subclass and
`useTransport` a protocol (A and C); how the two parallel arrays are built and
indexed, including `for_dynamic_ids` and `.no_dynamic_id` in the sub-drivers (A
and C); the syntax and replace-not-add meaning of `quirks=`, and that a new
letter needs the switch, the mask and `kernel-parameters.txt` (A and C); the
two families of result codes (C without a correction); what `dev_mutex` and
the host lock cover (A and C, with small corrections); the Bulk-only
tolerances, the last-sector logic and the maximum transfer size rules (C).

## Where the hand-written guide is stale

Nothing in `usb-storage.md` was found to be false. The argument positions, the
field names, the code values, the flag's header, the debugfs line format and
even the share of entries that use `USB_SC_DEVICE, USB_PR_DEVICE` (275 of 323)
match the tree. It is narrow rather than stale: all 414 words are about one
check that two of three readers already describe correctly. It does not say
that the check is skipped for the generic class entries, that there are three
variants of the message, that sub-driver tables go through the same check, or
anything about `unusual_uas.h`, the flags, what an entry matches, or the rest
of the directory. The built guide keeps the check as one item and spends the
rest on what the readers got wrong.

## What was left out of the build set, and why

The build set is sized to 600 words, the least a built guide is given, and no
answer is budgeted under 40: ten questions and 510 words of budget, which with
titles and headings comes to about 630. It keeps the nine it had when it was
held to the 414 words of the hand-written guide, now with room for whole
sentences, and `usbstor.urb-submission` came back: it is the third rule a
sub-driver fix runs into, two readers had disconnect stopping the transport,
and the locks item says who holds `dev_mutex`, not which helpers a transfer has
to go through. Two of the ten are worded differently from the measurement set:
`usbstor.flags-by-driver` asks for the flags uas reads, with every name in
full, and one sentence for the rest, because a table of all thirty-two does not
fit and a partial one reads as complete; `usbstor.flag-definitions` drops the
second expansion of the list and takes from `usbstor.quirks-param` what has to
change when a letter is added. Three were reworded in both files when the build
set was resized, without changing what they ask: `usbstor.urb-submission` asks
which paths cancel a transfer and whether disconnect is one of them, instead of
presupposing that it is, and asks for the in-tree code that does its own USB
I/O correctly as well as for the unsafe kind; `usbstor.uas-selection` asks
whether `unusual_uas.h` is included in more than one place before asking why;
`usbstor.locks` asks for the state bits by their full names.

- `usbstor.files`. All three readers place every file. The two header paths
  that two of them had wrong are given by the entry macro and flag definition
  items, so the built guide has no "where to look" part. A first build that
  had one came out over the size limit with nothing in it the other answers
  did not say.
- The command path, the probe order, the disconnect order, the dynamic state
  bits, the result codes, the Bulk-only tolerances, auto-sense, error recovery
  and the SCSI error handlers. Every reader had corrections here, but these
  are changes to the core, which are rare, and `transport.c` and `usb.c` carry
  long comments (one of them stale, as noted above). `usbstor.locks`,
  `usbstor.urb-submission` and `usbstor.extra-data` are kept as the three
  items a sub-driver fix needs. `usbstor.transport-returns` is the first to
  bring back if the guide is given more room: a sub-driver's transport
  function returns one family of codes and the helpers it calls return the
  other.
- The uas command state machine, error handling and queue depth. Confined to
  `uas.c`, which a patch to it has open; the split between the two drivers is
  kept. `usbstor.uas-error-handling` is the next after that: all three readers
  had the reset handler's name or the abort handler's return value wrong.
- `usbstor.quirks-param`. Two of three readers have it right; the one thing a
  new flag needs from it is folded into `usbstor.flag-definitions`.
- `usbstor.table-expansion`, `usbstor.subdriver-structure`,
  `usbstor.init-function`, `usbstor.descriptor-crosscheck`: known to A and C,
  and visible in `karma.c` or in the patch.
- The host template, per-device settings, LUN count, capacity workarounds,
  delayed scan and power management: mostly reader B's old names, and a patch
  that touches them shows the current ones.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 113 corrections, 28% rewritten on average
reader B: 131 corrections, 79% rewritten on average
reader C: 70 corrections, 18% rewritten on average

question                           reader A      reader B      reader C
usbstor.files                       1% ( 1)       9% ( 2)       0% ( 0)
usbstor.command-path               26% ( 4)      69% ( 4)      37% ( 3)
usbstor.us-data                    10% ( 3)      73% ( 6)      21% ( 2)
usbstor.locks                      12% ( 3)      75% ( 4)      10% ( 3)
usbstor.dflags                     15% ( 3)      57% ( 3)       8% ( 3)
usbstor.probe-sequence             40% ( 7)      81% ( 5)      80% ( 4)
usbstor.disconnect                 43% ( 1)      84% ( 1)      27% ( 0)
usbstor.scan-delay                 45% ( 1)      90% ( 1)      15% ( 2)
usbstor.pm                         14% ( 2)      73% ( 1)       8% ( 0)
usbstor.transport-returns          26% ( 5)      96% ( 5)       0% ( 0)
usbstor.urb-submission             31% ( 4)      86% ( 3)      26% ( 3)
usbstor.iobuf                      27% ( 1)      79% ( 2)       5% ( 1)
usbstor.bulk-transport             47% ( 3)      99% ( 2)      17% ( 1)
usbstor.autosense                  59% ( 7)      92% ( 3)      13% ( 1)
usbstor.error-recovery             32% ( 7)      85% ( 9)       5% ( 2)
usbstor.eh-handlers                28% ( 2)      80% ( 5)       9% ( 2)
usbstor.protocols                  11% ( 1)      85% ( 5)      38% ( 4)
usbstor.host-template              28% ( 2)      76% ( 1)      18% ( 1)
usbstor.sdev-configure             15% ( 2)      94% ( 2)      51% ( 4)
usbstor.max-lun                    13% ( 2)      91% ( 1)      17% ( 1)
usbstor.capacity-hacks             23% ( 3)      89% ( 1)      32% ( 4)
usbstor.unusual-macro              11% ( 4)      79% ( 5)       5% ( 1)
usbstor.table-expansion            10% ( 2)      91% ( 2)      14% ( 2)
usbstor.entry-match                12% ( 1)      84% ( 2)      13% ( 1)
usbstor.override-notice            34% ( 2)      79% ( 5)      32% ( 2)
usbstor.entry-conventions          33% ( 5)      79% ( 4)       4% ( 2)
usbstor.descriptor-crosscheck       9% ( 1)      84% ( 2)      35% ( 2)
usbstor.flag-definitions           40% ( 3)      81% ( 6)      29% ( 2)
usbstor.flags-by-driver            28% ( 6)      74% ( 5)       3% ( 1)
usbstor.quirks-param               13% ( 2)      81% ( 4)       6% ( 1)
usbstor.runtime-flag-changes       88% ( 5)      94% ( 1)      12% ( 1)
usbstor.uas-selection              73% ( 6)      86% ( 6)      23% ( 1)
usbstor.uas-command-state          41% ( 2)      79% ( 3)      11% ( 1)
usbstor.uas-error-handling         60% ( 3)      76% ( 4)      30% ( 3)
usbstor.uas-queue-depth            20% ( 1)      95% ( 4)      12% ( 1)
usbstor.subdriver-structure         6% ( 1)      67% ( 6)      12% ( 3)
usbstor.extra-data                 44% ( 3)      70% ( 4)      21% ( 3)
usbstor.init-function              31% ( 2)      73% ( 2)      18% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `usbstor.probe-sequence`, `usbstor.autosense`, `usbstor.sdev-configure`, `usbstor.uas-error-handling`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `usbstor.command-path`, `usbstor.us-data`, `usbstor.disconnect`, `usbstor.transport-returns`, `usbstor.iobuf`, `usbstor.bulk-transport`, `usbstor.error-recovery`, `usbstor.eh-handlers`, `usbstor.host-template`, `usbstor.table-expansion`, `usbstor.quirks-param`, `usbstor.uas-command-state`, `usbstor.subdriver-structure`.

## Questions reorganised

By subject now, 28 questions where there were 29: unusual device entries; quirk flags and the two
drivers (with the per-device SCSI settings and the host template, where most flags end up); the
command path and its locks; sense, Bulk-only and recovery; probe, disconnect and sub-drivers; UAS.
`usbstor.flag-definitions` and `usbstor.quirks-param` both asked what changes when a flag letter is
added and are merged as `usbstor.quirk-flags`. Nothing is dropped whole. Dropped from inside
questions, as lookups: the files that include the table header, the chain of functions on the command
path, the uas state bits, how code gets from `struct us_data` to the host, and the pieces of a
sub-driver beyond what a matched id needs.
