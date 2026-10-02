# Questions: Power Domain Subsystem

- guide: pmdomain.md
- title: Power Domain Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/pmdomain-measurement.md` is the
wider set the readers were measured on and `catalogue/pmdomain-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## pmdomain.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## pmdomain.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the generic PM domain core; its governors; the attach and
detach helpers that buses and the driver core call; the public header; the device tree bindings;
the cpuidle code that builds CPU domains. Then where provider drivers live, inside
`drivers/pmdomain/` and outside it, naming the largest group outside. Start from
`drivers/pmdomain/` and `drivers/base/power/common.c`.

# Domains

## pmdomain.flags: Domain flags

- section: Domains
- relevance: 5 - each flag changes when the core powers a domain off

By when must a provider have set the flags of a `struct generic_pm_domain`, and which flags does
the core set by itself? Which of the flags defined beside `GENPD_FLAG_PM_CLK` in
`include/linux/pm_domain.h` change whether the core powers the domain off, at runtime or at system
suspend?

## pmdomain.callback-context: Locks and callback context

- section: Domains
- relevance: 4 - decides whether the power callbacks may sleep

Which kinds of lock can protect a domain and what selects the kind, so in what context are the
provider's `power_on` and `power_off` callbacks called for each? On which path are those callbacks
and the power notifiers called without the domain lock? Start from `genpd_lock_init()`.

## pmdomain.device-callback-context: Per-device callback context

- section: Domains
- relevance: 4 - decides whether the per-device callbacks may sleep

Which of the per-device callbacks of a domain, such as `attach_dev` and `start`, does the core
call with the domain lock held? What does `pm_genpd_init()` do to the per-device callbacks of a
domain that sets `GENPD_FLAG_PM_CLK`?

## pmdomain.subdomains: Parent and child domains

- section: Domains
- relevance: 4 - a wrong link leaves a parent off under a powered child

What does a parent domain guarantee while one of its children is powered on: what does it count,
and when does the count change? Which combinations of power state or of flags does adding a
subdomain refuse? Which device tree property lets one provider node describe parents for several
of its domains, where a reader may offer another name? Start from `genpd_add_subdomain()`.

# Boot-time state and sync_state

## pmdomain.stay-on: Domains left on from boot

- section: Boot-time state and sync_state
- relevance: 5 - decides whether a domain the bootloader left on can ever go off

A provider registers a domain that is already powered on. What, if anything, stops the core from
powering it off before its consumers have probed: what sets that, what clears it, and which flag,
configuration or transition switches it off or ignores it? If this tree has no such mechanism,
say so and stop. Start from `pm_genpd_init()`.

## pmdomain.sync-state-wiring: Provider sync_state wiring

- section: Boot-time state and sync_state
- relevance: 5 - three cases, and one of them silently does nothing

How does a device tree provider end up with a sync_state callback in three cases: the provider
node has a device bound to a driver with no sync_state of its own, the driver has its own
sync_state callback, and there is no device for the node at all? What do the simple and the
onecell registration functions do differently? If the genpd core in this tree does nothing with
sync_state, say so and stop. Start from `of_genpd_add_provider_simple()`,
`of_genpd_add_provider_onecell()` and `dev_set_drv_sync_state()`.

## pmdomain.sync-state-timing: Timing of sync_state

- section: Boot-time state and sync_state
- relevance: 4 - whether it can be never

When does the driver core call a supplier's sync_state callback, what happens to a genpd
provider's domains if one consumer never probes, and which command line option or configuration
symbol changes that, and to what? Start from `fw_devlink_dev_sync_state()` in
`drivers/base/core.c`.

## pmdomain.unused-power-off: Powering off unused domains

- section: Boot-time state and sync_state
- relevance: 4 - ordering against other late cleanup

What does the genpd core run at the end of boot to power off unused domains: at which initcall
level, synchronously or not, and which domains does it leave alone? How does that relate in time
to the regulator core's disabling of unused regulators? Start from `genpd_power_off_unused()` and
`regulator_init_complete()`.

## pmdomain.sync-state-usage: Driver-specific sync_state callbacks

- section: Boot-time state and sync_state
- relevance: 5 - not visible in a diff that only adds the callback

What are the requirements for a genpd provider driver's own sync_state callback, with respect to
the domains the driver registered, in order to assure safe usage? What does
`of_genpd_sync_state()` do to every domain of the node it is given? Name in-tree drivers whose
sync_state callback shows it.

## pmdomain.boot-state-usage: Initial state and bootloader handover

- section: Boot-time state and sync_state
- relevance: 4 - a wrong initial state is either wasted power or a hang

What are the requirements for the `is_off` argument that a provider driver passes to
`pm_genpd_init()`, when the bootloader may have left the hardware running, in order to assure safe
usage? What must a driver that has to start from a powered-off domain do before it registers the
domain? Name examples under `drivers/pmdomain/`, reading each driver before naming it.

# Power transitions

## pmdomain.power-off-conditions: Runtime power-off conditions

- section: Power transitions
- relevance: 5 - every "why is this domain still on" question starts here

Under which conditions does `genpd_power_off()` decline to power a domain off? How does a caller
learn that it declined, or that the provider's callback refused?

## pmdomain.governors: Governors

- section: Power transitions
- relevance: 4 - no governor and the always-on governor both surprise people

What does each governor in `drivers/pmdomain/governor.c` decide at runtime power-off and at system
suspend? Which idle state is chosen in each of those two cases for a domain that has no governor?
What does the core do to a domain that is given `pm_domain_always_on_gov`? Start from
`drivers/pmdomain/governor.c`.

## pmdomain.governor-data: Data kept for governors

- section: Power transitions
- relevance: 4 - code that reads the data has to know when it exists

Does the core allocate or measure anything for a domain and its devices only when the domain has a
governor, and if so what? Start from `genpd_alloc_data()`.

## pmdomain.runtime-pm-callbacks: Runtime PM through a domain

- section: Power transitions
- relevance: 4 - the order of driver callback, device stop and domain power-off

When a device in a domain is runtime suspended and later resumed, in what order do the governor's
check, the device's own runtime PM callbacks, the domain's per-device stop and start operations
and the domain power-off and power-on happen, and what is skipped for an IRQ-safe device in a
domain that is not IRQ safe? Start from `genpd_runtime_suspend()`.

## pmdomain.performance-states: Performance state aggregation

- section: Power transitions
- relevance: 4 - votes, parents and runtime suspend interact

What counts towards a domain's performance state: its devices, its subdomains, a subdomain that
is powered off, a device that is runtime suspended? In what order are parent domains updated when
the state goes up and when it goes down? Start from `_genpd_set_performance_state()`.

## pmdomain.system-sleep: System suspend and resume

- section: Power transitions
- relevance: 4 - the domain is powered off in the noirq phase

In which phase of system sleep is a domain itself powered off and on again, and what makes
`genpd_finish_suspend()` leave it on? What does `genpd_prepare()` return when the generic prepare
returns a positive value? Start from `genpd_prepare()` and `genpd_finish_suspend()`.

## pmdomain.stay-on-system-sleep: Boot protection at system sleep

- section: Power transitions
- relevance: 4 - decides whether a domain left on from boot keeps power across suspend

Does the protection for a domain that was left on from boot stop the core from powering that
domain off at system suspend? Start from `genpd_sync_power_off()`.

# Provider drivers

## pmdomain.provider-registration: Registering a provider

- section: Provider drivers
- relevance: 5 - order and the checks made at registration

In what order must a provider driver call `pm_genpd_init()`, link subdomains and register the
device tree provider? What does `of_genpd_add_provider_onecell()` check about each domain, and
what does it do with an empty slot in its array? Start from `of_genpd_add_provider_onecell()`.

## pmdomain.provider-early-registration: Earliest provider registration

- section: Provider drivers
- relevance: 5 - decides which initcall level a provider may register from

How early in boot can `of_genpd_add_provider_simple()` or `of_genpd_add_provider_onecell()`
succeed, and what does each return when it is called before that?

## pmdomain.provider-removal: Removing a provider

- section: Provider drivers
- relevance: 5 - error paths in probe are where provider drivers go wrong

In what order must a provider be torn down, and under what conditions does removing a domain fail
and with which error? Start from `pm_genpd_remove()`, `of_genpd_del_provider()` and
`of_genpd_remove_last()`.

## pmdomain.provider-pitfalls: Provider probe and remove

- section: Provider drivers
- relevance: 4 - the recurring review comments on new provider drivers

What are the requirements for a provider driver's probe error path and remove path, for the
domains and the provider it registered, in order to assure safe usage? Which members of a `struct
generic_pm_domain` may a provider still write after `pm_genpd_init()`, and may it pass the same
structure to `pm_genpd_init()` again? Name an in-tree driver whose probe error path and remove are
complete, reading both before naming it.

# Consumer devices

## pmdomain.single-attach: Attaching one domain

- section: Consumer devices
- relevance: 4 - the signature and the flags have changed

What does each flag that `dev_pm_domain_attach()` accepts mean, and for which firmware? Is the
domain powered on at attach? What does `genpd_dev_pm_attach()` return when the provider has not
registered yet? Start from `genpd_dev_pm_attach()`.

## pmdomain.single-attach-caller: Single attach caller

- section: Consumer devices
- relevance: 4 - decides whether a driver has to attach the domain itself

Which code attaches a device that has exactly one entry in its `power-domains` property to its
domain, and at which point of the device's probe? Start from the callers of
`dev_pm_domain_attach()`.

## pmdomain.multi-attach: Attaching several domains

- section: Consumer devices
- relevance: 5 - the driver, not the bus, must power these domains

What does the bus do, and not do, at probe for a device that lists more than one power domain?
What do `dev_pm_domain_attach_list()` and `genpd_dev_pm_attach_by_id()` return for each domain,
and is that domain powered on when they return? What must the driver do to get the domain powered
and keep it so? Start from `dev_pm_domain_attach_list()` and `genpd_dev_pm_attach_by_id()`.

## pmdomain.attach-list-defaults: Attach list defaults

- section: Consumer devices
- relevance: 5 - the defaults decide what the driver still has to do for power

What does `dev_pm_domain_attach_list()` set up for each domain it attaches when the caller passes
no flags, and which of its flags change whether the domain is powered on?

## pmdomain.consumer-helpers: Consumer helpers

- section: Consumer devices
- relevance: 4 - several are new and each has a precondition

What are the requirements for calling each helper declared beside
`dev_pm_genpd_set_performance_state()` in `include/linux/pm_domain.h`, on a device attached to a
domain, in order to assure safe usage? A table, helper to what it requires of its caller.

# Model gaps

## pmdomain.model-gaps: Other mistakes models make

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
