# Questions: Netlink and Generic Netlink (measurement set)

- guide: netlink.md
- title: Netlink / Generic Netlink uAPI Details

A wide set of questions about Netlink as kernel code sees it: the Generic
Netlink core, attribute policies and validation, requests, dumps and
notifications, extended ACKs, and the YAML protocol specs with the code
generated from them. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written
guide it will replace is 781 words and is almost entirely uAPI design rules.
rtnetlink message handlers and the socket layer are left to the networking
guides. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## netlink.core-files: Core files

- section: Finding your way
- relevance: 4 - the code, the specs and the generator live in four trees
- words: 110

Which files hold the AF_NETLINK socket layer, the Generic Netlink core, the
policy dump, attribute parsing and validation, the kernel-internal headers for
messages, attributes and Generic Netlink, the uAPI headers, the YAML specs,
their schemas, the code generator, the user-space library and the tests? A
table. Start from `net/netlink/`.

## netlink.docs: Authoritative documentation

- section: Finding your way
- relevance: 4 - the design rules live only there
- words: 80

Which files under `Documentation/` are the authority on Netlink design rules
for kernel developers, on the protocol as user space sees it, on the spec
schema, on the legacy and raw schema levels, and on how C names are generated
from a spec?

## netlink.entry-points: Entry points

- section: Finding your way
- relevance: 3 - turns a search into a lookup
- words: 100

For each job, which function do you start reading from: dispatching a received
Generic Netlink message, parsing the attributes of a do request, starting a
dump, running one round of a dump and ending it, building the ACK with its
extended ACK attributes, validating one attribute against a policy, dumping a
policy to user space, sending a multicast notification? A table.

# Generic Netlink families

## netlink.family-registration: Family registration

- section: Families and operations
- relevance: 4 - registration is where a malformed family is caught
- words: 90

What does a Generic Netlink family fill in before it registers, what does
registration check and refuse, and how are the family ID and the multicast
group IDs assigned? Start from `struct genl_family`, `genl_register_family()`
and `genl_validate_ops()`.

## netlink.ops-forms: Operation table forms

- section: Families and operations
- relevance: 4 - three structs describe the same thing and new code uses one
- words: 90

In how many forms can a family describe its operations, what does each form
carry that the others do not, can one family mix them, and what ordering and
flag requirements does the do/dump split form have? Start from
`struct genl_split_ops`.

## netlink.policy-source: Policy for a command

- section: Families and operations
- relevance: 5 - decides whether the handler sees validated attributes at all
- words: 80

Where does the core take the attribute policy and the maximum attribute
number for a command from when both the family and the operation can supply
them, and what does the core do with the attributes of a command that has no
policy? Start from `genl_family_rcv_msg_attrs_parse()` and the comment on
`struct genl_family`.

## netlink.header-checks: Header and flag checks

- section: Families and operations
- relevance: 4 - new families get checks old ones do not
- words: 70

What does the Generic Netlink core check in the message headers and in
`nlmsg_flags` before it looks up a command, for which commands does it make
those checks, and which flags does it let through? Start from
`genl_header_check()`.

## netlink.op-permissions: Permission flags

- section: Families and operations
- relevance: 4 - the two flags check different capabilities
- words: 60

Which flags on an operation make the core check a capability before calling
the handler, what exactly does each check, and what does a family have to set
to be reachable from a network namespace other than the initial one? Start
from `genl_family_rcv_msg()`.

## netlink.core-locking: Locks in the core

- section: Families and operations
- relevance: 4 - handlers rely on serialisation that parallel families do not get
- words: 90

Which locks does the Generic Netlink core itself take, and which of them are
held while a doit, a dump start, a dumpit round and a dump done callback run,
for a family that sets `parallel_ops` and for one that does not? Start from
`genl_rcv()` and `genl_family_rcv_msg_dumpit()`.

## netlink.do-hooks: Hooks around a request

- section: Families and operations
- relevance: 3 - the unwind assumption is easy to get wrong
- words: 60

In what order does the core run attribute parsing, the pre-doit hook, the
doit handler and the post-doit hook, and is the post-doit hook called when the
pre-doit hook or the handler fails? Start from `genl_family_rcv_msg_doit()`.

# Attributes and validation

## netlink.validation-levels: Validation strictness

- section: Policies and parsing
- relevance: 5 - which checks a handler may assume were done
- words: 100

What are the separate checks that make up strict validation, which parse
entry points apply all of them and which apply none, which per-operation
flags turn strictness off for a Generic Netlink command, and how does a policy
make only its newer attributes strict? Give the flag names in full. Start from
`enum netlink_validation`.

## netlink.unknown-attributes: Unknown attributes

- section: Policies and parsing
- relevance: 4 - ignored versus rejected changes what user space may send
- words: 70

What does attribute parsing do with an attribute whose type is zero, above
the maximum the caller passed, or present in the policy array with no type
given, and how does that depend on the validation flags? Start from
`__nla_validate_parse()` and `validate_nla()`.

## netlink.policy-types: Policy attribute types

- section: Policies and parsing
- relevance: 4 - each type implies a different length check
- words: 120

List the attribute types a policy entry can name and, for each, what is
checked about the payload length under liberal and under strict validation and
what the `len` field means. A table. Start from the comment on
`struct nla_policy` and the length tables at the top of `lib/nlattr.c`.

## netlink.policy-macros: Policy initialiser macros

- section: Policies and parsing
- relevance: 4 - a declared constraint replaces open-coded checks
- words: 100

Which macros initialise a policy entry with a value range, a minimum, a
maximum, a bit mask, an exact or bounded length, a nested policy or a
validation function, which attribute types does each accept, and what limits
the values the plain range macros can express? Start from
`include/net/netlink.h`.

## netlink.nested-attributes: Nested attributes

- section: Policies and parsing
- relevance: 4 - validated is not the same as parsed
- words: 90

When a policy entry points at a nested policy, what has been done to the
contents of the nest by the time the handler runs and what must the handler
still do itself, what role does the nested flag bit in the attribute type
play on input and on output, and how deep may nests go? Start from
`nla_parse_nested()` and `nla_nest_start()`.

## netlink.repeated-attributes: Repeated attributes

- section: Policies and parsing
- relevance: 4 - the parsed table hides all but one instance
- words: 60

When the same attribute type appears more than once at one level of a
message, what does the parsed attribute table hold for it, and how does a
handler read every instance? Name in-tree code that does.

## netlink.variable-width-integers: Variable-width integers

- section: Policies and parsing
- relevance: 4 - newer than most readers' picture of the attribute types
- words: 80

Does this tree have integer attribute types whose size on the wire depends on
the value, and if so what are the policy types, the put and get helpers, the
sizes that validation accepts and the alignment a reader may assume? If not,
say so and stop.

## netlink.wide-integer-padding: Padding for 64-bit values

- section: Policies and parsing
- relevance: 3 - the pad attribute exists for one reason
- words: 70

How does the kernel get the payload of a fixed 64-bit attribute aligned to 8
bytes in a message whose attributes are aligned to 4, which helpers do it, on
which architectures is anything emitted, and what does a family have to
reserve in its attribute set for this?

## netlink.string-attributes: String attributes

- section: Policies and parsing
- relevance: 4 - the terminator is counted in one place and not in another
- words: 80

What are the two string policy types, what does each require of the payload,
does the length limit in the policy count the terminating NUL, and which
helpers copy a string attribute out safely? Start from `validate_nla()` and
`nla_strscpy()`.

## netlink.type-agreement: Type agreement

- section: Policies and parsing
- relevance: 5 - nothing checks it at build time
- words: 80

In how many places is the type of one attribute written down, which of them
does the compiler or the core check against each other, and what usage of the
get and put helpers is unsafe when they disagree while code that looks similar
is correct? Name an example of each.

# Requests, replies and dumps

## netlink.reply-construction: Building a reply

- section: Replies and notifications
- relevance: 3 - the helper sequence and its unwind
- words: 90

What is the sequence of helper calls that allocates a Generic Netlink reply,
writes its headers from the request, adds attributes, finishes it and sends
it back, what does each step return on failure, and what must be undone when
an attribute does not fit? Start from `genlmsg_iput()` and `genlmsg_reply()`.

## netlink.reply-or-ack: Reply versus ACK

- section: Replies and notifications
- relevance: 5 - fixed for ever by the first release
- words: 70

What do the kernel's own Netlink guidelines say a command that creates or
changes an object should send back to the requester, why can that choice not
be revisited later, and what do they say about relying on the echo flag for
it? Start from `Documentation/core-api/netlink.rst`.

## netlink.notifications: Sending notifications

- section: Replies and notifications
- relevance: 4 - the helpers differ in who receives the message
- words: 100

Which helpers send a Generic Netlink notification to a multicast group, how
is the group argument numbered, which of them also delivers to the requester
that set the echo flag and what must the caller pass for that to work, which
reach other network namespaces, and how does a caller avoid building a message
nobody listens for? Start from `genl_notify()`.

## netlink.mcast-group-access: Multicast group access

- section: Replies and notifications
- relevance: 2 - only matters when a group carries privileged data
- words: 50

How does a family restrict which sockets may join one of its multicast
groups, and what callbacks does it get when the first listener joins or the
last leaves? Start from `struct genl_multicast_group` and `genl_bind()`.

## netlink.multi-message-do: Multi-message replies to do

- section: Replies and notifications
- relevance: 3 - a design rule the code does not enforce
- words: 50

What do the guidelines say about answering a single non-dump request with
several messages marked as multipart, what is offered instead, and does the
core prevent it? Start from
`Documentation/userspace-api/netlink/genetlink-legacy.rst`.

## netlink.dump-lifecycle: Dump lifecycle

- section: Dumps
- relevance: 5 - the return value protocol is unwritten and has changed
- words: 120

How does a dump run from the request to the final message: when are the
start, dumpit and done callbacks called and in whose context, how does the
core read each possible return value of dumpit, when is the terminating
message written and can it share a buffer with the last objects? Start from
`netlink_dump()` and `__netlink_dump_start()`.

## netlink.dump-state: Dump state between rounds

- section: Dumps
- relevance: 4 - the old way is still in the struct
- words: 80

Where does a dumpit callback keep its position between rounds, which member of
`struct netlink_callback` is the current way and which is deprecated, how is
the size checked, and how does a Generic Netlink dumpit reach the parsed
request attributes, the family and the extended ACK? Start from
`genl_dumpit_info()`.

## netlink.dump-consistency: Dump consistency

- section: Dumps
- relevance: 4 - a dump that silently skips objects is a bug user space cannot see
- words: 80

How does a dump tell user space that the set of objects changed while it was
being dumped, what does the dumper have to maintain and where does it record
it, which helper sets the flag, and which value may the counter never take?
Start from `nl_dump_check_consistent()`.

## netlink.dump-buffer-size: Dump buffer size

- section: Dumps
- relevance: 3 - one object larger than the buffer stalls the dump
- words: 70

How large is the buffer a dumpit callback is given, what makes it larger, and
what happens when a single object does not fit in an empty buffer? Start from
`netlink_dump()` and `min_dump_alloc`.

# Design rules for the uAPI

## netlink.frozen-uapi: Frozen properties

- section: uAPI design
- relevance: 5 - the reason every other rule here exists
- words: 80

Which properties of a Netlink family are fixed once a kernel carrying it has
been released, which kinds of change remain possible afterwards, and how does
user space find out what a running kernel supports? Start from
`Documentation/userspace-api/netlink/intro.rst`.

## netlink.id-numbering: Command and attribute numbering

- section: uAPI design
- relevance: 4 - reviewers ask for this on every new family
- words: 80

What do the guidelines say about the first value of an attribute or command
enum, about the zero value, about the IDs of a request and its reply, and
about the IDs of notifications, and which message ID model must a new family
use? Do the rules apply to extending an existing family that already breaks
them?

## netlink.request-flags: Request-type flags

- section: uAPI design
- relevance: 3 - classic Netlink habits that new families must not copy
- words: 70

Which `nlmsg_flags` bits are specific to GET, NEW and DEL requests in classic
Netlink, what is their standing for new Generic Netlink families, and does
the core accept or reject them? Start from the request flags section of
`Documentation/userspace-api/netlink/intro.rst`.

## netlink.attribute-design: Attribute design preferences

- section: uAPI design
- relevance: 4 - the choices reviewers push back on
- words: 100

What do the guidelines prefer for carrying an array, for carrying a C
structure, for the width of an integer, and for integers narrower than 32
bits, and what reason, if any, do they give for each? Start from
`Documentation/userspace-api/netlink/specs.rst` and
`Documentation/userspace-api/netlink/genetlink-legacy.rst`.

# Extended ACK

## netlink.extack-helpers: Extended ACK helpers

- section: Extended ACK
- relevance: 4 - several macros, each with a catch
- words: 110

Which macros set a message, a formatted message, a bad attribute, a bad
attribute with its policy, and a missing attribute in a
`struct netlink_ext_ack`, which Generic Netlink wrappers exist, what limits a
formatted message, and what must be true of a string passed to the plain
message macro? Start from `include/linux/netlink.h`.

## netlink.extack-delivery: Delivery to user space

- section: Extended ACK
- relevance: 4 - some fields are dropped on success
- words: 80

Which fields of the extended ACK are sent to user space when the operation
failed and which when it succeeded, what does the socket have to have enabled,
and in which messages of a dump can they appear? Start from
`netlink_ack_tlv_len()`.

## netlink.extack-usage: Reporting errors well

- section: Extended ACK
- relevance: 4 - the difference between a usable error and EINVAL
- words: 90

What usage of the extended ACK is incorrect or discouraged (what a bad
attribute pointer may point at, when a text message is redundant, overwriting
a message a callee already set) and what that looks similar is correct? Start
from `netlink_ack_tlv_fill()` and the extended ACK part of
`Documentation/userspace-api/netlink/intro.rst`.

# YAML specs and generated code

## netlink.spec-levels: Schema levels

- section: Specs
- relevance: 4 - what a spec may contain depends on its level
- words: 80

What are the schema levels a spec can declare, which may a new family use,
where are the schemas, and how is a spec checked against its schema and
linted? Start from `Documentation/netlink/` and `tools/net/ynl/Makefile`.

## netlink.generated-code: Generated kernel code

- section: Specs
- relevance: 5 - hand edits to generated files are lost
- words: 110

Which kernel files are generated from a spec, how is a generated file
recognised, how is it regenerated, what does the generated source contain
(policies, operation table, family struct) and for which schema level is each
part emitted, and what is left for the family to write by hand? Start from
`tools/net/ynl/ynl-regen.sh` and `net/core/netdev-genl-gen.c`.

## netlink.kernel-policy-property: The kernel-policy property

- section: Specs
- relevance: 4 - the documentation and the generator may not agree
- words: 80

What values can the `kernel-policy` property of a spec take, what does each
make the generator emit, what is the default according to the documentation
and according to the generator and the schema, and which schema levels accept
the property at all? Start from `tools/net/ynl/pyynl/ynl_gen_c.py`.

## netlink.spec-checks: Attribute checks in a spec

- section: Specs
- relevance: 4 - this is how a spec declares validation
- words: 100

Which properties can appear under `checks` for an attribute, and what policy
initialiser does each turn into? Give the macro names in full. The
documentation describes a way to write a string limit from a C constant that
includes the terminator: does any spec in the tree use it, and does the C
generator handle it? Start from `Documentation/core-api/netlink.rst`,
`Documentation/netlink/genetlink.yaml` and `get_limit_str()` in
`tools/net/ynl/pyynl/ynl_gen_c.py`.

## netlink.spec-operations: Operation properties

- section: Specs
- relevance: 3 - each maps onto a field of the ops table
- words: 90

What do the `flags`, `dont-validate`, `config-cond`, `pre` and `post`
properties of an operation generate, where do `request` and `reply` attribute
lists matter to the kernel, and what is the difference between a `notify` and
an `event` entry and which is preferred?

## netlink.spec-definitions: Definitions in a spec

- section: Specs
- relevance: 3 - enums and constants have their own rules
- words: 80

What kinds of definition can a spec hold, how are enum and flags values
assigned and can they be sparse, how does an attribute refer to one, and how
does a spec use a constant that already lives in a C header without defining
it again? Start from the definitions section of
`Documentation/userspace-api/netlink/specs.rst`.

## netlink.spec-fractional-sets: Fractional attribute sets

- section: Specs
- relevance: 2 - one rule, easy to break when copying a set
- words: 50

What is an attribute set that declares `subset-of`, where may it be used,
what may it redefine and what may it not, and is it rendered into the uAPI
header?

## netlink.spec-structs: Structures in specs

- section: Specs
- relevance: 3 - the packing rule is not what C programmers assume
- words: 70

At which schema levels can a spec define a C structure, where can it be used,
and how does the layout of a struct defined in YAML differ from what a C
compiler would produce for the same members?

## netlink.spec-sub-messages: Sub-messages

- section: Specs
- relevance: 2 - raw families only
- words: 70

What is a sub-message in a raw Netlink spec, how is its format selected, what
ordering does that require inside the message, and what happens when the
selector attribute exists at more than one nesting level or is absent?

## netlink.spec-hygiene: Spec hygiene

- section: Specs
- relevance: 3 - the mechanical review points
- words: 90

What must a spec file have for its licence, its names (which characters, and
how they become C identifiers), its documentation strings, and its
independence from other specs and C headers? Which of these does the schema
enforce and which are convention? Start from
`Documentation/userspace-api/netlink/c-code-gen.rst`.

# Changing and testing

## netlink.testing-tools: Exercising a family

- section: Tools and tests
- relevance: 3 - how a reviewer can try a new command
- words: 80

Which in-tree tools send requests to a family from its spec, which directories
hold tests for the generator and the user library and which selftests cover
the Netlink core and dumps, and how are they run? Start from
`tools/net/ynl/pyynl/cli.py` and `tools/net/ynl/tests`.
