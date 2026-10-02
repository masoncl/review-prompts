# Questions: Wireless (measurement set)

- guide: wireless.md
- title: Wireless Subsystem Details

A wide set of questions about the wireless stack: cfg80211 (`net/wireless/`),
nl80211, mac80211 (`net/mac80211/`) and what the drivers under
`drivers/net/wireless/` must do for them. It is used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 402 words, all of them about which
mac80211 callback receives which BSS change flag, so five questions are on
that and the rest sample the stack around it. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## wifi.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

Which files hold each of these: the nl80211 command handlers and attribute
policy, the cfg80211 core and its private structures, the wrappers cfg80211
calls driver operations through, scan results and the BSS table, regulatory,
cfg80211's connection state machine, mac80211's implementation of the cfg80211
operations, its wrappers around driver callbacks, interface and link
management, channel contexts, station entries, the client MLME, element
parsing, the transmit and receive paths, the two driver-facing headers, the
userspace header, and the simulated radio driver? A table of topic and file.
Start from `net/wireless/` and `net/mac80211/`.

## wifi.object-model: Object model

- section: Finding your way
- relevance: 4 - every function signature is phrased in these
- words: 100

Which structure represents each of these, and how do you get from one to the
next: a physical device as cfg80211 sees it and cfg80211's private wrapper
around it, a virtual interface as cfg80211 sees it, the device as a mac80211
driver sees it and mac80211's private wrapper, a virtual interface as a
mac80211 driver sees it and mac80211's private wrapper, one link of an
interface on each side, a peer station and one link of it on each side? A
table. Start from `struct wiphy` and `struct ieee80211_hw`.

## wifi.protocol-headers: Protocol definitions

- section: Finding your way
- relevance: 3 - the definitions are not all in one header
- words: 60

Where are the 802.11 frame formats, element ids and the capability element
layouts for each PHY generation defined, and which header holds the helpers
that iterate over and look up elements? Start from `include/linux/ieee80211.h`.

## wifi.docs-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - says what can be run before sending a patch
- words: 80

Where is the wireless stack documented in the tree (rendered documentation,
and the documentation sections inside headers and sources), which unit tests
live beside cfg80211 and mac80211 and how are internal functions made visible
to them, and what in the tree can exercise mac80211 without hardware? Start
from `Documentation/driver-api/80211/`.

# Locking and context

## wifi.wiphy-mutex: The wiphy mutex

- section: Locking
- relevance: 5 - most state is covered by one lock, and older knowledge of the locks is wrong
- words: 100

What does the wiphy mutex protect in cfg80211 and in mac80211, which other
sleeping locks does mac80211's per-device structure still have, how does code
assert that the mutex is held, how are RCU-protected pointers read under it,
and in what order is it taken with the RTNL? Start from `wiphy_lock()` and
`struct ieee80211_local`.

## wifi.wiphy-work: Wiphy work items

- section: Locking
- relevance: 4 - the cancel semantics differ from ordinary work items
- words: 90

What kinds of deferred work does cfg80211 provide that run with the wiphy
mutex held, what does each guarantee about the mutex and about timing, and
what usage of their cancel and flush functions is unsafe or incorrect, and
what that looks similar is correct? Start from `wiphy_work_queue()`.

## wifi.cfg80211-ops-context: cfg80211 operation context

- section: Locking
- relevance: 4 - decides what a fullmac driver or mac80211 may do inside an operation
- words: 80

With which locks held does cfg80211 call the methods of a driver's
`struct cfg80211_ops`, may a method take the RTNL itself, and how must a
driver register or unregister a net device from inside such a method compared
with outside one? Start from `cfg80211_register_netdevice()`.

## wifi.mac80211-ops-context: mac80211 callback context

- section: Locking
- relevance: 4 - sleeping in an atomic callback is a bug no diff shows
- words: 100

Which `struct ieee80211_ops` callbacks must be atomic, which are called
without the wiphy mutex, and what checks do mac80211's wrappers around the
callbacks make before calling into the driver? Start from the kerneldoc above
`struct ieee80211_ops` and `net/mac80211/driver-ops.h`.

## wifi.rx-tx-status-context: Receive and status entry points

- section: Locking
- relevance: 4 - the variants are not interchangeable
- words: 90

List the functions a mac80211 driver uses to hand up a received frame and to
report transmit status, the context each may be called from, and the rules
about mixing them on one device. Start from `ieee80211_rx_napi()` and
`ieee80211_tx_status_skb()`.

## wifi.iterators: Iterating interfaces and stations

- section: Locking
- relevance: 3 - each variant needs a different context
- words: 90

Which helpers does mac80211 give drivers to walk a device's interfaces and
stations, what lock or context does each need or take, may the callback sleep
in each, and which interfaces does each include or skip? A table. Start from
`ieee80211_iterate_interfaces()`.

# mac80211 driver interface

## wifi.ops-validation: Callback set validation

- section: Registration
- relevance: 4 - a driver with the wrong set of callbacks does not load
- words: 80

Which callbacks does mac80211 require when a driver allocates its hardware
structure, which combinations of callbacks does it reject, and what does the
driver see when the check fails? Start from `ieee80211_alloc_hw_nm()`.

## wifi.hw-flags: Hardware capability flags

- section: Registration
- relevance: 3 - adding a flag touches more than the enum
- words: 60

How does a mac80211 driver declare hardware capability flags and how are they
tested, and what besides the enum must be edited when a flag is added or
removed? Start from `enum ieee80211_hw_flags`.

## wifi.chanctx: Channel contexts

- section: Registration
- relevance: 4 - two kinds of driver find the channel in different places
- words: 90

How does a mac80211 driver that does not manage channel contexts itself
declare that, which callbacks make up the channel context set, where does each
kind of driver find the current channel, and what identifies the radio a
context belongs to on a device with several radios? Start from
`struct ieee80211_chanctx_conf` and `ieee80211_emulate_add_chanctx()`.

## wifi.change-callbacks: Interface and link change callbacks

- section: Configuration changes
- relevance: 5 - the subject of the hand-written guide
- words: 100

Which driver callbacks does mac80211 use to tell a driver that BSS
configuration changed, which change flags go to which, where is that split
defined, and what happens when mac80211 code passes a flag to the notify
function for the other kind? Start from `ieee80211_link_info_change_notify()`
and `ieee80211_vif_cfg_change_notify()`.

## wifi.change-flag-data: Location of changed values

- section: Configuration changes
- relevance: 4 - a driver handling a flag has to read the right structure
- words: 110

For each change flag that is delivered for the interface as a whole rather
than for one link, which field carries the new value? A table of flag and
field. Start from `struct ieee80211_vif_cfg` and `struct ieee80211_vif`.

## wifi.change-flag-coverage: Split macro coverage

- section: Configuration changes
- relevance: 4 - a rule read off one macro may have exceptions
- words: 70

Is every change flag that a driver can receive in its interface-wide callback
listed in the macro that defines the split? If not, which are not and how does
mac80211 deliver them, and which interface types restrict which flags? Give
flag and interface type names in full. Start from the callers of
`drv_vif_cfg_changed()` and the checks in `drv_link_info_changed()`.

## wifi.legacy-change-callback: Single change callback

- section: Configuration changes
- relevance: 4 - most in-tree drivers were written against it
- words: 80

Does this tree still have a single driver callback that receives all BSS
change flags, and if so exactly when is it called, may a driver implement it
together with the split callbacks, and what does mac80211 check about
multi-link interfaces on the path that calls it for everything? Start from
`ieee80211_bss_info_change_notify()`.

## wifi.misplaced-flag-handling: Misplaced flag handling

- section: Configuration changes
- relevance: 5 - the mistake the hand-written guide warns about
- words: 80

What handling of a change flag by a driver's interface-wide or per-link
callback is incorrect, what happens at run time when a driver makes that
mistake (does mac80211 warn, and is the driver's code for the flag ever
reached), and what that looks similar is correct? Name an in-tree driver that
shows the correct form. Start from `drv_vif_cfg_changed()` and
`drv_link_info_changed()`.

## wifi.link-state: Per-link interface state

- section: Multi-link operation
- relevance: 5 - every per-BSS field moved behind a link
- words: 100

How does a driver tell whether an interface is a multi-link device, what does
each of the link bitmaps in `struct ieee80211_vif` mean, where is the
configuration of the only link of an interface that is not one, and how must
the per-link configuration pointers be read? Start from
`ieee80211_vif_is_mld()` and `for_each_vif_active_link()`.

## wifi.link-activation: Changing active links

- section: Multi-link operation
- relevance: 3 - the callback order is what a driver has to survive
- words: 90

How does a driver ask mac80211 to change which links of a client interface
are active, from what context may each function be called, which callback
lets the driver refuse a combination, and in what order are the driver's
callbacks invoked when one link is swapped for another? Start from
`ieee80211_set_active_links()`.

## wifi.mlo-requirements: Multi-link driver requirements

- section: Multi-link operation
- relevance: 4 - registration fails unless all of them are met
- words: 80

What does mac80211 require of a driver that advertises multi-link support when
it registers its hardware: which callbacks, which hardware flags must be set
and which must not be, which channel context mode, and what happens when a
requirement is not met? Give each flag's enumerator name in full. Start from
`ieee80211_register_hw()` and `WIPHY_FLAG_SUPPORTS_MLO`.

## wifi.sta-state: Station state transitions

- section: Stations
- relevance: 4 - which transitions may fail is easy to get backwards
- words: 90

What are the states mac80211 moves a peer station through, which callback
reports each transition and which older callbacks is it exclusive with, which
transitions may the driver fail, and what may the driver assume about the
station pointer after the last transition returns? Start from
`enum ieee80211_sta_state` and `drv_sta_state()`.

## wifi.sta-lookup: Station lookup and lifetime

- section: Stations
- relevance: 4 - use after free of a station is a recurring bug
- words: 80

What protects a station entry from being freed while a driver or mac80211 code
uses it, what usage of a station pointer obtained from a lookup is unsafe, and
what that looks similar is correct? Start from `ieee80211_find_sta()` and the
lifetime rules at the top of `net/mac80211/sta_info.c`.

## wifi.tx-info: Transmit control block

- section: Data path
- relevance: 4 - the parts overlap, and drivers read one after writing another
- words: 90

How is the per-frame transmit information stored with the skb, which parts of
it overlap, and what usage of it by a driver between receiving the frame and
reporting status is unsafe, and what that looks similar is correct? Start from
`struct ieee80211_tx_info` and `ieee80211_tx_info_clear_status()`.

## wifi.txq: Software transmit queues

- section: Data path
- relevance: 3 - the pull model is mandatory in this tree or it is not
- words: 90

How does a mac80211 driver pull frames from mac80211's queues: which callback
tells it frames are waiting and is that callback optional, which functions
does it call to pick a queue and take a frame, what bracketing do the
scheduling calls need, and what helper exists for a driver with no scheduling
needs of its own? Start from `ieee80211_tx_dequeue()`.

## wifi.keys: Hardware key installation

- section: Data path
- relevance: 3 - the return values select software or hardware crypto
- words: 80

What may the key installation callback return for the set command and what
does each value make mac80211 do, may the disable command fail, what does the
link id in the key configuration mean, and how long may the driver keep the
key configuration pointer? Start from the section on hardware crypto
acceleration in `include/net/mac80211.h` and `drv_set_key()`.

## wifi.hw-restart: Hardware restart

- section: Recovery
- relevance: 4 - every driver with firmware uses it
- words: 90

What happens when a driver calls `ieee80211_restart_hw()`: what is stopped at
once, where does the reconfiguration run, which driver callbacks are replayed
and roughly in what order, what tells the driver it has finished, and what
happens when it fails? Start from `ieee80211_reconfig()`.

# cfg80211 and nl80211

## wifi.nl80211-command: Adding an nl80211 command

- section: nl80211
- relevance: 4 - the declarations decide what the handler may assume
- words: 110

What does an nl80211 command's entry in the operations table declare about the
device, interface, link and locks it needs, how are those declarations
encoded, what do the common handlers that run before and after every command
do with them, and what must be added when a command needs a combination that
no existing command uses? Start from `nl80211_pre_doit()` and `nl80211_ops`.

## wifi.nl80211-attrs: Adding an nl80211 attribute

- section: nl80211
- relevance: 4 - userspace ABI, and the policy is the input validation
- words: 90

Where must a new nl80211 attribute be placed in the userspace header, what
must be added to the policy, from which attribute on is validation strict, and
how do handlers obtain and validate a link id? Start from `nl80211_policy` and
`NL80211_ATTR_MLO_LINK_ID`.

## wifi.feature-flags: Advertising features

- section: nl80211
- relevance: 3 - one of the mechanisms is full
- words: 60

How does a driver advertise an optional capability to userspace through
nl80211, which of the mechanisms can still take new entries, and how does
cfg80211 code test for one? Start from `wiphy_ext_feature_set()`.

## wifi.bss-refs: BSS entry references

- section: Scan results
- relevance: 4 - leaks and use after free both happen here
- words: 90

Which cfg80211 functions return a referenced BSS entry and how is the
reference dropped, what protects the element data an entry points at, and what
usage of an entry or its elements is unsafe, and what that looks similar is
correct? Start from `cfg80211_inform_bss_data()` and `struct cfg80211_bss`.

## wifi.element-parsing: Parsing elements

- section: Frames from the air
- relevance: 5 - the input is controlled by whoever is transmitting nearby
- words: 110

Which helpers walk and find elements in a received frame, what do they
guarantee about an element's length, and what usage of a found element's data
is unsafe, and what that looks similar is correct? How does mac80211 return
the result of parsing a whole frame, and who frees it? Start from
`for_each_element()`, `cfg80211_find_elem()` and
`ieee802_11_parse_elems_full()`.

# Changing the implementation

## wifi.op-wrappers: Operation wrappers and tracing

- section: What a change must preserve
- relevance: 3 - a new operation is more than a new structure member
- words: 80

When a new operation is added to `struct cfg80211_ops` or to
`struct ieee80211_ops`, what else in cfg80211 and mac80211 has to be added so
that it is called and traced like the others, and what do the mac80211
wrappers assert? Start from `net/wireless/rdev-ops.h` and
`net/mac80211/driver-ops.h`.

## wifi.new-change-flag: Adding a change flag

- section: What a change must preserve
- relevance: 3 - the flag has to land on the right side of the split
- words: 70

What has to be decided and edited when a new BSS change flag is added to
mac80211, and does any in-tree driver have to be updated with it? Start from
`enum ieee80211_bss_change`.

## wifi.change-checklist: Changing a driver-facing interface

- section: What a change must preserve
- relevance: 4 - the structures are shared by every wireless driver in the tree
- words: 90

What must a change to a cfg80211 or mac80211 driver-facing structure or
callback keep working besides the function it edits: in-tree drivers, the
simulated driver, kerneldoc, tracepoints, the unit tests, the wireless
extensions compatibility code, the userspace ABI? Name where each lives.
