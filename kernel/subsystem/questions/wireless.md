# Questions: Wireless Subsystem Details

- guide: wireless.md
- title: Wireless Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/wireless-measurement.md` is the
wider set the readers were measured on and `catalogue/wireless-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## wifi.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## wifi.core-files: Core files

- section: Finding your way
- relevance: 3 - the readers know most of the layout; this is the part that moved

A table and nothing else, job to file: the simulated radio driver; mac80211's element parser; its
link management; its wrappers around driver callbacks and their tracepoints; the macro that splits
change flags between callbacks; the capability element layouts of each PHY generation. If the tree
has no file for a job, say so in the row. Start from `net/mac80211/` and
`drivers/net/wireless/virtual/`.

## wifi.object-model: cfg80211 and mac80211 structures

- section: Finding your way
- relevance: 4 - every function signature is phrased in these

A table of which structure represents each of these on the cfg80211 side, on the side a mac80211
driver sees and in mac80211's private wrapper, and how code gets from one to the next: a physical
device, a virtual interface, one link of an interface, a peer station and one link of it. Start
from `struct wiphy` and `struct ieee80211_hw`.

# BSS change callbacks and flags

## wifi.change-callbacks: Interface and link change callbacks

- section: BSS change callbacks and flags
- relevance: 5 - the subject of the hand-written guide

Which driver callbacks does mac80211 use to tell a driver that BSS configuration changed, and
where is the split of the change flags between them defined? What does mac80211 do when its own
code passes a change flag to the notify function for the other kind? If this tree has only one
such callback, say so and stop. Start from `ieee80211_link_info_change_notify()` and
`ieee80211_vif_cfg_change_notify()`.

## wifi.change-flag-tests: Flag tests in driver callbacks

- section: BSS change callbacks and flags
- relevance: 5 - a driver acts on a change only in the callback that receives the flag

What must hold for a change flag that a driver tests in `vif_cfg_changed` or in
`link_info_changed` of `struct ieee80211_ops`, in order for mac80211 to deliver the flag to that
callback? If this tree has only one such callback, say so and stop. Start from
`drv_vif_cfg_changed()` and `drv_link_info_changed()`.

## wifi.legacy-change-callback: Single change callback

- section: BSS change callbacks and flags
- relevance: 4 - most in-tree drivers were written against it

Does this tree have a single driver callback that receives all BSS change flags, and if so when
does mac80211 call it? Which combinations of it and the split callbacks does mac80211 refuse, and
where? Start from `ieee80211_bss_info_change_notify()`.

## wifi.single-notify-interface: Single notify function interface

- section: BSS change callbacks and flags
- relevance: 4 - mac80211 code chooses between this function and the split notify functions

What are the requirements for an interface that is passed into
`ieee80211_bss_info_change_notify()` in order to assure safe usage? Start from
`ieee80211_bss_info_change_notify()`.

## wifi.change-flag-coverage: Split macro and dropped flags

- section: BSS change callbacks and flags
- relevance: 5 - every reader read a rule off the macro that the tree breaks

Does any change flag reach a driver's interface-wide callback without being listed in
`BSS_CHANGED_VIF_CFG_FLAGS`, and if so how does mac80211 deliver it? For which interface types and
which links does `drv_link_info_changed()` drop a per-link flag before it reaches the driver, and
does it warn? Give flag and interface type names in full. Start from the callers of
`drv_vif_cfg_changed()` and the checks in `drv_link_info_changed()`.

## wifi.change-flag-data: Location of changed values

- section: BSS change callbacks and flags
- relevance: 4 - a driver handling a flag has to read the right structure

For each change flag that is delivered for the interface as a whole rather than for one link,
which field carries the new value? A table of flag and field. Start from
`struct ieee80211_vif_cfg` and `struct ieee80211_vif`.

## wifi.new-change-flag: Adding a change flag

- section: BSS change callbacks and flags
- relevance: 3 - the flag has to land on the right side of the split

When a flag is added to `enum ieee80211_bss_change`, which definitions in mac80211 decide the
callback that delivers it to a driver? What does mac80211 do with a flag that is added to the enum
and to none of those definitions? Does any in-tree driver have to change with it? Start from `enum
ieee80211_bss_change`.

# Links and stations

## wifi.link-state: Per-link interface state

- section: Links and stations
- relevance: 5 - every per-BSS field moved behind a link

What does each of the link bitmaps in `struct ieee80211_vif` mean? Where is the configuration of
the only link of an interface that is not a multi-link device? What are the requirements for
reading the per-link configuration pointers and for using `for_each_vif_active_link()`? Start from
`ieee80211_vif_is_mld()` and `for_each_vif_active_link()`.

## wifi.sta-state: Station state transitions

- section: Links and stations
- relevance: 4 - which transitions may fail is easy to get backwards

Which callback of `struct ieee80211_ops` reports each transition between the states of `enum
ieee80211_sta_state`, and which transitions may the driver fail? Which callbacks does mac80211
call for a driver that does not set that callback, and on which transitions? Start from `enum
ieee80211_sta_state` and `drv_sta_state()`.

## wifi.sta-teardown: Station teardown

- section: Links and stations
- relevance: 4 - decides how long a driver may keep a pointer to a station

Where in the teardown of a station does the RCU grace period fall, relative to the last transition
of `enum ieee80211_sta_state`? What are the requirements for a driver's use of the station pointer
after that transition returns, in order to assure safe usage? Start from `drv_sta_state()` and the
lifetime rules at the top of `net/mac80211/sta_info.c`.

## wifi.sta-lookup: Station lookup and lifetime

- section: Links and stations
- relevance: 4 - use after free of a station is a recurring bug

What protects a station entry from being freed while a driver or mac80211 code uses it? What are
the requirements for using a station pointer that `ieee80211_find_sta()` or another lookup
returned, in order to assure safe usage? Start from `ieee80211_find_sta()` and the lifetime rules
at the top of `net/mac80211/sta_info.c`.

# Driver registration and restart

## wifi.ops-validation: Callback set validation

- section: Driver registration and restart
- relevance: 4 - a driver with the wrong set of callbacks does not load

Which callbacks does mac80211 require when a driver allocates its hardware structure, which
combinations of callbacks does it reject, and what does the driver see when the check fails?
Start from `ieee80211_alloc_hw_nm()`.

## wifi.chanctx: Channel contexts

- section: Driver registration and restart
- relevance: 4 - two kinds of driver find the channel in different places

How does a mac80211 driver that does not manage channel contexts itself declare that, and what
does mac80211 do with a driver that leaves the channel context callbacks unset? Where does each
kind of driver find the current channel? Start from `struct ieee80211_chanctx_conf` and
`ieee80211_emulate_add_chanctx()`.

## wifi.chanctx-radio: Radio of a channel context

- section: Driver registration and restart
- relevance: 4 - a driver for a device with several radios has to find the right one

On a device with several radios, what identifies the radio that a `struct ieee80211_chanctx_conf`
belongs to? Start from `struct ieee80211_chanctx_conf`.

## wifi.mlo-requirements: Multi-link driver requirements

- section: Driver registration and restart
- relevance: 4 - registration fails unless all of them are met

What does `ieee80211_register_hw()` require of a driver that sets `WIPHY_FLAG_SUPPORTS_MLO`, and
what happens when a requirement is not met? Give each flag's enumerator name in full, and only
requirements that the code checks. Start from `ieee80211_register_hw()` and
`WIPHY_FLAG_SUPPORTS_MLO`.

## wifi.hw-restart: Hardware restart

- section: Driver registration and restart
- relevance: 4 - every driver with firmware uses it

What does `ieee80211_restart_hw()` do before it returns, and what does it leave to a work item? In
what order does `ieee80211_reconfig()` call back into the driver to restore state? What tells the
driver that the reconfiguration has finished? Start from `ieee80211_reconfig()`.

## wifi.hw-restart-failures: Reconfiguration locks and failures

- section: Driver registration and restart
- relevance: 4 - a driver callback can fail while the state is restored

Which locks does the work item that `ieee80211_restart_hw()` queues hold while it runs, and in
which order does it take them? What does `ieee80211_reconfig()` do when a driver callback fails
during the reconfiguration? Start from `ieee80211_reconfig()`.

# Locking and callback context

## wifi.wiphy-mutex: The wiphy mutex

- section: Locking and callback context
- relevance: 5 - most state is covered by one lock, and older knowledge of the locks is wrong

What does the wiphy mutex protect in cfg80211 and in mac80211, and which other sleeping locks does
`struct ieee80211_local` have? In what order are the wiphy mutex and the RTNL taken? Start from
`wiphy_lock()` and `struct ieee80211_local`.

## wifi.wiphy-mutex-assertions: Wiphy mutex assertions

- section: Locking and callback context
- relevance: 5 - the assertion and the pointer read have to name the lock that is held

How does code assert that the wiphy mutex is held, and how does it read an RCU-protected pointer
under the mutex? Start from `wiphy_lock()`.

## wifi.wiphy-work: Wiphy work items

- section: Locking and callback context
- relevance: 4 - the cancel semantics differ from ordinary work items

What kinds of deferred work does cfg80211 provide that run with the wiphy mutex held, and what
does each guarantee about the mutex and about timing? What are the requirements for calling their
cancel and flush functions in order to assure safe usage? Start from `wiphy_work_queue()`.

## wifi.cfg80211-ops-context: cfg80211 operation context

- section: Locking and callback context
- relevance: 4 - decides what a fullmac driver or mac80211 may do inside an operation

With which locks held does cfg80211 call the methods of a driver's `struct cfg80211_ops`, is the
RTNL among them as a rule, and may a method take the RTNL itself? How must a driver register or
unregister a net device from inside such a method compared with outside one? Start from
`cfg80211_register_netdevice()` and `nl80211_pre_doit()`.

## wifi.mac80211-ops-context: mac80211 callback context

- section: Locking and callback context
- relevance: 4 - sleeping in an atomic callback is a bug no diff shows

Where does the tree state, for a callback in `struct ieee80211_ops`, whether it must be atomic and
whether it is called without the wiphy mutex? What do the wrappers in `net/mac80211/driver-ops.h`
check before they call into the driver? Which of the interface and station iterators require the
wiphy mutex, and which take another lock? Start from the kerneldoc above `struct ieee80211_ops`
and `net/mac80211/driver-ops.h`.

## wifi.change-checklist: Changing a driver callback

- section: Locking and callback context
- relevance: 4 - the structures are shared by every wireless driver in the tree

When a callback is added to `struct cfg80211_ops` or `struct ieee80211_ops`, or its signature
changes, what besides the callers has to change with it, and where does each of those live? Does
the build fail when one is missed?

# Data path

## wifi.rx-tx-status-context: Receive and status entry points

- section: Data path
- relevance: 4 - the variants are not interchangeable

A table of the functions that a mac80211 driver chooses between to hand up a received frame and to
report transmit status, with the context each may be called from. What are the requirements for
calling more than one of them on one device? Start from `ieee80211_rx_napi()` and
`ieee80211_tx_status_skb()`.

## wifi.tx-info: Transmit control block

- section: Data path
- relevance: 4 - the parts overlap, and drivers read one after writing another

Where in the skb is `struct ieee80211_tx_info` stored, and which parts of it overlay each other?
What are the requirements for a driver's use of it, between receiving the frame and reporting
status, in order to assure safe usage? What does `ieee80211_tx_info_clear_status()` keep and what
does it clear? Start from `struct ieee80211_tx_info` and `ieee80211_tx_info_clear_status()`.

# Elements and scan results

## wifi.element-parsing: Parsing elements

- section: Elements and scan results
- relevance: 5 - the input is controlled by whoever is transmitting nearby

What do `for_each_element()` and `cfg80211_find_elem()` guarantee about the length of an element?
What are the requirements for reading the data of a found element in order to assure safe usage?
How does `ieee802_11_parse_elems_full()` return its result, and who frees it? Start from
`for_each_element()`, `cfg80211_find_elem()` and `ieee802_11_parse_elems_full()`.

## wifi.bss-refs: BSS entry references

- section: Elements and scan results
- relevance: 4 - leaks and use after free both happen here

Which cfg80211 functions return a `struct cfg80211_bss` with a reference held, and which function
drops it? What protects the element data that an entry points at? What are the requirements for
using an entry and its elements in order to assure safe usage? Start from
`cfg80211_inform_bss_data()` and `struct cfg80211_bss`.

# nl80211

## wifi.nl80211-command: Adding an nl80211 command

- section: nl80211
- relevance: 4 - the declarations decide what the handler may assume

What does the entry of an nl80211 command in `nl80211_ops` declare about the device, interface,
link and locks that it needs? What do `nl80211_pre_doit()` and `nl80211_post_doit()` do with those
declarations? What must be added when a command needs a combination that no existing command uses,
and what happens when it is missing? Start from `nl80211_pre_doit()` and `nl80211_ops`.

## wifi.nl80211-attrs: Adding an nl80211 attribute

- section: nl80211
- relevance: 4 - userspace ABI, and the policy is the input validation

Where must a new nl80211 attribute be placed in `include/uapi/linux/nl80211.h`, and what must be
added for it to `nl80211_policy`? How do handlers obtain and validate a link id? Start from
`nl80211_policy` and `NL80211_ATTR_MLO_LINK_ID`.

## wifi.nl80211-strict-validation: Strict attribute validation

- section: nl80211
- relevance: 4 - the policy entry is the input validation of a new attribute

From which attribute on does `nl80211_policy` validate strictly, and what does strict validation
require of the policy entry of a new attribute? Start from `nl80211_policy`.

# Model gaps

## wifi.model-gaps: Other mistakes models make

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
