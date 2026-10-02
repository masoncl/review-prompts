# What the netlink measurement found

Three models were asked the 47 questions in `netlink-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.12 to 6.19), reader A a little behind it (6.10 to
6.15), and reader B older and much weaker: nearly every answer of its was
mostly rewritten. The hand-written guide was never checked against current
sources, so differences between it and the built guide are expected and are
noted near the end.

Readers A and C know the protocol, the attribute helpers and the published
design rules well. What they get wrong is how the Generic Netlink core treats
a command that has no policy or sets classic flags, the fine print of dumps
and extended ACKs, and almost everything about the YAML specs and the code
generated from them. Reader B is also wrong about the basics.

## What all three readers got wrong

- **Request-type flags are rejected, not ignored.** All three said the Generic
  Netlink core neither interprets nor rejects `NLM_F_REPLACE`, `NLM_F_EXCL`,
  `NLM_F_CREATE` and the rest. For a command at or above the family's
  `resv_start_op`, `genl_header_check()` returns `-EINVAL` for any flag other
  than `NLM_F_REQUEST`, `NLM_F_ACK`, `NLM_F_ECHO` and a full `NLM_F_DUMP`, and
  for a non-zero `genlmsghdr.reserved`. All three also added "use attributes
  instead", which no document says.
- **Where a command's policy comes from.** The family policy is inherited only
  by `struct genl_ops` (field by field) and `struct genl_small_ops`. A
  `struct genl_split_ops` entry never inherits it: with no policy of its own it
  gets a reject-all policy whatever `resv_start_op` says. Parsing is skipped
  only when the policy pointer is NULL, which can now only happen for an old
  command below `resv_start_op`; a policy with `maxattr` 0 still validates.
  Each reader had a different part of this wrong.
- **The first attribute and command value.** All three called the zero value
  reserved. `Documentation/core-api/netlink.rst` says new families should not
  define `unspec` entries at all and should just start at 1, and `specs.rst`
  lets a spec set `value: 0` explicitly. The `directional` message ID model is
  accepted by the `netlink-raw` schema as well as `genetlink-legacy`;
  `genetlink` and `genetlink-c` accept only `unified`.
- **Reasons behind the attribute design rules.** Each reader supplied reasons
  of its own. The documents say: `multi-attr` because it needs no extra nest
  (and `indexed-array` is limited to 64kB); no C structures because of
  validation and extensibility; `uint` and `sint` "in most cases" with no
  reason given; nothing under 32 bits because alignment eats the saving.
- **Growing a dump buffer.** None knew that a dumpit callback may raise
  `cb->min_dump_alloc` itself and return a positive value with an empty buffer
  to be called again with a larger one, as `net/wireless/nl80211.c` does.
  `NLMSG_GOODSIZE` is a page capped at 8 KiB, but `min_dump_alloc` can be far
  larger.
- **What an extended ACK carries.** The cookie is sent on success and on
  failure; the offset, policy and missing-attribute fields only on failure.
  In `NLMSG_DONE` the attributes are added only if the buffer has room, and
  only what the last dumpit round set is reported.
- **Multicast bind callbacks.** `bind` and `unbind` in `struct genl_family` run
  for every socket that joins or leaves, not for the first and the last, and
  `genl_bind()` throws away what `bind` returns.
- **Spec checks.** `flags-mask` becomes `NLA_POLICY_MASK()`; on a binary
  attribute `min-len` and `max-len` become `NLA_POLICY_MIN_LEN()` and
  `NLA_POLICY_MAX_LEN()`; `unterminated-ok` is not in the `genetlink` schema;
  "full-range" and "sparse" are decided by the generator and are not
  properties. The `CONST - 1` form for a string length is documented and
  allowed by the schema, no spec in the tree uses it, and `get_limit_str()`
  does not emit it correctly.
- **Spec hygiene.** All three made `doc` optional; every schema requires it
  at the top level and on each operation. The name pattern is in three of the
  four schemas, not in `genetlink-c`. Two readers called the licence a
  convention: `tools/net/ynl/pyynl/lib/nlspec.py` refuses a spec without the
  SPDX line and `ynl_gen_c.py` exits unless it is exactly the dual licence.
- **Schema levels and generated code.** The `Makefile` targets are
  `schema_check` and `lint`. `struct genl_family` is generated only for the
  `genetlink` level, never with `resv_start_op`, a policy or `maxattr`; at the
  other levels the operation table is exported and the family is written by
  hand. Generated files are found by their `YNL-GEN` marker, not by name.
- **Fractional sets.** `specs.rst` says they can only be used in nests, yet
  `Documentation/netlink/specs/ovpn.yaml` uses them as the `attribute-set` of
  operations. A subset may override any property, even the type; only `value`
  always comes from the main set.
- **Tools.** There is no tools/net/ynl/samples directory; the C and shell
  tests are in `tools/net/ynl/tests`, where `ethtool.py` also lives. Run them
  with `make -C tools/net/ynl run_tests`.

## What readers A and B got wrong as well

- A family may mix `ops`, `small_ops` and `split_ops`; only a duplicate
  command is refused. Both said the forms cannot be combined.
- The unsafe getter. Both offered `nla_get_u64()` on a 4-byte attribute as
  reading past the payload. It goes through `nla_memcpy()`, which is bounded
  and zero-fills. The dangerous one is `nla_get_u32()`, a plain load, on an
  attribute whose policy says `NLA_U8` or `NLA_U16`.
- The `kernel-policy` property is accepted only by the `genetlink-legacy` and
  `netlink-raw` schemas, and the generator and schemas default to `split`
  while `Documentation/core-api/netlink.rst` says `per-op`.
- On a dump entry the spec's `pre` and `post` become `start` and `done`, and
  only a split table carries them.
- The generator is `tools/net/ynl/pyynl/ynl_gen_c.py`; both gave another name.
- The per-socket dump lock is `nl_cb_mutex`. It is held for `start`, every
  dumpit round and `done`, except the `done` run from `netlink_release()`.

## What only reader B got wrong

Almost everything else, of which the parts that would change a review:
it doubted `genl_header_check()` exists; put `rcu_read_lock()` in the receive
path and left out `cb_lock`; said operations must be sorted for a binary
search; called `args` the current place for dump state and `ctx` unknown;
listed exact-length and minimum-length as attribute types; gave
`NLA_POLICY_MASK()` to bitfields; said liberal parsing checks only minimum
lengths; said 64-bit padding is emitted on every architecture; recommended an
indexed nest for arrays and events over notifications; left `split` out of the
`kernel-policy` values; placed the documentation under a directory that does
not exist; and named limits and helpers that are nowhere in the tree.

## What only reader C got wrong

- A per-socket dump mutex that an rtnetlink flag lets a dump skip. This tree
  has only `nl_cb_mutex`, held whatever the flags; `RTNL_FLAG_DUMP_UNLOCKED`
  decides only whether `rtnl_lock()` is taken.
- `genl_info_init_ntf()` followed by `genl_notify()`. The init zeroes the
  network namespace and `genl_notify()` dereferences it, so
  `genl_info_net_set()` has to come between, as in `net/psp/psp_nl.c`.
- `GENL_DONT_VALIDATE_DUMP` removes the dump policy only for `genl_ops` and
  `genl_small_ops`; a split dump entry keeps its policy.
- A signed 64-bit put helper that does not exist; the helper is
  `nla_put_s64()`, which takes the pad attribute.

## What the readers already knew

Readers A and C: where the documentation is, the permission flags, the order
of the hooks around a request, that a repeated attribute leaves only its last
instance in the table and how to walk them all, the variable-width integers
and their helpers, the reply-rather-than-ACK rule and why, the rule against
multipart replies to a do, string policy types, the `ctx` area for dump state,
the dump consistency helper and the zero it must avoid (reader C), the extended
ACK macros (reader C), the policy macros (reader C), sub-messages and struct
packing in specs. Reader B knew the outline of the protocol and little more.

## Where the hand-written guide is stale

`netlink.md` is a fair summary of the documents it cites and has no map of the
code at all. Against this tree:

- It calls `per-op` the default `kernel-policy`. The generator and both
  schemas that have the property default to `split`; only
  `Documentation/core-api/netlink.rst` says `per-op`. A spec at the `genetlink`
  level, the only one a new family may use, cannot set the property.
- It says specs commonly write `max-len: CONST - 1`. None does, and the
  generator would not emit it correctly.
- It gives dashes in names, a `doc` on each property and the unified message
  ID model as things to check. The schemas enforce all three (the name pattern
  everywhere but `genetlink-c`, `doc` at the top level and on operations).
- It treats the request-type flags purely as a convention. For new commands
  the core rejects them.
- It asks for extended ACK information on success as well. Only the message
  and the cookie are delivered on success.
- It ties the `pad` attribute to 64-bit integers "in legacy fixed structs".
  The pad attribute aligns fixed-width 64-bit attributes; structs are padded
  with explicit members.
- It says a fractional set never defines `value`, which is right, and nothing
  about where such a set may be used, where the document and the tree differ.

## Left out of the build set

The hand-written guide is 781 words and no answer in a built guide is budgeted
under 40 words, so the build set holds 13 of the 47 questions with 665 words
of budget between them, chosen by importance to someone reviewing a change to
a family or its spec and by what every reader got wrong. A first build held 19
at 25 to 35 words each, and its answers were fragments that meant little
without the question beside them. Six of the 19 were taken out to give the
others room:

- the reply-rather-than-ACK rule and dump consistency, which readers A and C
  already had right; the frozen-properties answer still says that reply or ACK
  only is fixed by the first release;
- sending notifications, where readers A and C were close and what reader C
  got wrong about `genl_info_init_ntf()` never fitted in the short answer;
- the schema levels, where those two readers missed little more than the
  `Makefile` targets;
- the `kernel-policy` property, although readers A and B had it wrong and the
  hand-written guide is stale about it: a spec at the `genetlink` level, the
  only one a new family may use, cannot set it;
- spec hygiene, although all three had it wrong: what they missed is that the
  schemas and the generator already enforce the licence, the names and `doc`,
  so the tools catch it before a reviewer has to.

Left out from the start although a reader got them wrong: the operation table
forms, registration, the locks in the core, the hooks around a request and the
entry-point table (a change to the core needs the source); the policy type and
macro tables, nested and repeated attributes, 64-bit padding and strings
(`include/net/netlink.h` documents them well and readers A and C were close);
building a reply, multicast group access, the dump buffer size and dump state;
the extended ACK macro list; and from the specs the operation properties,
definitions, fractional sets, structs and sub-messages, which matter to the
few who edit legacy and raw specs. The rule against multipart replies to a do
and the variable-width integers are left out because every reader but B had
them right.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A:  87 corrections, 28% rewritten on average
reader B: 121 corrections, 72% rewritten on average
reader C:  74 corrections, 18% rewritten on average

question                           reader A      reader B      reader C
netlink.core-files                  3% ( 1)      16% ( 7)       1% ( 2)
netlink.docs                        0% ( 0)      43% ( 3)       0% ( 0)
netlink.entry-points                9% ( 1)      32% ( 5)      11% ( 1)
netlink.family-registration        35% ( 2)      71% ( 6)      12% ( 3)
netlink.ops-forms                  43% ( 3)      60% ( 3)       0% ( 0)
netlink.policy-source              50% ( 3)      75% ( 2)      12% ( 3)
netlink.header-checks               6% ( 1)      82% ( 1)       0% ( 0)
netlink.op-permissions              0% ( 0)      53% ( 2)       0% ( 0)
netlink.core-locking               32% ( 4)      92% ( 3)      11% ( 3)
netlink.do-hooks                   17% ( 1)      56% ( 1)      12% ( 0)
netlink.validation-levels          21% ( 3)      73% ( 5)      14% ( 2)
netlink.unknown-attributes         28% ( 1)      54% ( 2)      13% ( 2)
netlink.policy-types               15% ( 4)      51% ( 6)      11% ( 4)
netlink.policy-macros              23% ( 4)      74% ( 4)       1% ( 1)
netlink.nested-attributes          32% ( 2)      75% ( 2)      23% ( 1)
netlink.repeated-attributes         0% ( 0)      50% ( 1)       2% ( 1)
netlink.variable-width-integers     5% ( 1)      79% ( 1)       5% ( 1)
netlink.wide-integer-padding       22% ( 1)      65% ( 1)      24% ( 1)
netlink.string-attributes          27% ( 1)      74% ( 1)      14% ( 1)
netlink.type-agreement             36% ( 3)      65% ( 2)      21% ( 1)
netlink.reply-construction         16% ( 1)      89% ( 2)      14% ( 1)
netlink.reply-or-ack                0% ( 0)      80% ( 1)       0% ( 0)
netlink.notifications               6% ( 1)      77% ( 1)       9% ( 1)
netlink.mcast-group-access         43% ( 2)      81% ( 1)      19% ( 1)
netlink.multi-message-do           20% ( 1)      80% ( 1)      30% ( 1)
netlink.dump-lifecycle             34% ( 2)      81% ( 6)      42% ( 2)
netlink.dump-state                 25% ( 1)      86% ( 2)       0% ( 0)
netlink.dump-consistency           35% ( 1)      76% ( 2)       0% ( 0)
netlink.dump-buffer-size           43% ( 1)      74% ( 1)      77% ( 2)
netlink.frozen-uapi                35% ( 1)      81% ( 1)      39% ( 1)
netlink.id-numbering               64% ( 3)      87% ( 1)      37% ( 2)
netlink.request-flags              54% ( 2)      87% ( 2)      38% ( 1)
netlink.attribute-design           69% ( 1)      89% ( 1)      38% ( 1)
netlink.extack-helpers             32% ( 3)      68% ( 4)       0% ( 0)
netlink.extack-delivery            32% ( 2)      85% ( 2)      18% ( 1)
netlink.extack-usage               37% ( 3)      72% ( 2)      17% ( 2)
netlink.spec-levels                41% ( 4)      86% ( 4)      34% ( 4)
netlink.generated-code             62% ( 2)      75% ( 2)      17% ( 3)
netlink.kernel-policy-property     38% ( 3)      91% ( 2)      20% ( 1)
netlink.spec-checks                53% ( 3)      89% ( 2)      31% ( 5)
netlink.spec-operations            40% ( 2)      84% ( 2)      19% ( 2)
netlink.spec-definitions           16% ( 1)      86% ( 5)       9% ( 1)
netlink.spec-fractional-sets       18% ( 1)      62% ( 2)      36% ( 3)
netlink.spec-structs               12% ( 1)      82% ( 2)      13% ( 1)
netlink.spec-sub-messages          23% ( 1)      83% ( 2)      15% ( 1)
netlink.spec-hygiene               47% ( 4)      85% ( 4)      48% ( 3)
netlink.testing-tools              40% ( 4)      70% ( 6)      47% ( 7)
```

## Questions put back

A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `netlink.family-registration`, `netlink.ops-forms`, `netlink.header-checks`, `netlink.op-permissions`, `netlink.core-locking`, `netlink.unknown-attributes`, `netlink.policy-types`, `netlink.policy-macros`, `netlink.nested-attributes`, `netlink.repeated-attributes`, `netlink.variable-width-integers`, `netlink.string-attributes`, `netlink.reply-or-ack`, `netlink.notifications`, `netlink.dump-state`, `netlink.dump-consistency`, `netlink.extack-helpers`, `netlink.spec-levels`, `netlink.kernel-policy-property`.

## Questions reorganised

By subject now, 33 questions from 34, each a hazard, a contract or orientation. Subjects: families
and operations; policies and parsing; dumps; extended ACK; uAPI design rules; specs and generated
code. Merged: `netlink.header-checks` and `netlink.request-flags`, which both asked what the core
does with `nlmsg_flags`, into `netlink.header-flag-checks`. Nothing dropped whole.
`netlink.family-registration` lost its list of what a family fills in and gained the multicast bind
callbacks; `netlink.dump-lifecycle` now asks how a callback gets a larger buffer;
`netlink.spec-levels` asks what the schemas and tools already refuse; the macro and helper
inventories in `netlink.policy-macros` and `netlink.variable-width-integers` went.
