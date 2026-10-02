# What the pm measurement found

Three models were asked the 66 questions in `pm-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels up to 7.0), reader A a few releases behind it, and reader B
older again, with whole mechanisms out of date. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted near the end.

All three know the concepts of runtime PM and of the device phases well: the
usage counter, the four phases and their lists, direct complete, the driver
flags, wakeup sources. What they get wrong is return values and conditions at
the edges, a handful of things that changed in the last few releases and that
the in-tree documentation has not caught up with either, and, for reader B,
most names.

## What all three readers got wrong

- **`power.runtime_error`.** All three said a failed resume callback sets it.
  Only the fail path of `rpm_suspend()` writes it, and only for errors other
  than -EAGAIN and -EBUSY; `rpm_resume()` just puts the status back to
  `RPM_SUSPENDED`. `rpm_callback()` turns a callback's -EACCES into -EAGAIN.
  The idle callback is called directly by `rpm_idle()` and is never recorded.
- **`pm_wq` is not freezable.** All three gave `WQ_FREEZABLE`. It is
  `alloc_workqueue("pm", WQ_UNBOUND, 0)` in `pm_start_workqueues()` in
  `kernel/power/main.c`, so queued runtime PM requests run while tasks are
  frozen. `Documentation/power/runtime_pm.rst` still explains `pm_wq` by its
  synchronisation with system-wide transitions.
- **The late phase disables runtime PM with a resume check.**
  `device_suspend_late()` calls `pm_runtime_disable()`, which is
  `__pm_runtime_disable(dev, true)`: a pending resume request is carried out
  first. Readers A and C said `(dev, false)`. It re-enables runtime PM straight
  away if the late callback fails.
- **`pm_runtime_get_sync()` on a disabled device does not always fail.**
  `rpm_resume()` returns 1 when both `runtime_status` and `last_status` are
  `RPM_ACTIVE`, returns 0 with `RPM_TRANSPARENT`, and only otherwise -EACCES.
  Readers A and B did not know the flag; reader C knew it and still said no
  flag changes the result.
- **Filesystem freezing is unconditional.** `suspend_prepare()` and
  `hibernate()` always call `filesystems_freeze(filesystem_freeze_enabled)`;
  with the sysfs knob off it still freezes filesystems flagged
  `FS_POWER_FREEZE`. Readers A and C said the knob gates the call; reader B put
  the freezing inside `freeze_processes()`.
- **The macros in `include/linux/pm.h`.** All three called the `SET_` family
  deprecated. Only `SIMPLE_DEV_PM_OPS()` and `UNIVERSAL_DEV_PM_OPS()` carry
  that comment. All three left out `DEFINE_NOIRQ_DEV_PM_OPS()`. `RUNTIME_PM_OPS()`
  assigns its callbacks bare; they are dropped only through `pm_ptr()` on the
  pointer in the driver structure. Reader B had the `__maybe_unused` rule
  backwards.
- **`PM_EVENT_POWEROFF`** is handled by `pm_op()` and its late and noirq
  counterparts next to `PM_EVENT_HIBERNATE`; nothing in the tree issues it. None
  listed it.
- **Thaw situations.** None listed `hibernate_quiet_exec()` (used by the nvdimm
  driver) or a cancelled Xen save, both of which thaw with the system carrying
  on and with neither helper able to tell. `PMSG_RECOVER` also follows a failed
  restore, not only a failed image creation.
- **Wakeup plumbing.** `pm_system_irq_wakeup()` records at most two interrupts
  and calls `pm_system_wakeup()` only if a slot was free (all three). Readers A
  and C: `dev_pm_arm_wake_irq()` calls `enable_irq_wake()` for any wake interrupt
  of a wakeup-enabled device, not only a dedicated one, and `pm_wakeup_pending()`
  is checked in `device_suspend()` and `device_suspend_late()` and not in the
  noirq phase. Reader B placed the arming on the wakeup-enable path.
- **What a change to the cores must preserve.** Every reader needed four or
  more corrections here. `rpm_idle()` drops and retakes `power.lock` itself
  around the idle callback; `__rpm_callback()` is not the only place. Setting
  `RPM_SUSPENDING` or `RPM_RESUMING` wakes nobody. In the
  device phases the prepare and complete walks go the opposite way from the
  others, the remainder is spliced forward onto the target list on error, and
  only the suspend-side functions look at `async_error`.
- **Locks on `struct dev_pm_info`.** `power.lock` does not cover all the
  bitfields: `ignore_children`, `needs_force_resume`, `is_suspended`,
  `must_resume` and others are written without it.

## What only some readers got wrong

Reader B, and nobody else:

- Names that are gone: DPM_FLAG_NEVER_SKIP (it is `DPM_FLAG_NO_DIRECT_COMPLETE`),
  disable_nonboot_cpus(), freezable_schedule(), PF_FREEZER_SKIP (it is
  `PF_NOFREEZE`), PMSG_AFTER_RESTORE, a device_pm_async flag,
  PM_QOS_FLAG_REMOTE_WAKEUP, swsusp_resume() as the boot entry point.
- There are no scope guards for runtime PM. There are: `pm_runtime_noresume`,
  `pm_runtime_active`, `pm_runtime_active_auto`, their `_try` and
  `_try_enabled` forms and the `PM_RUNTIME_ACQUIRE()` family, checked with
  `PM_RUNTIME_ACQUIRE_ERR()`.
- `power.last_busy` is in jiffies and no put helper refreshes it. It is
  nanoseconds, and `pm_runtime_put_autosuspend()`,
  `pm_runtime_put_sync_autosuspend()`, `pm_runtime_autosuspend()` and
  `pm_request_autosuspend()` all call `pm_runtime_mark_last_busy()`;
  `__pm_runtime_put_autosuspend()` is the form that does not.
- `pm_runtime_put_autosuspend()` goes through `__pm_runtime_idle()`. It goes
  through `__pm_runtime_suspend()`.
- The suspend and idle paths return -EAGAIN on a disabled device (it is
  -EACCES), the suspend path never returns a positive value, a contended resume
  returns -EAGAIN (it is -EINPROGRESS), and the `CONFIG_PM=n` stubs return 0
  and 1 (`__pm_runtime_resume()` returns 1, the idle and suspend stubs -ENOSYS,
  `pm_runtime_get_if_active()` -EINVAL). These would change a verdict.
- `pm_runtime_disable()` waits for queued work to run. `__pm_runtime_barrier()`
  cancels it.
- An irq-safe device's callbacks run with `power.lock` held, and the flag
  cannot be undone. The lock is released with interrupts left off, and
  `pm_runtime_reinit()` clears the flag and drops the parent.
- `PM_EVENT_RECOVER` selects the restore callbacks. It selects thaw.
- The allocation mask calls do not nest and need no lock; `lock_system_sleep()`
  returns a bool; `hibernate_acquire()` is a trylock of the transition mutex;
  wakeup source readers use RCU (it is SRCU); there is no managed
  `device_init_wakeup()`.

Readers A and B:

- **`pm_runtime_put()` returns int.** It returns void in this tree; the
  documentation still says int. Reader C knew the header and guessed the
  documentation agreed with it.
- `RPM_BLOCKED` and `RPM_TRANSPARENT` were not recognised. Both also said
  `pm_runtime_enable()` on a blocked device has no effect; it warns, dumps the
  stack and enables anyway.
- `pm_runtime_get_if_in_use()` also succeeds on a non-zero child count when
  `ignore_children` is clear.
- `wakeup_source_create()`, `wakeup_source_add()`, `wakeup_source_remove()` and
  `wakeup_source_destroy()` are static now, the list is exposed to BPF through
  three kfuncs, and `power.out_band_wakeup` exists.
- -ENOSYS for a missing callback (reader A): a NULL callback counts as success.

Readers A and C:

- irq_pm_check_wakeup() is gone; it is `irq_pm_handle_wakeup()`. Reader A also
  had dpm_noirq_begin(), cpuidle_pause() and suspend_console() in the device
  phases; none is there, and the console call is `console_suspend_all()`.
- Reader C offered pm_complete_with_resume_check() and legacy_resume(), which do
  not exist, and told an interrupt handler to put on any non-zero return from
  `pm_runtime_get_if_active()`; only 1 means a reference was taken.

## What the readers already knew

Where the files are and which document covers what; the entry points; the
order of the device phases, their lists and flags; the fields of the runtime PM
state (apart from reader B); the wrapper table and the conditional get helpers
(readers A and C); that a failed `pm_runtime_get_sync()` keeps its reference;
the managed helpers; forbid and allow; direct complete and the driver flags
(readers A and C); the notifier events; the hibernation sequence in outline.
These are dropped from the build set or shrunk to a pointer.

## Where the hand-written guide is stale

- It lists `pm_runtime_put()` among the functions that "can return 1". It
  returns void here, so code that reads its result does not build.
- Its wrapper lists leave out `pm_request_autosuspend()`,
  `pm_runtime_put_autosuspend()` and `pm_runtime_get_active()`, and it does not
  know the scope guards or that the autosuspend helpers now refresh the
  last-busy time themselves.
- The resume path "returns 1 when the device was already active" is incomplete:
  it also does so on a disabled device whose status and last status are both
  active, and `RPM_TRANSPARENT` makes a disabled resume return 0.
- The hibernation section says that in hybrid sleep the thaw callback runs "on
  wake from suspend". It runs before: devices are thawed so the image can be
  written, then `power_down()` calls `suspend_devices_and_enter()`, which runs
  the ordinary suspend callbacks, and wake-up runs the resume callbacks. The
  conclusion (do not skip the hardware resume in thaw when the mode is suspend)
  stands; the reason given does not. It also presents `PMSG_RECOVER` as what
  any failed image creation sends. Only an error from `swsusp_arch_suspend()`
  does: `in_suspend` is set just before it, and every earlier failure brings
  devices back with `PMSG_RESTORE`, so through the restore callbacks. A failed
  restore also recovers with `PMSG_RECOVER`. Its three cases are not all there
  are.
- "Drivers must use" `pm_sleep_ptr()` and `pm_ptr()` is stated as an absolute.
  The `SET_` macros with `__maybe_unused` callbacks are not marked deprecated,
  and hundreds of drivers correctly use `pm_sleep_ptr()` on the structure
  pointer when it holds only sleep callbacks.
- The interrupt handler example returns `IRQ_NONE` for `ret <= 0`.
  `pm_runtime_get_if_active()` returns -EINVAL when runtime PM is disabled and
  from the `CONFIG_PM=n` stub, where the device is powered; the ipu6 handler
  treats a negative value as "carry on without a reference".
- "Use `pm_runtime_put_sync()`" before removal is not enough when autosuspend
  is in use: through `rpm_idle()` it reaches `rpm_suspend()` with `RPM_AUTO` and
  may only arm the timer, which `__pm_runtime_barrier()` then cancels.
- Correct and kept as questions: the three base functions and their return
  values, the races that produce -EAGAIN and -EINPROGRESS, that
  `pm_runtime_get_noresume()` says nothing about the device's state.

## Left out of the build set

The hand-written guide is 1,202 words, so the build set holds 21 of the 66
questions, chosen by what someone reviewing a driver patch needs. Left out
although a reader got them wrong: the Kconfig relations; callback selection for
runtime PM and for the sleep phases; parents, children, suppliers and irq-safe
devices; calling context; the conditional get helpers and the failed-get leak
(the interrupt handler question carries the first, every reader knows the
second); the `CONFIG_PM=n` stubs; direct complete, the driver flags and smart
suspend (readers A and C were close, and `devices.rst` is accurate); async
ordering and rollback; interrupts around the noirq phase; the whole of the
suspend core (sequence, states, notifiers, locks, allocation mask, freezer);
the hibernation sequence and modes; all of wakeup; device PM QoS; the PM domain
object; debugging aids; and adding a field to `struct dev_pm_info`. A patch to
`kernel/power/` or to `drivers/base/power/wakeup.c` needs the source, not forty
words.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count. For reader B the check of the four questions from
`pm.rpm-enable-disable` to `pm.rpm-guards` came back empty the first time and
those four were run again on their own.

```
reader A: 137 corrections, 28% rewritten on average
reader B: 185 corrections, 75% rewritten on average
reader C: 127 corrections, 21% rewritten on average

question                      reader A      reader B      reader C
pm.core-files                   0% ( 0)        2% ( 2)        7% ( 1)
pm.docs                         0% ( 0)        4% ( 1)        0% ( 0)
pm.kconfig                     24% ( 1)       69% ( 4)        7% ( 2)
pm.entry-points                10% ( 0)       22% ( 2)       15% ( 2)
pm.rpm-fields                   6% ( 2)       75% ( 5)       18% ( 2)
pm.rpm-status-values            8% ( 1)       73% ( 1)        0% ( 0)
pm.rpm-flags                   13% ( 1)       64% ( 3)        0% ( 0)
pm.rpm-callback-lookup          7% ( 0)       90% ( 2)       15% ( 1)
pm.rpm-wrappers                 7% ( 2)       46% ( 6)       27% ( 2)
pm.rpm-resume-returns          37% ( 4)       86% ( 1)       13% ( 2)
pm.rpm-suspend-returns         14% ( 2)       77% ( 1)       67% ( 1)
pm.rpm-idle-returns             9% ( 2)       65% ( 1)       10% ( 1)
pm.rpm-put-return-type         54% ( 3)       79% ( 1)       36% ( 5)
pm.rpm-get-sync-error          15% ( 1)       91% ( 1)       18% ( 1)
pm.rpm-disabled-behaviour      40% ( 2)       83% ( 6)       30% ( 2)
pm.rpm-runtime-error           63% ( 3)       74% ( 1)       40% ( 4)
pm.rpm-conditional-get          7% ( 1)       77% ( 1)        0% ( 0)
pm.rpm-noresume                 4% ( 1)       92% ( 1)        7% ( 1)
pm.rpm-autosuspend             19% ( 1)       78% ( 2)       25% ( 1)
pm.rpm-enable-disable           8% ( 3)       85% ( 1)       17% ( 1)
pm.rpm-set-status               6% ( 1)       92% ( 1)       26% ( 1)
pm.rpm-devm                    15% ( 1)       78% ( 1)        0% ( 0)
pm.rpm-guards                  35% ( 1)       91% ( 1)        6% ( 1)
pm.rpm-parent-child            43% ( 2)       76% ( 3)       10% ( 1)
pm.rpm-device-links            32% ( 1)       82% ( 1)       24% ( 1)
pm.rpm-irq-safe                27% ( 1)       89% ( 2)       11% ( 2)
pm.rpm-atomic-context          16% ( 1)       82% ( 2)        2% ( 1)
pm.rpm-concurrency             16% ( 1)       79% ( 1)       37% ( 1)
pm.rpm-workqueue               68% ( 1)       80% ( 1)       63% ( 1)
pm.rpm-async-put-remove        18% ( 2)       89% ( 3)       12% ( 2)
pm.rpm-irq-handler             13% ( 2)       83% ( 3)       35% ( 5)
pm.rpm-forbid-allow             0% ( 0)       79% ( 2)        0% ( 0)
pm.rpm-no-pm-stubs              9% ( 1)       81% ( 1)       13% ( 2)
pm.sleep-phases                 6% ( 3)       19% ( 4)       21% ( 3)
pm.sleep-events                 6% ( 1)       39% ( 2)       21% ( 2)
pm.sleep-callback-lookup       24% ( 2)       73% ( 1)       21% ( 1)
pm.sleep-rpm-interaction       37% ( 3)       93% ( 4)       22% ( 3)
pm.sleep-blocked-enable        78% ( 3)       78% ( 3)       36% ( 2)
pm.sleep-direct-complete       14% ( 1)       67% ( 5)       13% ( 2)
pm.sleep-driver-flags          13% ( 1)       75% ( 4)        2% ( 1)
pm.sleep-smart-suspend         36% ( 3)       83% ( 4)       15% ( 1)
pm.sleep-force-suspend         37% ( 3)       81% ( 3)       21% ( 1)
pm.sleep-async                 64% ( 3)       80% ( 4)       23% ( 4)
pm.sleep-errors                58% ( 6)       87% ( 4)       31% ( 4)
pm.sleep-ops-macros            55% ( 3)       85% ( 6)       19% ( 3)
pm.sleep-noirq-irqs            51% ( 4)       84% ( 3)       31% ( 3)
pm.suspend-sequence            26% ( 5)       91% ( 9)       17% ( 4)
pm.suspend-states              16% ( 3)       81% ( 3)        7% ( 2)
pm.notifiers                    7% ( 0)       75% ( 3)       17% ( 1)
pm.locks-sleep                 28% ( 3)       77% ( 4)       17% ( 3)
pm.gfp-mask                    46% ( 2)       86% ( 3)       34% ( 3)
pm.freezer                     29% ( 2)       79% ( 5)       47% ( 5)
pm.hib-sequence                23% ( 3)       77% ( 6)       21% ( 1)
pm.hib-thaw-cases              15% ( 1)       79% ( 2)       47% ( 2)
pm.hib-modes                   18% ( 2)       74% ( 1)       27% ( 1)
pm.wakeup-sources              51% ( 4)       82% ( 3)       37% ( 3)
pm.wakeup-device-api           26% ( 1)       77% ( 3)       11% ( 2)
pm.wakeup-events               54% ( 3)       77% ( 3)        9% ( 1)
pm.wake-irq                    41% ( 3)       77% ( 2)        0% ( 0)
pm.wakeup-path                 51% ( 2)       91% ( 2)       39% ( 4)
pm.dev-qos                     35% ( 4)       85% ( 5)        0% ( 0)
pm.pm-domain-hooks             48% ( 3)       69% ( 3)       22% ( 2)
pm.debug                       20% ( 3)       53% ( 2)       30% ( 2)
pm.change-runtime-core         53% ( 4)       92% ( 4)       53% ( 4)
pm.change-sleep-core           64% ( 4)       85% ( 5)       46% ( 7)
pm.change-dev-pm-info          55% ( 4)       85% ( 5)       57% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `pm.sleep-async`, `pm.sleep-errors`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `pm.rpm-fields`, `pm.rpm-status-values`, `pm.rpm-callback-lookup`, `pm.rpm-get-sync-error`, `pm.rpm-conditional-get`, `pm.rpm-noresume`, `pm.rpm-parent-child`, `pm.rpm-atomic-context`, `pm.sleep-callback-lookup`, `pm.sleep-direct-complete`, `pm.sleep-driver-flags`, `pm.sleep-smart-suspend`, `pm.suspend-sequence`, `pm.locks-sleep`, `pm.hib-sequence`, `pm.wakeup-device-api`.

## Questions reorganised

Organised by subject, 41 questions before and 39 after: runtime PM helpers, runtime PM return
values, the runtime PM core, runtime PM during system sleep, device callbacks, the device phases
of system sleep, system-wide transitions and hibernation, wakeup. The driver-pattern hazards sit
with the helpers they are about, the two change questions with the core and the device phases.
Merged: `pm.rpm-conditional-get` and `pm.rpm-irq-handler` into `pm.rpm-get-if-active`;
`pm.rpm-callback-lookup` and `pm.sleep-callback-lookup` into `pm.callback-lookup`.
Reworded away from inventories: `pm.rpm-fields` (what `power.lock` covers), `pm.suspend-sequence`
(what is already stopped when a callback runs), `pm.sleep-smart-suspend`. Nothing is dropped.
