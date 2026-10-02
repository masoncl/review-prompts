# Questions: Power domains (measurement set)

- guide: pmdomain.md
- title: Power Domain Subsystem

A wide set of questions about generic PM domains (genpd): the core in
`drivers/pmdomain/core.c`, its governors, the interface in
`include/linux/pm_domain.h`, how provider drivers register domains and how
consumer devices are attached to them. It is used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 735 words and is almost entirely
about one mechanism (domains left on from boot until sync_state), so most of
what is asked here cannot be in the built guide; the point is to find which few
things must be. The runtime PM core and the system sleep core belong to the
`pm` guide and are asked about only where genpd hooks into them. Individual
provider drivers are not covered. The trimmed set a guide is built from is
`../pmdomain.md`. Format: `../../../docs/subsystem-questions.md`.

# Where to look

## pmdomain.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 90

Which files hold the generic PM domain core, its governors, the attach and
detach helpers that buses and the driver core call, the public header, the
device tree bindings and the cpuidle code that builds CPU domains, and where
do provider drivers live, both inside and outside `drivers/pmdomain/`? A
table. Start from `drivers/pmdomain/` and `drivers/base/power/common.c`.

## pmdomain.entry-points: Entry points

- section: Finding your way
- relevance: 4 - the function to start reading from for each job
- words: 100

For each job (initialise a domain, register a device tree provider, attach a
device that has one domain, attach a device that has several, power a domain
on or off for runtime PM, suspend a device in a domain at system sleep, power
off unused domains at the end of boot), which function do you start reading
from? A table.

## pmdomain.docs-and-debug: Documentation and debugfs

- section: Finding your way
- relevance: 2 - saves looking for a document that may not exist
- words: 60

Is there prose documentation for generic PM domains under `Documentation/`
besides the device tree bindings, and if not what in the tree is the authority
on the flags and the interface? Which debugfs files show a domain's state, and
which kernel command line parameter does the genpd core define?

# The domain object

## pmdomain.struct-fields: Domain fields

- section: Domains
- relevance: 4 - which fields a provider may touch and which the core owns
- words: 100

Which fields of `struct generic_pm_domain` does a provider fill in before it
initialises the domain, which does the core own, and which of the core's
fields count attached devices, powered-on subdomains and progress through
system sleep?

## pmdomain.flags: Domain flags

- section: Domains
- relevance: 5 - each flag changes when the core powers a domain off
- words: 130

Give a table of the domain configuration flags this tree defines in
`include/linux/pm_domain.h` and what each makes the core do. By when must a
provider have set them?

## pmdomain.locks: Lock kinds

- section: Domains
- relevance: 4 - decides whether the power callbacks may sleep
- words: 70

Which kinds of lock can protect a domain, what selects the kind, and in what
context are the provider's power-on and power-off callbacks therefore called
for each kind? Start from `genpd_lock_init()`.

## pmdomain.lock-order: Lock ordering

- section: Domains
- relevance: 3 - lockdep catches most of it
- words: 70

In which order are a child domain's lock and its parent's lock taken, how is
lockdep told about the nesting, which global locks protect the list of domains
and the list of providers, and in which order are those two taken when both
are needed?

## pmdomain.subdomains: Parent and child domains

- section: Domains
- relevance: 4 - a wrong link leaves a parent off under a powered child
- words: 90

How are parent and child domains linked, what counter does a parent keep for
its children and when does it change, which combinations of power state or of
flags does adding a subdomain refuse, and which device tree property lets one
provider node describe parents for several of its domains? Start from
`genpd_add_subdomain()`.

# Power on and power off

## pmdomain.power-off-conditions: Runtime power-off conditions

- section: Runtime power transitions
- relevance: 5 - every "why is this domain still on" question starts here
- words: 110

List the conditions under which `genpd_power_off()` declines to power a domain
off. Which concern the domain's flags and state, which its devices, which its
subdomains and which the governor?

## pmdomain.power-on-path: Power-on path

- section: Runtime power transitions
- relevance: 3 - the unwinding on failure is easy to break
- words: 70

What does powering a domain on do to its parents and in what order, what is
undone if a parent or the domain itself fails to power on, and what does the
caller see? Start from `genpd_power_on()`.

## pmdomain.runtime-pm-callbacks: Runtime PM through a domain

- section: Runtime power transitions
- relevance: 4 - the order of driver callback, device stop and domain power-off
- words: 100

When a device in a domain is runtime suspended and later resumed, in what
order do the governor's check, the device's own runtime PM callbacks, the
domain's per-device stop and start operations and the domain power-off and
power-on happen, and what is skipped for an IRQ-safe device in a domain that
is not IRQ safe? Start from `genpd_runtime_suspend()`.

## pmdomain.notifiers: Power notifiers

- section: Runtime power transitions
- relevance: 3 - called under the domain lock
- words: 70

Which events do genpd power notifiers deliver, with what lock held, how many
notifiers may one device register, and what happens when a notifier rejects
the event sent before a transition? Start from `dev_pm_genpd_add_notifier()`.

# Boot, sync_state and unused domains

## pmdomain.stay-on: Domains left on from boot

- section: Boot-time state
- relevance: 5 - decides whether a domain the bootloader left on can ever go off
- words: 100

A provider registers a domain that is already powered on. What, if anything,
stops the core from powering it off before its consumers have probed: what
sets that, what clears it, and which flag or configuration switches it off?
If this tree has no such mechanism, say so and stop. Start from
`pm_genpd_init()`.

## pmdomain.sync-state-wiring: Provider sync_state wiring

- section: Boot-time state
- relevance: 5 - three cases, and one of them silently does nothing
- words: 120

How does a device tree provider end up with a sync_state callback in three
cases: the provider node has a device bound to a driver with no sync_state of
its own, the driver has its own sync_state callback, and there is no device
for the node at all? What do the simple and the onecell registration
functions do differently? If the genpd core in this tree does nothing with
sync_state, say so and stop. Start from `of_genpd_add_provider_simple()`,
`of_genpd_add_provider_onecell()` and `dev_set_drv_sync_state()`.

## pmdomain.sync-state-usage: Driver-specific sync_state callbacks

- section: Boot-time state
- relevance: 5 - not visible in a diff that only adds the callback
- words: 80

A genpd provider driver supplies its own sync_state callback. What usage is
unsafe or incorrect with respect to the domains it registered, and what that
looks similar is correct? Name in-tree drivers that show the correct form, and
say what `of_genpd_sync_state()` does to every domain of the node it is given.

## pmdomain.sync-state-timing: Timing of sync_state

- section: Boot-time state
- relevance: 4 - whether it can be never
- words: 80

When does the driver core call a supplier's sync_state callback, what happens
to a genpd provider's domains if one consumer never probes, and which command
line option or configuration symbol changes that, and to what? Start from
`fw_devlink_dev_sync_state()` in `drivers/base/core.c`.

## pmdomain.unused-power-off: Powering off unused domains

- section: Boot-time state
- relevance: 4 - ordering against other late cleanup
- words: 100

What does the genpd core run at the end of boot to power off unused domains:
at which initcall level, synchronously or not, and which domains does it leave
alone? How does that relate in time to the regulator core's disabling of
unused regulators? Start from `genpd_power_off_unused()` and
`regulator_init_complete()`.

## pmdomain.boot-state-usage: Initial state and bootloader handover

- section: Boot-time state
- relevance: 4 - a wrong initial state is either wasted power or a hang
- words: 100

How do in-tree provider drivers decide the initial state they pass when they
initialise a domain, what usage is unsafe when the bootloader left hardware
running, and what do drivers that must start from a known-off state do, where
in probe, and gated on what? Name examples under `drivers/pmdomain/`.

# Providers

## pmdomain.provider-registration: Registering a provider

- section: Provider drivers
- relevance: 5 - order and the checks made at registration
- words: 110

In what order does a provider driver initialise its domains, link subdomains
and register the device tree provider, what does registration check about each
domain, how early in boot can it succeed, and what does a onecell provider do
with an empty slot in its array? Start from `of_genpd_add_provider_onecell()`.

## pmdomain.provider-removal: Removing a provider

- section: Provider drivers
- relevance: 5 - error paths in probe are where provider drivers go wrong
- words: 100

In what order must a provider be torn down, under what conditions does
removing a domain fail and with which error, and what therefore has a probe
error path to undo? Start from `pm_genpd_remove()`, `of_genpd_del_provider()`
and `of_genpd_remove_last()`.

## pmdomain.provider-device: The domain's own device

- section: Provider drivers
- relevance: 3 - explains name clashes and where sync_state hangs
- words: 80

Each domain embeds a `struct device`. Which bus is it on, when is it added and
deleted, how is it named and which flag avoids a clash between two domains of
the same name, and what does the core use it for? Start from
`genpd_alloc_data()`.

## pmdomain.callbacks: Provider callbacks

- section: Provider drivers
- relevance: 4 - what may sleep and what runs under the lock
- words: 120

List the callbacks a provider can set in a domain (power on and off, attaching
and detaching a device, starting and stopping a device, performance state,
hardware mode), say when the core calls each and whether the domain lock is
held, and say what the flag for PM clocks installs.

## pmdomain.provider-pitfalls: Provider probe and remove

- section: Provider drivers
- relevance: 4 - the recurring review comments on new provider drivers
- words: 100

What usage in a provider driver's probe and remove paths is unsafe or
incorrect (order of calls, unwinding on error, flags changed after
initialisation, reuse of a domain structure), and what that looks similar is
correct? Name an in-tree driver whose probe error path and remove are
complete.

# Consumers

## pmdomain.single-attach: Attaching one domain

- section: Consumer devices
- relevance: 4 - the signature and the flags have changed
- words: 110

How does a device with exactly one entry in its `power-domains` property get
attached and by whom, what does `dev_pm_domain_attach()` take and what do the
flags it accepts mean, is the domain powered on at attach, and what is
returned when the provider has not registered yet? Start from
`genpd_dev_pm_attach()`.

## pmdomain.multi-attach: Attaching several domains

- section: Consumer devices
- relevance: 5 - the driver, not the bus, must power these domains
- words: 120

What does the bus do at probe for a device that lists more than one power
domain, which functions does its driver call to attach them, what kind of
device comes back for each domain, is that domain powered on by the attach,
and what must the driver do to get it powered and keep it so? Start from
`dev_pm_domain_attach_list()` and `genpd_dev_pm_attach_by_id()`.

## pmdomain.detach: Detaching

- section: Consumer devices
- relevance: 3 - can fail during system sleep
- words: 70

What does detaching a device from a domain do, when does it retry or fail,
what does its power-off argument change for a generic PM domain, and how is a
list of attached domains released? Start from `genpd_dev_pm_detach()`.

## pmdomain.consumer-helpers: Consumer helpers

- section: Consumer devices
- relevance: 4 - several are new and each has a precondition
- words: 120

List the helpers a consumer driver can call on a device attached to a domain
(the ones declared beside `dev_pm_genpd_set_performance_state()` in
`include/linux/pm_domain.h`), what each does, and what each requires of its
caller (no concurrent detach, a particular runtime PM state, one call per
device). A table.

# Performance states

## pmdomain.performance-states: Performance state aggregation

- section: Performance states
- relevance: 4 - votes, parents and runtime suspend interact
- words: 110

How is a domain's performance state computed from its devices and subdomains,
in what order are parent domains updated when the state goes up and when it
goes down, what happens to a device's vote while the device is runtime
suspended, and does a powered-off subdomain still vote? Start from
`_genpd_set_performance_state()`.

## pmdomain.opp-tables: OPP tables and required OPPs

- section: Performance states
- relevance: 3 - where the numbers come from
- words: 80

How does a domain that supports performance states get its OPP table, which
flag says firmware supplies it instead, and how is a consumer's required OPP
turned into a vote when the device is attached? Start from
`genpd_set_required_opp()`.

# Governors and idle states

## pmdomain.governors: Governors

- section: Governors and idle states
- relevance: 4 - no governor and the always-on governor both surprise people
- words: 110

Which governors does the tree provide and which callbacks does each fill in,
what does passing no governor mean for the idle state chosen at runtime
power-off and at system suspend, and which per-domain and per-device data is
allocated only when there is a governor? Start from
`drivers/pmdomain/governor.c`.

## pmdomain.idle-states: Domain idle states

- section: Governors and idle states
- relevance: 3 - ownership of the states array
- words: 90

How are a domain's idle states described in the device tree and parsed, who
owns and frees the resulting array, which end of the array is the deepest
state, and which of the latencies does the core update from its own
measurements? Start from `of_genpd_parse_idle_states()`.

## pmdomain.cpu-domains: CPU domains

- section: Governors and idle states
- relevance: 3 - confined to cpuidle, but the lock kind differs
- words: 90

What does marking a domain as a CPU domain change (lock, cpumask, governor),
which cpuidle drivers build such domains, and what are
`dev_pm_genpd_suspend()` and `dev_pm_genpd_resume()` for? Start from
`GENPD_FLAG_CPU_DOMAIN`.

# System sleep

## pmdomain.system-sleep: System suspend and resume

- section: System sleep
- relevance: 4 - the domain is powered off in the noirq phase
- words: 110

Which system sleep callbacks does a domain install for its devices, in which
phase is the domain itself powered off and on again, which counters decide
that, and what does the prepare callback return when the generic prepare
returns a positive value? Start from `genpd_prepare()` and
`genpd_finish_suspend()`.

## pmdomain.wakeup-path: Wakeup devices at suspend

- section: System sleep
- relevance: 3 - one flag, often forgotten
- words: 70

When is a domain kept powered through system suspend because of a wakeup
device, which domain flag and which per-device state decide it, and what is
different for a device whose wakeup is out of band? Start from
`genpd_finish_suspend()`.

## pmdomain.sleep-checks: Checks skipped at system sleep

- section: System sleep
- relevance: 3 - runtime guarantees that do not hold across suspend
- words: 70

Of the checks that stop a runtime power-off (the always-on flags, staying on
from boot, a per-device request to stay on, devices not runtime suspended, the
governor), which also apply in `genpd_sync_power_off()` and which do not?

# Changing the implementation

## pmdomain.core-change-checklist: Changing the core

- section: What a change must preserve
- relevance: 4 - a default that changes breaks boards nobody tested
- words: 100

What must a change to the genpd core's default power-on, power-off or timing
behaviour keep working: which kinds of provider depend on boot-time state,
which opt-out flags exist for them, which configurations (without OF, without
system sleep) build different code, and is there any in-tree test of genpd?
