# Questions: Power management

- guide: pm.md
- title: Power Management Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/pm-measurement.md` is the wider
set the readers were measured on and `catalogue/pm-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## pm.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## pm.core-files: Core files

- section: Finding your way
- relevance: 4 - two files called main.c and two called qos.c

A table and nothing else, job to file and the header a driver includes for it: runtime PM; the
device phases of system sleep; wakeup sources; wake interrupts; device PM QoS; the per-device
sysfs attributes; the suspend core; the hibernation core and its image code; the task freezer.
Start from `drivers/base/power/` and `kernel/power/`.

# Runtime PM helpers

## pm.rpm-wrappers: Wrapper to base function map

- section: Runtime PM helpers
- relevance: 5 - the return contract follows from which base function a wrapper reaches

A table of the runtime PM get, put, idle, suspend, autosuspend and resume wrappers in
`include/linux/pm_runtime.h` that a driver chooses among: which of `__pm_runtime_idle()`,
`__pm_runtime_suspend()` and `__pm_runtime_resume()` each reaches, synchronously or not, and
whether it also refreshes the last-busy time itself.

## pm.rpm-guards: Scope-based helpers

- section: Runtime PM helpers
- relevance: 4 - new code uses them and readers may never have seen them

Does `include/linux/pm_runtime.h` define cleanup guards or acquire macros for holding a runtime
PM reference over a scope? If so, say what the variants to choose among do on entry and on exit,
how they differ when runtime PM is disabled, and how a caller checks that the device was actually
resumed. If not, say so and stop.

## pm.rpm-put-return-type: Put helpers and their results

- section: Runtime PM helpers
- relevance: 5 - code that checks a result that is not there no longer builds

What is the return type of each of `pm_runtime_put()`, `pm_runtime_put_autosuspend()`,
`pm_runtime_put_sync()`, `pm_runtime_put_sync_suspend()` and `pm_runtime_put_noidle()` in this
tree, and for those that return a value, is a non-zero result an error a caller should act on?
Check the header, and say if the documentation disagrees with it.

## pm.rpm-get-sync-error: Usage counter after a failed get

- section: Runtime PM helpers
- relevance: 5 - the classic leak

What is the state of the usage counter after `pm_runtime_get_sync()` returns an error, and after
`pm_runtime_resume_and_get()` does? What are the requirements for the error path of a caller of
each in order to assure safe usage? Does `pm_runtime_get()` differ?

## pm.rpm-noresume: Counter-only helpers

- section: Runtime PM helpers
- relevance: 4 - they say nothing about the device's state

What do `pm_runtime_get_noresume()` and `pm_runtime_put_noidle()` change, and what do they
guarantee about the runtime PM status of the device? What do `rpm_drop_usage_count()` and
`pm_runtime_put_noidle()` each do when a put would take the usage counter below zero? Start from
`rpm_drop_usage_count()`.

## pm.rpm-get-if-active: Conditional get and interrupt handlers

- section: Runtime PM helpers
- relevance: 4 - the only safe way to touch hardware without resuming it

What do `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()` each check before taking a
reference, and what does each return, including when runtime PM is disabled or `CONFIG_PM` is off?
Start from `pm_runtime_get_conditional()`.

## pm.rpm-irq-handler: Register access in interrupt handlers

- section: Runtime PM helpers
- relevance: 4 - a handler can run while the device is suspended or on its way there

What are the requirements for an interrupt handler that touches the registers of a device under
runtime PM, a handler on a shared line included, in order to assure safe usage? What are the
requirements for the runtime suspend callback of that device about a handler that may be running?
Name in-tree drivers that show it.

## pm.rpm-autosuspend: Autosuspend

- section: Runtime PM helpers
- relevance: 4 - which helper refreshes the timestamp has changed

What does `pm_runtime_autosuspend_expiration()` compute the expiry from, and what does a negative
autosuspend delay do? What must a driver undo on removal after `pm_runtime_use_autosuspend()`?
Start from `pm_runtime_autosuspend_expiration()`.

## pm.rpm-async-put-remove: Asynchronous put before teardown

- section: Runtime PM helpers
- relevance: 4 - the pending work is cancelled and the device stays powered

What are the requirements for dropping the last runtime PM reference shortly before
`pm_runtime_disable()`, device removal or another operation that needs the device suspended, in
order to assure safe usage, including when autosuspend is in use? What does `pm_runtime_disable()`
do with an idle or suspend request that is still queued, and which function does it?

# Runtime PM return values

## pm.rpm-resume-returns: Resume path return values

- section: Runtime PM return values
- relevance: 5 - callers test for the wrong sign

What can `__pm_runtime_resume()` return for a synchronous and for an asynchronous call, and under
what condition is each value produced? Read the body of `rpm_resume()`, not the comment above it.

## pm.rpm-suspend-returns: Suspend path return values

- section: Runtime PM return values
- relevance: 5 - a success value is mistaken for a failure

What can `__pm_runtime_suspend()` return, and under what condition is each value produced? Start
from `rpm_check_suspend_allowed()` and `rpm_suspend()`.

## pm.rpm-idle-returns: Idle path return values

- section: Runtime PM return values
- relevance: 5 - differs between the put and the non-put callers

What can `__pm_runtime_idle()` return, and does the result for a device that is already suspended
depend on whether the caller passes `RPM_GET_PUT`? What happens after the idle callback returns
zero, and what if it returns non-zero? Start from `rpm_idle()`.

## pm.rpm-disabled-behaviour: Calls while runtime PM is disabled

- section: Runtime PM return values
- relevance: 4 - probe paths and system sleep both hit it

When a device's disable depth is non-zero, what do the resume, suspend and idle paths each
return? Is there a case in which a resume on a disabled device reports success, and is there a
flag that makes it do so? Start from the top of `rpm_resume()`.

## pm.rpm-runtime-error: Sticky callback errors

- section: Runtime PM return values
- relevance: 4 - one failed callback can disable runtime PM for good

Which runtime PM callbacks have a failure recorded in `power.runtime_error`, and which of their
return values are not recorded? What do `rpm_suspend()`, `rpm_resume()` and `rpm_idle()` return
while the field is set, and what clears it? Read `rpm_suspend()`, `rpm_resume()` and
`rpm_callback()`.

## pm.rpm-concurrency: Concurrent transitions

- section: Runtime PM return values
- relevance: 4 - the error returns look spurious unless expected

What do `rpm_suspend()` and `rpm_resume()` do when the status of the device is `RPM_SUSPENDING` or
`RPM_RESUMING` on entry: when do they wait, and what do they return when they do not? What does
`power.deferred_resume` record, and what acts on it?

## pm.rpm-put-race: Put and get races

- section: Runtime PM return values
- relevance: 4 - the result of the put looks like a failure unless it is expected

What does a put helper that reaches `rpm_idle()` return when another thread takes a reference
before `rpm_idle()` checks the usage counter, and is that result an error for the caller to act
on?

# Runtime PM core

## pm.rpm-status-values: Status values

- section: Runtime PM core
- relevance: 4 - one value is not a device state at all

Which values of `enum rpm_status` do not describe the power state of a device, and what does each
of those stand for? Which of `power.runtime_status` and `power.last_status` can hold each of them?

## pm.rpm-fields: Runtime PM state and its lock

- section: Runtime PM core
- relevance: 4 - every rule is phrased in this state

Which members of the runtime PM state of a device does `power.lock` cover, and which are read or
written without it? What are the requirements for code that tests or changes
`power.runtime_status`, `power.usage_count` or `power.disable_depth` in order to assure safe
usage? In what state does `pm_runtime_init()` leave a new device? Start from `pm_runtime_init()`.

## pm.rpm-parent-child: Parents and children

- section: Runtime PM core
- relevance: 4 - explains -EBUSY and why a parent will not suspend

What does runtime PM guarantee about a parent while a child is active? What do
`power.ignore_children` and `power.no_callbacks` change about that? Which return value of
`rpm_resume()` or `rpm_suspend()` comes from the state of the parent and not from the device
itself? Start from `rpm_resume()` and `rpm_suspend()`.

## pm.rpm-atomic-context: Calling context

- section: Runtime PM core
- relevance: 4 - sleeping in atomic context

What are the requirements for calling `__pm_runtime_idle()`, `__pm_runtime_suspend()` and
`__pm_runtime_resume()` from atomic context in order to assure safe usage: what do their
`might_sleep_if()` checks test? May a synchronous resume of a device that is already active be
called from atomic context? What does `pm_runtime_irq_safe()` change?

## pm.change-runtime-core: Changing the runtime PM core

- section: Runtime PM core
- relevance: 4 - the lock is dropped in the middle of every transition

Which status is visible to other callers while `rpm_suspend()`, `rpm_resume()` and `rpm_idle()`
have dropped `power.lock` around a callback? At which status changes must waiters on
`power.wait_queue` be woken? Which in-tree test checks the return values of the three?

# Runtime PM during system sleep

## pm.sleep-rpm-interaction: Runtime PM in each phase

- section: Runtime PM during system sleep
- relevance: 5 - decides whether a runtime PM call in a sleep callback can work

In which phase of a system suspend and resume does the PM core take and drop a usage reference on
each device, and in which does it disable and re-enable runtime PM? What does that disable do
about a resume request that is pending? In which sleep callbacks can a driver therefore still
usefully call `pm_runtime_get_sync()`?

## pm.rpm-workqueue: The PM work queue

- section: Runtime PM during system sleep
- relevance: 4 - whether it is freezable decides what works during system sleep

Where is `pm_wq` allocated and with which flags? Is it freezable in this tree, and what follows
from that for an asynchronous resume request made while tasks are frozen for a system suspend?
Read the allocation, not the documentation.

## pm.sleep-blocked-enable: Devices never enabled for runtime PM

- section: Runtime PM during system sleep
- relevance: 3 - a warning people will meet without knowing its cause

Does system suspend treat a device whose runtime PM is disabled when its prepare phase runs
specially? If so, what happens when a driver then enables runtime PM before the transition
completes, and where is that state cleared? Start from `pm_runtime_block_if_disabled()`; if this
tree has no such function, say so.

## pm.sleep-force-suspend: Force suspend and force resume

- section: Runtime PM during system sleep
- relevance: 4 - the most common way drivers implement system sleep

Which callback do `pm_runtime_force_suspend()` and `pm_runtime_force_resume()` each call, and when
does each skip it? What are the requirements for a driver that uses the pair as its system sleep
callbacks, in order to assure safe usage?

## pm.sleep-force-flags: Flags behind force resume

- section: Runtime PM during system sleep
- relevance: 4 - the flags decide whether the pair calls a callback

What do `power.needs_force_resume` and `power.strict_midlayer` record, and what does each change
about what `pm_runtime_force_suspend()` and `pm_runtime_force_resume()` do?

# Device callbacks

## pm.sleep-ops-macros: Defining a dev_pm_ops

- section: Device callbacks
- relevance: 4 - the old macros need ifdefs or attributes, the new ones do not

Which macros for defining a `struct dev_pm_ops` and filling its members does `include/linux/pm.h`
mark deprecated, and which does it name in their place? Which of `pm_ptr()` and `pm_sleep_ptr()`
is to be used for the sleep members, the runtime members and the `pm` pointer in `struct
device_driver`?

## pm.callback-lookup: Callback selection

- section: Device callbacks
- relevance: 4 - a driver callback can be shadowed without anyone noticing

In what order do `__rpm_get_callback()` and `device_suspend()` consult the objects that can supply
a PM callback for a device? When does each of the two reach the callback of the driver although a
subsystem object with a `pm` pointer exists? Where do legacy bus `suspend` and `resume` methods
fit? Start from `__rpm_get_callback()`, `device_suspend()` and `device_suspend_late()`.

# Device phases of system sleep

## pm.sleep-driver-flags: Driver flags

- section: Device phases of system sleep
- relevance: 4 - each changes what the core and the bus do

A table of the driver flags this tree defines for `dev_pm_set_driver_flags()`: what each asks of
the PM core or of the bus type, when a driver may set them, and who clears them. Start from
`include/linux/pm.h` and `Documentation/driver-api/pm/devices.rst`.

## pm.sleep-direct-complete: Direct complete

- section: Device phases of system sleep
- relevance: 4 - skips every callback but one

Under what conditions is `power.direct_complete` set for a device, and what clears it again
before the suspend phase acts on it? Which callbacks are then skipped and which still runs? Does
it apply to hibernation transitions? Start from `device_prepare()` and `device_suspend()`.

## pm.sleep-smart-suspend: Smart suspend and skipped resume

- section: Device phases of system sleep
- relevance: 4 - the flags interact across parents and suppliers

What do `dev_pm_skip_suspend()` and `dev_pm_skip_resume()` guarantee a bus type or driver that
tests them, for each kind of transition? What in a parent, a supplier or the device's own state
stops its resume from being skipped? What does the noirq resume phase do to the runtime PM status
of a device whose resume is skipped? Start from `device_prepare_smart_suspend()` and
`device_suspend_noirq()`.

## pm.sleep-async: Asynchronous suspend and resume

- section: Device phases of system sleep
- relevance: 4 - ordering is kept by waiting, not by list order

What do `dpm_wait()` and its callers wait on to keep the order between devices that are related as
parent and child or as supplier and consumer, when devices are suspended and resumed
asynchronously? What decides whether a device is handled asynchronously? What order does the core
guarantee between two devices that have no such relation? Start from `dpm_wait()` and
`dpm_async_fn()`.

## pm.sleep-errors: Failure and rollback

- section: Device phases of system sleep
- relevance: 4 - the unwind uses a different message from the one that failed

When a device callback fails in one of the device suspend phases, which devices are resumed and
with which message? Which return values of a prepare callback does the core not treat as an error?
Start from `resume_event()`.

## pm.sleep-wakeup-abort: Pending wakeup events

- section: Device phases of system sleep
- relevance: 4 - a suspend can end without any callback having failed

In which device suspend phases does the core look for a pending wakeup event, and what does it do
when it finds one? Start from `pm_wakeup_pending()`.

## pm.change-sleep-core: Changing the device phases

- section: Device phases of system sleep
- relevance: 4 - resume only undoes what the flags say was done

What are the requirements for completing `power.completion` in the `device_suspend` and
`device_resume` family, in order to assure safe usage? How does a resume phase know which suspend
phases ran for a device, and onto which list does a device go when a phase fails part way?

# System-wide transitions and hibernation

## pm.suspend-sequence: System state during device callbacks

- section: System-wide transitions and hibernation
- relevance: 4 - what is already stopped when a callback runs

When the suspend, late and noirq callbacks of a device run during `pm_suspend()`, what has the
suspend core already stopped at each of the three? Under what condition are filesystems frozen,
and can the filesystem sync be interrupted? Start from `enter_state()`, `suspend_prepare()` and
`suspend_enter()`.

## pm.locks-sleep: System-wide locks

- section: System-wide transitions and hibernation
- relevance: 4 - what excludes what

Which of `system_transition_mutex`, `lock_system_sleep()`, `device_pm_lock()` and
`hibernate_acquire()` does code take to exclude what? What does `lock_system_sleep()` do to the
calling task besides taking the mutex, and what must be done with the value it returns?

## pm.hib-sequence: Hibernation sequence

- section: System-wide transitions and hibernation
- relevance: 4 - devices are suspended and resumed more than once

A table of the device transitions of a hibernation and of the restore that follows, in order:
for creating the image, for bringing devices back to write it, for powering off, in the boot
kernel before the image is restored, and in the restored kernel, the message that is sent and so
the callbacks a driver sees. Which message follows a failure at each stage? Start from
`hibernate()`, `hibernation_snapshot()`, `create_image()` and `hibernation_restore()`.

## pm.hib-thaw-cases: Situations a thaw callback sees

- section: System-wide transitions and hibernation
- relevance: 4 - skipping work in thaw is only right in one of them

In which situations does the hibernation core invoke the thaw callback of a driver, and what does
`pm_hibernate_is_recovering()` report in each? What are the requirements for a thaw callback that
skips resuming the hardware, in order to assure safe usage? Name an in-tree driver that shows it.
Start from `pm_hibernate_is_recovering()`.

# Wakeup

## pm.wakeup-device-api: Device wakeup capability

- section: Wakeup
- relevance: 4 - can, may and should are three different things

What is the difference between `device_can_wakeup()` and `device_may_wakeup()`, and what does
`device_init_wakeup()` do for true and for false? What must a driver undo on removal, and is
there a managed form that does it?

# Model gaps

## pm.model-gaps: Other mistakes models make

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
