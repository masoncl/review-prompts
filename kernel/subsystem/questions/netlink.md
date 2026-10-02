# Questions: Netlink and Generic Netlink

- guide: netlink.md
- title: Netlink / Generic Netlink uAPI Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/netlink-measurement.md` is the
wider set the readers were measured on and `catalogue/netlink-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## netlink.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## netlink.core-files: Core files

- section: Finding your way
- relevance: 4 - the code, the specs and the generator live in four trees

A table and nothing else, job to file or directory: the AF_NETLINK socket layer; the Generic
Netlink core; the policy dump; attribute parsing and validation; the kernel-internal headers for
messages, attributes and Generic Netlink; the uAPI headers; the YAML specs; their schemas; the
code generator; the user-space library; the tests and how they are run. Start from `net/netlink/`
and `tools/net/ynl/`.

# Families and operations

## netlink.family-registration: Family registration

- section: Families and operations
- relevance: 4 - registration is where a malformed family is caught

What does `genl_register_family()` refuse, and how does it assign the family ID and the multicast
group IDs? What does the core do with the value that a family's `bind` callback returns? Start
from `genl_register_family()`, `genl_validate_ops()` and `genl_bind()`.

## netlink.bind-callbacks: Multicast bind callbacks

- section: Families and operations
- relevance: 4 - a family that acts when a listener joins a group has to know when each callback runs

For which sockets, and at which points, does the Generic Netlink core call the `bind` and `unbind`
callbacks of `struct genl_family`? Start from `genl_bind()`.

## netlink.ops-forms: Operation table forms

- section: Families and operations
- relevance: 4 - three structs describe the same thing and new code uses one

What does each of `struct genl_ops`, `struct genl_small_ops` and `struct genl_split_ops` carry
that the others do not? What does `genl_validate_ops()` require of a family that supplies more
than one of them, and of the order and flags of its `struct genl_split_ops` entries? Start from
`struct genl_split_ops`.

## netlink.policy-source: Policy for a command

- section: Families and operations
- relevance: 5 - decides whether the handler sees validated attributes at all

Where does the core take the attribute policy and the maximum attribute number for a command
from when both the family and the operation can supply them, which of the operation table forms
inherit from the family and which never do, and what does the core do with the attributes of a
command that has no policy of its own? Start from `genl_family_rcv_msg_attrs_parse()` and the
comment on `struct genl_family`.

## netlink.header-flag-checks: Header and request flag checks

- section: Families and operations
- relevance: 4 - new commands get checks old ones do not, and classic habits fail them

What does `genl_header_check()` check in the message headers and in `nlmsg_flags`, and for which
commands does it make those checks? What does `Documentation/userspace-api/netlink/intro.rst` say
a new family should do about the request-type flags of classic Netlink, the ones specific to GET,
NEW and DEL requests? Start from `genl_header_check()` and the request flags section of
`Documentation/userspace-api/netlink/intro.rst`.

## netlink.op-permissions: Permission flags

- section: Families and operations
- relevance: 4 - the two flags check different capabilities

Which flags on an operation make the core check a capability before calling the handler, what
exactly does each check, and what does a family have to set to be reachable from a network
namespace other than the initial one? Start from `genl_family_rcv_msg()`.

## netlink.core-locking: Locks in the core

- section: Families and operations
- relevance: 4 - handlers rely on serialisation that parallel families do not get

Which locks do the Generic Netlink core and the socket layer under it take, and which of them
are held while a doit, a dump start, a dumpit round and a dump done callback run, for a family
that sets `parallel_ops` and for one that does not? When can a done callback run without the
lock the rounds ran under? Start from `genl_rcv()` and `genl_family_rcv_msg_dumpit()`.

## netlink.notifications: Sending notifications

- section: Families and operations
- relevance: 4 - the helpers differ in who receives the message

Which of the helpers that send a Generic Netlink notification also delivers to a requester that
set the echo flag, and what does it require of the `struct genl_info` it is passed? How is the
group argument of these helpers numbered? Start from `genl_notify()` and `genl_info_init_ntf()`.

## netlink.multicast-helpers: Multicast helpers and namespaces

- section: Families and operations
- relevance: 4 - the helpers differ in which network namespaces receive the message

To which network namespaces does each of `genlmsg_multicast()`, `genlmsg_multicast_netns()` and
`genlmsg_multicast_allns()` deliver a notification, and what does each require of its caller? What
does `genl_has_listeners()` tell a caller before it builds a message? Start from
`include/net/genetlink.h`.

# Policies and parsing

## netlink.policy-types: Policy attribute types

- section: Policies and parsing
- relevance: 4 - each type implies a different length check

A table of the attribute types a policy entry chooses between: what is checked about the payload
length under liberal and under strict validation, and what the `len` field means for that type.
Start from the comment on `struct nla_policy` and the length tables at the top of
`lib/nlattr.c`.

## netlink.policy-macros: Policy initialiser macros

- section: Policies and parsing
- relevance: 4 - a declared constraint replaces open-coded checks

Which attribute types does each policy initialiser macro defined in `include/net/netlink.h`
accept? Which constraints can `NLA_POLICY_RANGE()`, `NLA_POLICY_MIN()` and `NLA_POLICY_MAX()` not
express, and which initialiser is used for them? Start from `include/net/netlink.h`.

## netlink.string-attributes: String attributes

- section: Policies and parsing
- relevance: 4 - the terminator is counted in one place and not in another

What does each of `NLA_STRING` and `NLA_NUL_STRING` require of the payload, and does the length
limit in the policy count the terminating NUL? What are the requirements for reading a string
attribute through `nla_data()`, or for copying it out with `nla_strscpy()` or `nla_strdup()`, in
order to assure safe usage? Start from `validate_nla()` and `nla_strscpy()`.

## netlink.validation-levels: Validation strictness

- section: Policies and parsing
- relevance: 5 - which checks a handler may assume were done

Which parse entry points apply every check in `enum netlink_validation` and which apply none, and
how does a policy make only its newer attributes strict? Which per-operation flags turn checks off
for a Generic Netlink command? Give the flag names in full. Start from `enum netlink_validation`.

## netlink.dump-validation-flag: Dump validation flag

- section: Policies and parsing
- relevance: 5 - the flag decides whether a dump handler sees validated attributes

What does `GENL_DONT_VALIDATE_DUMP` change for a dump command in each of `struct genl_ops`,
`struct genl_small_ops` and `struct genl_split_ops`? Start from `genl_cmd_full_to_split()` and
`genl_start()`.

## netlink.unknown-attributes: Unknown attributes

- section: Policies and parsing
- relevance: 4 - ignored versus rejected changes what user space may send

What does attribute parsing do with an attribute whose type is zero, above the maximum the
caller passed, or present in the policy array with no type given, and how does that depend on
the validation flags? Start from `__nla_validate_parse()` and `validate_nla()`.

## netlink.nested-attributes: Nested attributes

- section: Policies and parsing
- relevance: 4 - validated is not the same as parsed

When a policy entry points at a nested policy, what has been done to the contents of the nest by
the time the handler runs, and what must the handler still do itself? What do `nla_parse_nested()`
and `nla_nest_start()` each do about the `NLA_F_NESTED` bit in the attribute type? Start from
`nla_parse_nested()` and `nla_nest_start()`.

## netlink.repeated-attributes: Repeated attributes

- section: Policies and parsing
- relevance: 4 - the parsed table hides all but one instance

When the same attribute type appears more than once at one level of a message, what does the
parsed attribute table hold for it, and how does a handler read every instance? Name in-tree code
that does.

## netlink.type-agreement: Policy types and accessor helpers

- section: Policies and parsing
- relevance: 5 - nothing checks it at build time

Where is the type of one attribute written down, and which of those places does the compiler or
the core check against each other? What are the requirements for calling a typed get or put
helper, such as `nla_get_u32()` or `nla_put_u32()`, on an attribute in order to assure safe usage,
given the type in the attribute's policy entry? Name in-tree code that shows it.

# Dumps

## netlink.dump-lifecycle: Dump lifecycle

- section: Dumps
- relevance: 5 - the return value protocol is unwritten and has changed

How does `netlink_dump()` read each possible return value of a dumpit callback, and when does it
write the terminating message? In whose context are the start, dumpit and done callbacks called?
Start from `netlink_dump()` and `__netlink_dump_start()`.

## netlink.dump-buffer-size: Buffer size for a round

- section: Dumps
- relevance: 5 - an object that does not fit the buffer stops the dump

How large is the buffer that `netlink_dump()` allocates for one round, and how does a dumpit
callback whose object does not fit get a larger one? Start from `netlink_dump()`.

## netlink.dump-state: Dump state between rounds

- section: Dumps
- relevance: 4 - the old way is still in the struct

Where does a dumpit callback keep its position between rounds: which member of
`struct netlink_callback` is the current way, which is deprecated, and how is the size of what is
kept there checked? How does a Generic Netlink dumpit reach the parsed request attributes, the
family and the extended ACK? Start from `genl_dumpit_info()`.

## netlink.dump-consistency: Dump consistency

- section: Dumps
- relevance: 4 - a dump that silently skips objects is a bug user space cannot see

How does a dump tell user space that the set of objects changed while it was being dumped, what
does the dumper have to maintain and where does it record it, and which value may the counter
never take? Start from `nl_dump_check_consistent()`.

# Extended ACK

## netlink.extack-helpers: Extended ACK helpers

- section: Extended ACK
- relevance: 4 - several macros, each with a catch

What limits the text of `NL_SET_ERR_MSG_FMT()`, and what does `NL_SET_ERR_MSG()` require of the
string it is passed? What do `NL_SET_BAD_ATTR()`, `NL_SET_ERR_MSG_ATTR_POL()` and
`NL_SET_ERR_ATTR_MISS()` each record that the others do not? Start from `include/linux/netlink.h`.

## netlink.extack-delivery: Delivery to user space

- section: Extended ACK
- relevance: 4 - some fields are dropped on success

What of the extended ACK is sent to user space when the operation failed and what when it
succeeded, what does the socket have to have enabled, and in which messages of a dump can it
appear and under what condition? Start from `netlink_ack_tlv_len()`.

## netlink.extack-usage: Attribute pointer and message text

- section: Extended ACK
- relevance: 4 - the difference between a usable error and EINVAL

What are the requirements for setting the bad attribute pointer and the message of a `struct
netlink_ext_ack` in order to assure correct usage, and what does
`Documentation/userspace-api/netlink/intro.rst` ask of a family that sets them? Start from
`netlink_ack_tlv_fill()` and the extended ACK part of
`Documentation/userspace-api/netlink/intro.rst`.

# uAPI design rules

## netlink.frozen-uapi: Frozen properties

- section: uAPI design rules
- relevance: 5 - the reason every other rule here exists

Which properties of a Netlink family are fixed once a kernel carrying it has been released,
which kinds of change remain possible afterwards, and how does user space find out what a
running kernel supports? Start from `Documentation/userspace-api/netlink/intro.rst`.

## netlink.reply-or-ack: Reply versus ACK

- section: uAPI design rules
- relevance: 5 - fixed for ever by the first release

What does `Documentation/core-api/netlink.rst` say a command that creates or changes an object
should send back to the requester, what does it say about changing that choice after a release,
and what does it say about relying on the echo flag for it? Start from
`Documentation/core-api/netlink.rst`.

## netlink.id-numbering: Command and attribute numbering

- section: uAPI design rules
- relevance: 4 - reviewers ask for this on every new family

What do `Documentation/core-api/netlink.rst` and
`Documentation/userspace-api/netlink/genetlink-legacy.rst` say about the first value of an
attribute or command enum, about the IDs of a request, its reply and its notifications, and about
the message ID model of a new family? Start from `Documentation/core-api/netlink.rst`.

## netlink.existing-family-numbering: Numbering in existing families

- section: uAPI design rules
- relevance: 4 - a rule for new families may not apply to a command added to an old one

What do `Documentation/core-api/netlink.rst` and
`Documentation/userspace-api/netlink/genetlink-legacy.rst` say about numbering a command or
attribute that is added to an existing family which does not follow the rules for new families?
Start from `Documentation/core-api/netlink.rst`.

## netlink.attribute-design: Attribute design preferences

- section: uAPI design rules
- relevance: 4 - the choices reviewers push back on

What do the guidelines prefer for carrying an array, for carrying a C structure, for the width
of an integer, and for integers narrower than 32 bits, and what reason, if any, do they give for
each? Give only reasons the documents state. Start from
`Documentation/userspace-api/netlink/specs.rst` and
`Documentation/userspace-api/netlink/genetlink-legacy.rst`.

# Specs and generated code

## netlink.spec-levels: Schema levels

- section: Specs and generated code
- relevance: 4 - what a spec may contain depends on its level

Which schema levels can a spec declare, and which does
`Documentation/userspace-api/netlink/specs.rst` say a new family should use? How is a spec checked
against its schema and linted? Start from `Documentation/netlink/` and `tools/net/ynl/Makefile`.

## netlink.generated-code: Generated kernel code

- section: Specs and generated code
- relevance: 5 - hand edits to generated files are lost

How is a kernel file that was generated from a spec recognised, and how is it regenerated? Of the
policies, the operation table and the family structure, which does the generator emit at each
schema level? Start from `tools/net/ynl/ynl-regen.sh` and `net/core/netdev-genl-gen.c`.

## netlink.kernel-policy-property: The kernel-policy property

- section: Specs and generated code
- relevance: 4 - the documentation and the generator may not agree

What does each value of the `kernel-policy` property of a spec make the generator emit, what is
the default according to the documentation and according to the generator and the schema, and
which schema levels accept the property at all? Start from `tools/net/ynl/pyynl/ynl_gen_c.py`.

## netlink.spec-checks: Attribute checks in a spec

- section: Specs and generated code
- relevance: 4 - this is how a spec declares validation

What policy initialiser does each property under an attribute's `checks` turn into? Give the macro
names in full. Which ways of writing a string length limit does
`Documentation/core-api/netlink.rst` describe, and which of them does `get_limit_str()` handle?
Start from `Documentation/core-api/netlink.rst`, `Documentation/netlink/genetlink.yaml` and
`get_limit_str()` in `tools/net/ynl/pyynl/ynl_gen_c.py`.

# Model gaps

## netlink.model-gaps: Other mistakes models make

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
