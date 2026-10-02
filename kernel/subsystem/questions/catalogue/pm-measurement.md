# Questions: Power management (measurement set)

- guide: pm.md
- title: Power Management Subsystem

A wide set of questions about device power management: runtime PM, the device
phases of system sleep, the suspend and hibernation cores, and wakeup. It is
used to measure what a model already knows before deciding what the built guide
should spend its words on. The hand-written guide it will replace is 1,202
words. Generic PM domains (`drivers/pmdomain/`) have their own guide and are
left to it. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## pm.core-files: Core files

- section: Finding your way
- relevance: 4 - two files called main.c and two called qos.c
- words: 110

Which files hold runtime PM, the device phases of system sleep, wakeup sources,
wake interrupts, device PM QoS, the per-device sysfs attributes, the suspend
core, the hibernation core and its image code, the task freezer, and the
headers a driver includes for each? A table. Start from `drivers/base/power/`
and `kernel/power/`.

## pm.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules live only there, and some of it lags the code
- words: 70

Which files under `Documentation/` are the authority on runtime PM, on the
system sleep callbacks and driver flags, on PM notifiers, on freezing of tasks
and on debugging a failed suspend? Start from `Documentation/power/` and
`Documentation/driver-api/pm/`.

## pm.kconfig: Configuration symbols

- section: Finding your way
- relevance: 3 - decides which callbacks can ever run in a build
- words: 80

How do `CONFIG_PM`, `CONFIG_PM_SLEEP`, `CONFIG_SUSPEND`, `CONFIG_HIBERNATION`
and `CONFIG_HIBERNATE_CALLBACKS` relate: which selects or depends on which, and
which of them gates runtime PM, the sleep callbacks in `struct dev_pm_ops`, and
the hibernation callbacks? Start from `kernel/power/Kconfig`.

## pm.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

For each job (runtime-resume a device, runtime-suspend it, run the device
phases of a system suspend, enter a sleep state from the state file, hibernate,
restore an image at boot, report a wakeup event, freeze tasks), which function
do you start reading from? A table.

# Runtime PM

## pm.rpm-fields: Runtime PM state of a device

- section: Runtime PM state
- relevance: 4 - every rule is phrased in these fields
- words: 110

Which fields of `struct dev_pm_info` hold a device's runtime PM state (the
counters, the status, the disable depth, the pending request, the error, the
autosuspend timer), what is each one's initial value for a new device, and
which are protected by `power.lock` and which are atomics read without it?
Start from `pm_runtime_init()`.

## pm.rpm-status-values: Status values

- section: Runtime PM state
- relevance: 4 - one value is not a device state at all
- words: 70

List the values of `enum rpm_status` in this tree and say what each means.
Which field or fields of `struct dev_pm_info` hold a value of that type, and is
any value only ever stored in one of them?

## pm.rpm-flags: Flag argument bits

- section: Runtime PM state
- relevance: 3 - the wrappers differ only in these
- words: 70

What does each of the RPM flag bits passed to `__pm_runtime_idle()`,
`__pm_runtime_suspend()` and `__pm_runtime_resume()` mean? List every bit this
tree defines in `include/linux/pm_runtime.h`.

## pm.rpm-callback-lookup: Runtime callback selection

- section: Runtime PM state
- relevance: 4 - a driver callback can be shadowed without anyone noticing
- words: 80

When the core needs a device's runtime suspend, resume or idle callback, in what
order does it look at the PM domain, the device type, the class, the bus and the
driver, and when does it fall through to the driver's own callback? Start from
`__rpm_get_callback()`.

## pm.rpm-wrappers: Wrapper to base function map

- section: Runtime PM calls
- relevance: 5 - the return contract follows from which base function a wrapper reaches
- words: 130

Give a table of the runtime PM get, put, idle, suspend, autosuspend and resume
wrappers in `include/linux/pm_runtime.h`: for each, which of
`__pm_runtime_idle()`, `__pm_runtime_suspend()` and `__pm_runtime_resume()` it
calls, with which flags, and whether it also updates the last-busy time.

## pm.rpm-resume-returns: Resume path return values

- section: Runtime PM calls
- relevance: 5 - callers test for the wrong sign
- words: 90

What can `__pm_runtime_resume()` return, and under what condition is each value
produced: the positive value, zero for a synchronous and for an asynchronous
call, and each negative errno? Read the body of `rpm_resume()`, not the comment
above it.

## pm.rpm-suspend-returns: Suspend path return values

- section: Runtime PM calls
- relevance: 5 - a success value is mistaken for a failure
- words: 100

What can `__pm_runtime_suspend()` return, and under what condition is each value
produced: the positive value, zero, and each negative errno, including the ones
that come from a race with a resume? Start from `rpm_check_suspend_allowed()`
and `rpm_suspend()`.

## pm.rpm-idle-returns: Idle path return values

- section: Runtime PM calls
- relevance: 5 - differs between the put and the non-put callers
- words: 100

What can `__pm_runtime_idle()` return, and does the result for a device that is
already suspended depend on whether the caller passes `RPM_GET_PUT`? What
happens after the idle callback returns zero, and what if it returns non-zero?
Start from `rpm_idle()`.

## pm.rpm-put-return-type: Put helpers and their results

- section: Runtime PM calls
- relevance: 5 - code that checks a result that is not there no longer builds
- words: 70

What is the return type of each of `pm_runtime_put()`,
`pm_runtime_put_autosuspend()`, `pm_runtime_put_sync()`,
`pm_runtime_put_sync_suspend()` and `pm_runtime_put_noidle()` in this tree, and
for those that return a value, is a non-zero result an error a caller should
act on? Check the header, and say if the documentation disagrees with it.

## pm.rpm-get-sync-error: Usage counter after a failed get

- section: Runtime PM calls
- relevance: 5 - the classic leak
- words: 80

What is the state of the usage counter after `pm_runtime_get_sync()` returns an
error, and after `pm_runtime_resume_and_get()` does? What usage of either is
unsafe, and what that looks similar is correct? Does `pm_runtime_get()` differ?

## pm.rpm-disabled-behaviour: Calls while runtime PM is disabled

- section: Runtime PM calls
- relevance: 4 - probe paths and system sleep both hit it
- words: 100

When a device's disable depth is non-zero, what do the resume, suspend and idle
paths and the conditional get helpers each return? Is there a case in which a
resume on a disabled device reports success, and is there a flag that makes it
do so? Start from the top of `rpm_resume()`.

## pm.rpm-runtime-error: Sticky callback errors

- section: Runtime PM calls
- relevance: 4 - one failed callback can disable runtime PM for good
- words: 100

Which runtime PM callback failures are recorded in `power.runtime_error`, which
error codes are treated as transient and not recorded, what does every later
call return while the field is set, and how is it cleared? Does a failed resume
callback set it? What is done with a callback that returns -EACCES? Read
`rpm_suspend()`, `rpm_resume()` and `rpm_callback()`.

## pm.rpm-conditional-get: Conditional get helpers

- section: Runtime PM calls
- relevance: 4 - the only safe way to touch hardware without resuming it
- words: 90

What do `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()` each check
before taking a reference, what does each return in each case, and what do they
return when runtime PM is disabled or `CONFIG_PM` is off? Start from
`pm_runtime_get_conditional()`.

## pm.rpm-noresume: Counter-only helpers

- section: Runtime PM calls
- relevance: 4 - they say nothing about the device's state
- words: 80

What exactly do `pm_runtime_get_noresume()` and `pm_runtime_put_noidle()` do and
not do? What does the core do when a put would take the usage counter below
zero, and does `pm_runtime_put_noidle()` behave the same way? Start from
`rpm_drop_usage_count()`.

## pm.rpm-autosuspend: Autosuspend

- section: Runtime PM calls
- relevance: 4 - which helper refreshes the timestamp has changed
- words: 110

How does autosuspend decide when to suspend: which fields hold the delay and
the last-busy time, which helpers refresh the last-busy time themselves and
which leave it to the caller, what does a negative delay do, and what must a
driver undo on removal after `pm_runtime_use_autosuspend()`? Start from
`pm_runtime_autosuspend_expiration()`.

## pm.rpm-enable-disable: Enabling and disabling

- section: Setting runtime PM up
- relevance: 4 - probe and remove ordering bugs
- words: 110

In what state does a newly initialised device start with respect to runtime PM?
What do `pm_runtime_enable()` and `pm_runtime_disable()` do to the disable depth,
what does the first disable wait for and cancel, and what does it do with a
pending resume request? What does the core print for an unbalanced enable?
Start from `__pm_runtime_disable()` and `__pm_runtime_barrier()`.

## pm.rpm-set-status: Setting the status by hand

- section: Setting runtime PM up
- relevance: 4 - the status has to match the hardware before enabling
- words: 100

When may `pm_runtime_set_active()` and `pm_runtime_set_suspended()` be called,
what do they return otherwise, what do they do to the parent's child count and to
the device's suppliers, and when does setting a device active fail because of
its parent? Start from `__pm_runtime_set_status()`.

## pm.rpm-devm: Managed setup helpers

- section: Setting runtime PM up
- relevance: 3 - what each undoes decides whether remove needs code
- words: 70

Which device-managed runtime PM helpers does this tree provide, and what does
each one undo when the driver is unbound? Start from
`devm_pm_runtime_enable()` in `drivers/base/power/runtime.c`.

## pm.rpm-guards: Scope-based helpers

- section: Setting runtime PM up
- relevance: 4 - new code uses them and readers may never have seen them
- words: 100

Does `include/linux/pm_runtime.h` define cleanup guards or acquire macros for
holding a runtime PM reference over a scope? If so, list them, say what each
does on entry and on exit, how the variants differ when runtime PM is disabled,
and how a caller checks that the device was actually resumed.

## pm.rpm-parent-child: Parents and children

- section: Dependencies between devices
- relevance: 4 - explains -EBUSY and why a parent will not suspend
- words: 100

How does runtime PM keep a parent active while a child is: when is the parent's
child count changed, how is the parent resumed when a child resumes, what do
`power.ignore_children` and `power.no_callbacks` change, and what is done for
the parent after a child suspends? Start from `rpm_resume()` and `rpm_suspend()`.

## pm.rpm-device-links: Suppliers and consumers

- section: Dependencies between devices
- relevance: 3 - the second dependency graph, easy to forget
- words: 90

For a device link with `DL_FLAG_PM_RUNTIME`, when are the suppliers resumed and
when are their references dropped, which counter on the link tracks that, and
how is a supplier with runtime PM disabled treated? Start from
`rpm_get_suppliers()` and `__rpm_callback()`.

## pm.rpm-irq-safe: IRQ-safe devices

- section: Dependencies between devices
- relevance: 3 - changes locking, parents and suppliers at once
- words: 90

What does `pm_runtime_irq_safe()` change: how the callbacks are invoked with
respect to `power.lock` and interrupts, what happens to the parent, whether
suppliers are handled, and how a concurrent transition is waited for? How is it
undone?

## pm.rpm-atomic-context: Calling context

- section: Dependencies between devices
- relevance: 4 - sleeping in atomic context
- words: 80

Which runtime PM calls may be made from atomic context and which may sleep? What
do the `might_sleep_if()` checks in `__pm_runtime_idle()`, `__pm_runtime_suspend()`
and `__pm_runtime_resume()` test, and is a synchronous resume of a device that is
already active allowed from atomic context?

## pm.rpm-concurrency: Concurrent transitions

- section: Dependencies between devices
- relevance: 4 - the error returns look spurious unless expected
- words: 110

What does a caller get when another thread is already suspending or resuming the
same device: when does it wait, when does it get -EINPROGRESS, when -EAGAIN, and
what is a deferred resume? What does a caller of a put see when another thread
takes a reference before the idle check runs? Which lock serialises all of it?

## pm.rpm-workqueue: The PM work queue

- section: Dependencies between devices
- relevance: 4 - whether it is freezable decides what works during system sleep
- words: 80

Where is `pm_wq` allocated and with which flags? Is it freezable in this tree,
and what follows from that for an asynchronous resume request made while tasks
are frozen for a system suspend? Read the allocation, not the documentation.

## pm.rpm-async-put-remove: Asynchronous put before teardown

- section: Using runtime PM safely
- relevance: 4 - the pending work is cancelled and the device stays powered
- words: 100

What usage of an asynchronous put shortly before `pm_runtime_disable()`, device
removal or another operation that needs the device idle is unsafe, and what that
looks similar is correct? Say what happens to the queued request when runtime
PM is then disabled, and name the function responsible.

## pm.rpm-irq-handler: Hardware access from interrupt handlers

- section: Using runtime PM safely
- relevance: 4 - reads of powered-off registers
- words: 110

What usage of runtime PM in an interrupt handler that touches device registers
is unsafe, and what that looks similar is correct? What does a handler on a
shared line have to allow for, and what must the runtime suspend callback do
about a handler that may be running? Name in-tree drivers that show it.

## pm.rpm-forbid-allow: User-space control

- section: Using runtime PM safely
- relevance: 3 - a hidden reference held on behalf of sysfs
- words: 80

What do `pm_runtime_forbid()` and `pm_runtime_allow()` do to the usage counter
and the device, how do they relate to the control attribute in a device's power
directory in sysfs, and which other per-device attributes does
`drivers/base/power/sysfs.c` expose for runtime PM?

## pm.rpm-no-pm-stubs: Builds without runtime PM

- section: Using runtime PM safely
- relevance: 3 - error handling must not break the CONFIG_PM=n build
- words: 70

With `CONFIG_PM` disabled, what do `__pm_runtime_resume()`, `__pm_runtime_idle()`,
`__pm_runtime_suspend()`, `pm_runtime_get_if_active()`, `pm_runtime_enabled()` and
`pm_runtime_active()` return? Which common error checks misbehave as a result?

# System sleep: devices

## pm.sleep-phases: Device phases

- section: The device phases
- relevance: 5 - nothing else about system sleep makes sense without it
- words: 120

List in order the phases devices go through in a system suspend and in the
resume that follows, the function in `drivers/base/power/main.c` that runs
each, the list a device sits on after each phase, and the per-device flag each
phase sets or clears. Start from `dpm_suspend_start()`, `dpm_suspend_end()`,
`dpm_resume_start()` and `dpm_resume_end()`.

## pm.sleep-events: Transition messages

- section: The device phases
- relevance: 4 - which callback runs for which transition
- words: 110

Give a table of the `PM_EVENT_` values the PM core issues and, for each, which
member of `struct dev_pm_ops` is invoked in the main, late or early, and noirq
phases. Which events share a callback? Start from `pm_op()`.

## pm.sleep-callback-lookup: Sleep callback selection

- section: The device phases
- relevance: 4 - differs from runtime PM in when the driver is consulted
- words: 100

In the system sleep phases, in what order are the PM domain, type, class, bus
and driver consulted, and when is the driver's callback invoked although a
subsystem object with a `pm` pointer exists? Where do legacy bus `suspend` and
`resume` methods fit? Start from `device_suspend()` and `device_suspend_late()`.

## pm.sleep-rpm-interaction: Runtime PM during system sleep

- section: The device phases
- relevance: 5 - decides whether a runtime PM call in a sleep callback can work
- words: 120

What does the PM core do to each device's runtime PM state around each phase of
a system suspend and resume: where does it take and drop a usage reference,
where does it flush pending requests, where does it disable and re-enable
runtime PM? In which sleep callbacks can a driver still usefully call
`pm_runtime_get_sync()`?

## pm.sleep-blocked-enable: Devices never enabled for runtime PM

- section: The device phases
- relevance: 3 - a warning people will meet without knowing its cause
- words: 80

Does system suspend treat a device whose runtime PM is disabled when its prepare
phase runs specially? If so, what happens when a driver then enables runtime PM
before the transition completes, and where is that state cleared? Start from
`pm_runtime_block_if_disabled()`; if this tree has no such function, say so.

## pm.sleep-direct-complete: Direct complete

- section: Skipping work for suspended devices
- relevance: 4 - skips every callback but one
- words: 110

Under what conditions is `power.direct_complete` set for a device, what clears it
before the suspend phase acts on it, which callbacks are then skipped and which
still runs, and does it apply to hibernation transitions? Start from
`device_prepare()` and `device_suspend()`.

## pm.sleep-driver-flags: Driver flags

- section: Skipping work for suspended devices
- relevance: 4 - each changes what the core and the bus do
- words: 100

List the driver flags this tree defines for `dev_pm_set_driver_flags()` and say what each asks of
the PM core or the bus type, when a driver may set them, and who clears them.
Start from `include/linux/pm.h` and `Documentation/driver-api/pm/devices.rst`.

## pm.sleep-smart-suspend: Smart suspend and skipped resume

- section: Skipping work for suspended devices
- relevance: 4 - the flags interact across parents and suppliers
- words: 120

How are `power.smart_suspend`, `power.may_skip_resume` and `power.must_resume`
computed, what do `dev_pm_skip_suspend()` and `dev_pm_skip_resume()` return for
each kind of transition, and what does the noirq resume phase do to the runtime
PM status of a device whose resume is skipped? Start from
`device_prepare_smart_suspend()` and `device_suspend_noirq()`.

## pm.sleep-force-suspend: Reusing the runtime callbacks

- section: Skipping work for suspended devices
- relevance: 4 - the most common way drivers implement system sleep
- words: 120

What do `pm_runtime_force_suspend()` and `pm_runtime_force_resume()` do, step by
step: what they disable, which callback they call and how it is chosen, when the
resume is skipped, and what `power.needs_force_resume` and
`power.strict_midlayer` are for? Which macro wires them into a `dev_pm_ops`?

## pm.sleep-async: Asynchronous suspend and resume

- section: Ordering and failure
- relevance: 4 - ordering is kept by waiting, not by list order
- words: 120

How is ordering between parents, children, suppliers and consumers kept when
devices are suspended and resumed asynchronously: what is waited on, who starts
the async work for a device, which devices are started first, and what decides
whether a device is handled asynchronously at all? Start from `dpm_wait()` and
`dpm_async_fn()`.

## pm.sleep-errors: Failure and rollback

- section: Ordering and failure
- relevance: 4 - the unwind uses a different message from the one that failed
- words: 110

When a device callback fails in the prepare, suspend, late or noirq phase, what
stops, which devices are resumed, and with which message? Which return value
from a prepare callback is not treated as an error, and how does a pending
wakeup event abort a suspend in progress? Start from `resume_event()`.

## pm.sleep-ops-macros: Defining a dev_pm_ops

- section: Writing the callbacks
- relevance: 4 - the old macros need ifdefs or attributes, the new ones do not
- words: 120

Which macros for defining a `struct dev_pm_ops` and filling its members does
`include/linux/pm.h` recommend and which does it mark deprecated? What do
`pm_ptr()` and `pm_sleep_ptr()` expand to, which of them is right for the sleep
members, the runtime members and the pointer in `struct device_driver`, and what
usage leaves dead code or needs `__maybe_unused`?

## pm.sleep-noirq-irqs: Interrupts around the noirq phase

- section: Writing the callbacks
- relevance: 3 - explains what a noirq callback may rely on
- words: 100

What is done to device interrupts before the noirq suspend callbacks run and
after the noirq resume callbacks, which interrupts stay enabled, and how are
wakeup interrupts armed and disarmed? Start from `dpm_suspend_noirq()` and
`dpm_resume_noirq()`.

# System sleep: the core

## pm.suspend-sequence: Suspend sequence

- section: Suspend to RAM and to idle
- relevance: 4 - what is already stopped when a callback runs
- words: 130

List in order what `pm_suspend()` does before and after the device phases, as
far as this tree does each: filesystem sync, notifiers, filesystem freezing,
task freezing, console, platform hooks, non-boot CPUs, syscore, and where a
pending wakeup is checked. Can the filesystem sync be interrupted? Start from
`enter_state()`, `suspend_prepare()` and `suspend_enter()`.

## pm.suspend-states: Sleep states and platform hooks

- section: Suspend to RAM and to idle
- relevance: 3 - drivers branch on these
- words: 110

Which system sleep states does `include/linux/suspend.h` define, how does
suspend-to-idle differ from the states that use `struct platform_suspend_ops`,
and what do `pm_suspend_target_state`, `pm_suspend_via_firmware()`,
`pm_resume_via_firmware()` and `pm_suspend_no_platform()` tell a driver?

## pm.notifiers: PM notifiers

- section: Suspend to RAM and to idle
- relevance: 3 - the only hook that runs before tasks are frozen
- words: 90

Which events does the PM notifier chain deliver, in what order relative to task
freezing and the device phases, and what happens to the callbacks already run
when one of them fails a prepare event? Start from `register_pm_notifier()` and
`pm_notifier_call_chain_robust()`.

## pm.locks-sleep: System-wide locks

- section: Suspend to RAM and to idle
- relevance: 4 - what excludes what
- words: 100

Which locks serialise system-wide transitions and the device list:
what `system_transition_mutex`, `lock_system_sleep()`, `device_pm_lock()` and
`hibernate_acquire()` each protect, what `lock_system_sleep()` does to the
calling task besides taking the mutex, and why it returns a value.

## pm.gfp-mask: Allocation restrictions

- section: Suspend to RAM and to idle
- relevance: 3 - allocations in callbacks silently change behaviour
- words: 70

Between which points of a suspend or hibernation are `__GFP_IO` and `__GFP_FS`
masked out of allocations, which functions do it, do the calls nest, and what
must be held when they are called? Start from `pm_restrict_gfp_mask()`.

## pm.freezer: Freezing tasks

- section: Suspend to RAM and to idle
- relevance: 3 - decides which kernel threads and work items still run
- words: 110

What is frozen by `freeze_processes()` and what by `freeze_kernel_threads()`,
which of them suspend and hibernation each use, how does a kernel thread or a
work queue opt in, what happens on timeout, and does this tree also freeze
filesystems as part of the sequence? Start from `kernel/power/process.c`.

# Hibernation

## pm.hib-sequence: Hibernation sequence

- section: Hibernation
- relevance: 4 - devices are suspended and resumed more than once
- words: 130

List in order the device transitions of a hibernation and of the restore that
follows: which message is sent for creating the image, for bringing devices back
to write it, for powering off, in the boot kernel before the image is restored,
and in the restored kernel. Start from `hibernate()`, `hibernation_snapshot()`,
`create_image()` and `hibernation_restore()`.

## pm.hib-thaw-cases: Situations a thaw callback sees

- section: Hibernation
- relevance: 4 - skipping work in thaw is only right in one of them
- words: 120

In which distinct situations is a driver's thaw callback invoked, what happens to
the system after each, and which helpers let the callback tell them apart? What
usage of those helpers to skip resuming the hardware in thaw is unsafe, and what
is correct? Name an in-tree driver that does it. Start from
`pm_hibernate_is_recovering()`.

## pm.hib-modes: Hibernation modes

- section: Hibernation
- relevance: 3 - one mode runs a full suspend after the image is written
- words: 100

Which hibernation modes can be selected through the `disk` attribute, and what
does `power_down()` do for each? If one of them suspends the machine instead of
powering it off, which device callbacks run between writing the image and the
machine sleeping, and which on wake-up?

# Wakeup

## pm.wakeup-sources: Wakeup source objects

- section: Wakeup
- relevance: 3 - part of the old API is no longer exported
- words: 100

What is a `struct wakeup_source`, which functions may a driver call to create and
destroy one in this tree, are the separate create, add, remove and destroy steps
available to drivers, how is the global list protected for readers, and is any
of it exposed to BPF? Start from `wakeup_source_register()`.

## pm.wakeup-device-api: Device wakeup capability

- section: Wakeup
- relevance: 4 - can, may and should are three different things
- words: 100

What is the difference between `device_can_wakeup()` and `device_may_wakeup()`,
what does `device_init_wakeup()` do for true and for false, is there a managed
form, and what must a driver undo on removal? What changes without
`CONFIG_PM_SLEEP`?

## pm.wakeup-events: Reporting wakeup events

- section: Wakeup
- relevance: 3 - what aborts a suspend and what only counts
- words: 110

How do `pm_stay_awake()`, `pm_relax()`, `pm_wakeup_event()` and
`pm_wakeup_hard_event()` differ, how are events in progress and total events
counted, what does `pm_wakeup_pending()` test, and what do `pm_system_wakeup()`
and `pm_system_irq_wakeup()` add to that?

## pm.wake-irq: Dedicated wake interrupts

- section: Wakeup
- relevance: 3 - enabled and disabled by the core around runtime suspend
- words: 100

What do `dev_pm_set_wake_irq()`, `dev_pm_set_dedicated_wake_irq()` and
`dev_pm_set_dedicated_wake_irq_reverse()` set up, when does the core enable and
disable a dedicated wake interrupt relative to the runtime suspend and resume
callbacks, and what is done with wake interrupts at system suspend?

## pm.wakeup-path: Wakeup path

- section: Wakeup
- relevance: 3 - keeps parents and domains powered for a wakeup device
- words: 80

How is `power.wakeup_path` set and propagated during a system suspend, who reads
it, what effect does a wakeup-capable device have on direct complete, and what is
`power.out_band_wakeup` for? Start from `dpm_propagate_wakeup_to_parent()`.

# Other device-level pieces

## pm.dev-qos: Device PM QoS and runtime PM

- section: Other pieces
- relevance: 3 - one constraint value forbids runtime suspend outright
- words: 90

How does a device's resume-latency QoS constraint affect runtime suspend, which
value forbids it and which error does the caller see, what are the QoS flags,
and which locks protect `dev->power.qos`? Start from
`__dev_pm_qos_resume_latency()` and `drivers/base/power/qos.c`.

## pm.pm-domain-hooks: The PM domain object

- section: Other pieces
- relevance: 3 - it replaces the bus and driver callbacks wholesale
- words: 90

What is `struct dev_pm_domain`, what do its members besides `ops` do and when
does the driver core call them around probe and removal, and how must
`dev_pm_domain_set()` be called? Leave generic PM domains out.

## pm.debug: Debugging aids

- section: Other pieces
- relevance: 2 - saves a reviewer asking for the wrong test
- words: 90

What do the `pm_test` levels, `pm_print_times`, `pm_debug_messages`, the DPM
watchdog, `pm_trace` and the `suspend_stats` attributes each give you, and which
configuration symbol does each need?

# Changing the implementation

## pm.change-runtime-core: Changing the runtime PM core

- section: What a change must preserve
- relevance: 4 - the lock is dropped in the middle of every transition
- words: 120

What must a change to `rpm_suspend()`, `rpm_resume()` or `rpm_idle()` keep true:
where `power.lock` is dropped and retaken around callbacks, which status is
visible meanwhile, who is woken on `power.wait_queue`, the accounting and
tracepoints on a status change, and the tests that pin the return values? Name
the test file.

## pm.change-sleep-core: Changing the device phases

- section: What a change must preserve
- relevance: 4 - resume only undoes what the flags say was done
- words: 120

What must a change to the `device_suspend` and `device_resume` family keep true:
the movement between lists, completing `power.completion` on every path, the
per-device flags that tell resume what to undo, propagating errors through
`async_error`, and the runtime PM enable and disable pairing?

## pm.change-dev-pm-info: Adding per-device PM state

- section: What a change must preserve
- relevance: 3 - bitfields share a word
- words: 90

What does someone adding a field to `struct dev_pm_info` have to get right: the
configuration block it belongs in, where it is initialised, which flags are
owned by the PM core and which by drivers or subsystems, and what protects the
bitfields from concurrent read-modify-write?
