# What the ata measurement found

Three models were asked the 30 questions in `ata-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.15 to 7.0), precise, and needed little rewriting;
reader A was close behind (6.12 to 6.17) and knew the recent reworks but got
details of them wrong; reader B (6.10 to 6.12) described an older libata
throughout, with a good many names that are gone and a handful it made up. The
hand-written guide was never checked against current sources, so differences
between it and the built guide are expected and are noted near the end.

Readers A and C know the shape of the library well: the file map, the objects,
the command path, completion and the flag that hands a command to error
handling, the reset callbacks and where they now live, what the transfer
functions return. What all three get wrong is narrower and is mostly about the
hand-written guide's own subject, the paths that identify and configure a
device: what an error return from them costs, which optional-feature helpers
can fail the device, how long a quirk bit set at run time lasts, and the rule
for setting one, where each reader offered a rule that correct in-tree code
breaks.

## What all three readers got wrong

- **Quirk bits set at run time are never cleared by revalidation, reset or
  detach.** Readers A and B said detach clears them, and reader C, who knew
  better, still wrote its rule as if it did. Only `ata_dev_init()` sets
  `dev->quirks = 0`, and it runs from `ata_link_init()` and
  `ata_eh_schedule_probe()`; `ata_eh_detach_dev()` leaves them, and
  `ata_dev_configure()` only ORs the table's bits in. No reader had the whole
  list of setters (reader C came closest, four short):
  `ata_read_log_page()`, `ata_identify_page_supported()`,
  `ata_hpa_resize()`, `ata_dev_config_ncq()`, `ata_dev_config_lpm()`,
  `ata_dev_configure()` for ATAPI tape, `ata_sff_dev_classify()`,
  `ahci_dev_config()`, `sil_dev_config()`, and `it821x_dev_config()`, which
  also clears one.
- **The rule each reader gave for setting a quirk is broken by correct code.**
  Readers A and C said a bit should be set only when the device itself aborted
  the command (`AC_ERR_DEV`); reader B said setting one after a single failed
  command is unsafe. `ata_read_log_page()` sets `ATA_QUIRK_NO_DMA_LOG` on any
  failure of the DMA form and retries with PIO, and `ata_dev_config_ncq()` sets
  `ATA_QUIRK_BROKEN_FPDMA_AA` only when the error is not `AC_ERR_DEV`, then
  returns `-EIO` so the retry skips the feature.
- **What a failed configuration costs.** No reader had all of
  `ata_eh_handle_dev_fail()`: `-EAGAIN` does not use up a try; `-ENODEV` and
  `-EINVAL` cut the remaining tries to one and, falling through to the `-EIO`
  case, lower the link speed and drop to PIO at once; `-EIO` itself does that
  only when one try is left; tries start at `ATA_EH_DEV_TRIES`, or at one with
  `ATA_LFLAG_NO_RETRY`; at zero the device is disabled, detached only if the
  link is offline, and probed again only if its `probe_mask` bit is set.
  `-ENOENT` is special only from `ata_dev_read_id()` on a new device.
  Reader C had all but the single try and the scope of `-ENOENT`; reader A
  charged `-EAGAIN` a try; reader B had the meanings of the errnos wrong, made
  up a counter name and said the device stays gone until it is replugged.
- **Deferred commands.** All three left out `ATA_DEFER_LINK_EXCL`. Only a
  non-NCQ command deferred with `ATA_DEFER_LINK` is held, in
  `link->deferred_qc` in `struct ata_link`, reported to the SCSI layer as
  issued and sent later by `ata_scsi_deferred_qc_work()`; everything else is
  freed and handed back. Readers A and C knew the mechanism but put the fields
  in `struct ata_port`; reader B said libata never holds a command.
- **There is no ata_qc_new_init().** All three named it. `ata_scsi_qc_new()`
  takes `ap->qcmd[]` by the request's tag, and `ata_exec_internal()` sets up
  the internal one.
- **`libata.force`: for quirks the first matching entry wins.**
  `ata_force_get_fe_for_dev()` scans forward and returns the first entry that
  matches the device, of any kind, while the cable, link and transfer-mode
  lookups scan from the end. `kernel-parameters.txt` says the last one is
  used, and so did reader A; the other two did not say. All three gave wrong
  call sites; `ata_force_xfermask()` is called from `ata_set_mode()`, and two
  readers named an ata_do_set_mode() that does not exist.
- **Host template macros.** `__ATA_BASE_SHT` does not set `.sdev_configure`,
  `.can_queue` or the scatterlist limits. `ATA_SUBBASE_SHT` sets the first
  two, `ATA_BASE_SHT` adds only `.sdev_groups`, `ATA_PIO_SHT` and
  `ATA_BMDMA_SHT` add `.sg_tablesize` and `.dma_boundary`, and the NCQ macros
  exist only with `CONFIG_SATA_HOST`.
- **Link power management.** `ata_dev_config_lpm()` turns a port's
  `ATA_FLAG_NO_LPM` into `ATA_QUIRK_NOLPM` on the device, not the reverse, and
  a device with the quirk forces the whole port's `target_lpm_policy` to
  `ATA_LPM_MAX_POWER`; nothing restores it, and `ata_scsi_lpm_store()` then
  returns `-EOPNOTSUPP`. No reader had all the places the flags are set.
- **Stale documentation.** Readers A and C listed stale parts of
  `Documentation/driver-api/libata.rst` that are not in it (phy_reset,
  eng_timeout, port_disable); reader B named none. What is stale:
  irq_handler, irq_clear,
  post_set_mode and ata_host_set, several prototypes, and no mention of the
  `reset` and `pmp_reset` structures.
- **Entering error handling.** `ata_port_freeze()` and `ata_port_abort()`
  schedule error handling themselves only when no command was aborted;
  otherwise each aborted command gets there through `ata_qc_complete()` and
  `ata_qc_schedule_eh()`. `eh_mutex` is dropped in `ata_exec_internal()` and
  the reset retry waits as well as in `ata_msleep()`.

## What readers A and B got wrong as well

- **The quirk word is 64 bits.** Both said `unsigned int`, `1U << n` and a
  limit of 32. It is `u64 quirks`, masks are `BIT_ULL()` of the
  `__ATA_QUIRK_` bit numbers, and `ata_dev_quirks()` has a `BUILD_BUG_ON()` at
  64. Reader C knew that. None knew that `ata_dev_print_quirks()` takes an
  `unsigned int` and cannot print a bit above 31.
- **The log directory with a bad version word is read again on every call.**
  `ata_read_log_directory()` treats the cache as valid only when word 0 is
  0x0001, warns once and uses the data anyway. Reader A missed the re-read;
  reader B said the directory is treated as invalid and that
  `ata_log_supported()` returns a bool (it returns the log's page count).
  Reader A could not say where the cache is dropped:
  `ata_clear_log_directory()` at the start of every `ata_dev_configure()` and
  after a failed read.
- **Optional feature helpers.** Both named an ata_dev_config_zac() (it is
  `ata_dev_config_zoned()`), and neither knew which helper can fail the
  device: only `ata_dev_config_ncq()`, through `ata_dev_config_lba()`, when
  enabling FPDMA auto-activate fails with something other than a device
  error. Reader B said none can.
- **Log page reads.** The scratch buffer is `dev->sector_buf`; reader A said
  `ap->sector_buf`. Reader B said `ata_read_log_page()` returns an errno and
  misspelt the port flag. Both put the two log quirks inside the function;
  its callers check them.
- **Reconfiguration.** Reader A said any size change explained by the host
  protected area is tolerated; only a late unlock is, a late lock returns
  `-EIO` with `ATA_DFLAG_UNLOCK_HPA`. Reader B had `ata_dev_same_device()`
  comparing firmware and size; it compares class, model and serial, and the
  size check is in `ata_dev_revalidate()`.
- **Where a SCSI device is attached.** Both said all of probing runs in error
  handling. `ata_scsi_scan_host()` runs afterwards, from `async_port_probe()`
  or the hotplug work.
- **Operations inheritance.** Finalisation runs only from `ata_host_start()`;
  parents reached only through `inherits` can be and are `const`.

## What reader B got wrong as well

- Names that are gone: `ATA_QCFLAG_FAILED` (it is `ATA_QCFLAG_EH`), the reset
  callbacks as direct members of the operations structure, the `slave_*` host
  template callbacks (`ata_scsi_sdev_init()`, `ata_scsi_sdev_configure()`,
  `ata_scsi_sdev_destroy()`), ata_exec_internal_sg(), ATA_HORKAGE_ names mixed
  in with `ATA_QUIRK_` ones.
- Names it made up: libata-bmdma.c, CONFIG_ATA_ZPODD, ata_scsi_dev_attach(),
  ATA_QUIRK_NOHRST, ATA_QUIRK_MAX_SEC_128, ata_dummy_qc_prep, a
  libata.ata_lpm_policy parameter, a `qc_ns` callback.
- Quirk table entries are not ORed together: `ata_dev_quirks()` returns at the
  first `glob_match()` hit. The value of a quirk comes from a separate table,
  `__ata_dev_max_sec_quirks[]`, after the force parameter.
- `ap->lock` is the lock in `struct ata_host`, not the SCSI host lock. It
  protects `pflags`; `flags` belongs to error handling once the port is
  active, which reader A had wrong too.
- `-ENOENT` is special only from prereset; `-EAGAIN` from hardreset asks for a
  follow-up softreset. The port is frozen after prereset and thawed before
  postreset.

## What the readers already knew

The file map (A and C), the chain of objects, the command path, completion and
`ata_qc_from_tag()` (A and C), `ata_exec_internal()` and that it returns a
mask, which functions return a mask and which an errno (A and C), the embedded
reset structures (A and C), first match wins in the quirk table (A and C),
the places a new quirk touches (A and C), the two flag words in the port (C).

## Where the hand-written guide is stale

`ata.md` is one lesson, drawn from one patch: do not reject the log directory
over its version word. The tree now does exactly what the guide calls correct
(`ata_read_log_directory()` warns once and goes on), so the wrong example it
shows is nowhere in the tree, and `ATA_QUIRK_NO_LOG_DIR` is set only from the
quirk table and the force parameter. Its table of when to fail is not what the
code does. It says an I/O error reading device data and a bad checksum should
fail with an error; a failed log read makes the helper treat the feature as
absent and the device carries on, and `ata_eh_read_log_10h()` only warns about
a bad checksum. It says invalid configuration of NCQ, TRIM or security should
fail; the helpers turn the one feature off, and the only one that fails the
device is `ata_dev_config_ncq()` on the auto-activate path. It says a quirk
set at run time should have a fallback, without saying that such bits are set
in ten places on purpose and last until `ata_dev_init()`. It recommends
`ata_dev_warn_once()` without saying that it is `pr_warn_once()`: once per
call site for every device in the system, not once per device. It does not
say what an error return costs (three tries, then the device is disabled), or
that `ata_dev_configure()` runs again on every revalidation, so a check added
there runs on resume against a disk that is in use. It was never onboarded to
the drift checker; the names it uses all exist.

## What was left out of the build set and why

The hand-written guide is 432 words and about one thing, so the build set is
sized to the 600-word floor: eleven questions and 550 words of budget, none
under 40. Nine of them are the guide's subject: the configuration path, when
it runs again, what a failure costs, the optional-feature helpers, the log
directory, reading a log page, the quirk table, quirks set at run time and the
rule for checking device-reported data. The other two are what the quirk flags
are called and what adding one touches, because quirk patches are the
commonest change to this code. Log page reads were left out when the guide was
held to 432 words and came back with the floor: every new feature helper calls
`ata_read_log_page()`, reader B took its return value for an errno, reader A
put its buffer in the port, and both put inside it the quirk tests that its
callers make. Left to the source: the file map, the objects, the command path,
completion, internal commands and the return conventions (readers A and C
fair); deferred commands, the force parameter, the host template macros and
link power management (every reader was wrong, but each is one function or one
block of macros that a reviewer of such a patch opens anyway, none bears on
configuring a device, and as measured each asks for ninety words or more,
about a sixth of this guide); error handling entry, reporting, reset callbacks
and locking (A and C fair, and B's errors are old names); the documentation,
the message helpers, the configuration symbols and the change checklist (low
relevance, or a list the Makefile gives).

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A           75        42%      2     17   6.12 to 6.17
reader-B          103        79%      0     29   6.10 to 6.12
reader-C           74        25%     11      7   6.15 to 7.0

question                      reader-A      reader-B      reader-C   verdict
ata.core-files                 0% ( 0)      21% ( 6)       2% ( 2)   middling
ata.objects                   27% ( 3)      46% ( 3)      20% ( 3)   weak: reader-B
ata.docs                      50% ( 5)      90% ( 2)      46% ( 3)   all weak
ata.config-path               48% ( 3)      91% ( 6)       4% ( 2)   weak: reader-A, reader-B
ata.config-reruns             81% ( 3)      94% ( 3)      26% ( 4)   weak: reader-A, reader-B
ata.config-failure            40% ( 1)      89% ( 3)      12% ( 3)   weak: reader-A, reader-B
ata.optional-features         53% ( 5)      88% ( 4)      14% ( 2)   weak: reader-A, reader-B
ata.log-directory             59% ( 2)      83% ( 7)       9% ( 1)   weak: reader-A, reader-B
ata.log-page-reads            51% ( 3)      88% ( 4)       0% ( 0)   weak: reader-A, reader-B
ata.validation-usage          54% ( 2)      83% ( 5)      35% ( 4)   weak: reader-A, reader-B
ata.message-helpers           66% ( 1)      65% ( 2)      29% ( 1)   weak: reader-A, reader-B
ata.quirk-names               38% ( 1)      86% ( 3)      53% ( 3)   weak: reader-B, reader-C
ata.quirk-table               29% ( 1)      78% ( 1)       9% ( 1)   weak: reader-B
ata.quirk-runtime             69% ( 4)      85% ( 2)      70% ( 3)   all weak
ata.quirk-add                 22% ( 1)      80% ( 1)      38% ( 1)   weak: reader-B
ata.force-param               70% ( 3)      88% ( 2)      25% ( 3)   weak: reader-A, reader-B
ata.command-path              17% ( 2)      69% ( 3)      20% ( 2)   weak: reader-B
ata.qc-defer                  82% ( 2)      77% ( 3)      64% ( 4)   all weak
ata.completion                22% ( 1)      83% ( 3)      10% ( 1)   weak: reader-B
ata.internal-commands         28% ( 5)      72% ( 2)      22% ( 1)   weak: reader-B
ata.return-conventions         5% ( 0)      51% ( 2)       6% ( 1)   weak: reader-B
ata.eh-entry                  27% ( 4)      90% ( 3)      41% ( 7)   weak: reader-B, reader-C
ata.eh-reporting              27% ( 3)      97% ( 5)      17% ( 2)   weak: reader-B
ata.reset-ops                 31% ( 2)      83% ( 4)      24% ( 4)   weak: reader-B
ata.locking                   31% ( 3)      90% ( 4)      16% ( 3)   weak: reader-B
ata.port-ops-inheritance      62% ( 3)      75% ( 3)       0% ( 0)   weak: reader-A, reader-B
ata.sht-macros                43% ( 3)      89% ( 3)      43% ( 2)   all weak
ata.lpm                       50% ( 4)      81% ( 5)      52% ( 3)   all weak
ata.config-symbols            49% ( 3)      97% ( 5)      15% ( 4)   weak: reader-A, reader-B
ata.change-checklist          58% ( 2)      75% ( 4)      38% ( 4)   weak: reader-A, reader-B
```

In the build set `ata.validation-usage` asks for the unsafe usage on both
sides, checking too little and checking too much, which the measured wording
left to the answerer; the id is unchanged. A first build from the measured
wording gave, from one builder, only the unchecked count as the unsafe usage
and, from the other, only the error return over a word the code never uses.
At 60 words one builder's answer was sent back for length and came back with
only the side that checks too little, so the question has 80 and says "on both
sides". `ata.quirk-runtime` went from 65 words to 80 for the same reason, and
asks for every function by name: at 65 one builder's check cut three setters
from the list to make it fit, and the whole list is what no reader had.

Six more questions are reworded in the build set, ids unchanged, because a
clause in the measured wording presupposed an answer. `ata.config-path` asked
in which context "all of that" runs, and attaching the SCSI device does not
run where the rest does. `ata.config-reruns` asked what is compared
"afterwards", and the identity check comes before `ata_dev_configure()` and
only the size check after. `ata.optional-features` asked which helpers can
fail the configuration rather than whether any can. `ata.log-directory` took
the cache as given. `ata.quirk-table` took it as given that a quirk carries a
value. `ata.log-page-reads` asked which quirks stop `ata_read_log_page()`
issuing a command, which is the mistake two readers made: it now asks whether
each flag or quirk is tested inside the function or by its callers.

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `ata.qc-defer`, `ata.change-checklist`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `ata.command-path`, `ata.completion`, `ata.internal-commands`, `ata.return-conventions`, `ata.eh-entry`, `ata.eh-reporting`, `ata.reset-ops`, `ata.locking`.

## Questions reorganised

By subject now, 22 questions where there were 23: configuring a device (with
`ata.validation-usage` beside the helpers it is about); quirks; issuing and completing commands;
error handling; other users and builds. `ata.quirk-names` and `ata.quirk-add` are merged as
`ata.quirk-flags`: what the flags are called, what holds them, and what adding one touches.
`ata.quirk-runtime` no longer asks for every setter by name, which a search for writes to the quirk
word gives; it asks how long a bit lasts, the rule, and how to find the setters. `ata.command-path`
asks what is held and where a command can be refused, not for the chain of functions, and
`ata.change-checklist` keeps the outside users and the configured-out builds. Nothing else dropped.
