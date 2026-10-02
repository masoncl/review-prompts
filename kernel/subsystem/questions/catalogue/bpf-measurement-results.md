# What the bpf measurement found

Two models were asked the questions in `bpf-measurement.md` with no sources, and a checker
that had the sources then corrected each answer against a mainline tree (kernel
7.3.0-rc4). The readers are labelled A (the more current) and B (a few releases
older); which models they were does not matter here. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted at the end.

## What both readers got wrong

- **The verifier is no longer one file.** Both listed `verifier.c` and `log.c`.
  The tree also has `cfg.c`, `states.c`, `backtrack.c`, `liveness.c`,
  `fixups.c`, `diagnostics.c` and more, and the functions that moved gained a
  `bpf_` prefix: `bpf_check_cfg()`, `bpf_is_state_visited()`,
  `bpf_mark_chain_precision()`, `bpf_convert_ctx_accesses()`,
  `bpf_do_misc_fixups()`. Names both used that are gone: check_cfg(),
  resolve_pseudo_ldimm64(), do_misc_fixups(), reg_set_min_max(),
  clean_live_states().
- **Scalar bounds** are not smin_value/umax_value fields any more. They are
  `struct cnum64 r64` and `struct cnum32 r32`, read through `reg_smin()` and
  friends.
- **References**: there is no ref_obj_id. The reference id is the register's
  `id`; acquire is the fixed list in `is_acquire_function()`, only release is
  declared on the argument type.
- **Liveness** is computed statically in `liveness.c`; the read marks both
  remembered are gone.
- **Helper size arguments** are `ARG_MEM_SIZE`/`ARG_MEM_SIZE_OR_ZERO`, not the
  ARG_CONST_SIZE names.
- **Kfunc flags**: KF_TRUSTED_ARGS is not defined; trusted arguments are the
  default. Both left out `KF_IMPLICIT_ARGS`, `KF_SPINLOCK_SAFE` and the arena
  flags. KF_DEPRECATED is described in the documentation and defined nowhere.
- **Kfunc argument suffixes**: both offered __opt and __prog, which do not
  exist, and missed `__const_map`, `__nonown_allowed`, `__iter`, `__arena`.
- **Limits**: call depth is 16, not 8.
- **The comment style rule is written down nowhere in the tree.** One reader
  placed it in the netdev maintainer document, the other in the BPF development
  Q&A; neither mentions comments.

## What reader B got wrong as well

- A kfunc's pointer arguments by default "only need the right BTF type and may
  be NULL or untrusted". The opposite: possibly-NULL and untrusted pointers are
  rejected unless the argument is marked nullable.
- New helpers "can still be added". The header calls the list effectively
  frozen and says to add a kfunc.
- Untrusted pointers cannot be dereferenced. Loads become probe loads; only
  writes and passing to helpers are refused.
- The tail call limit is 32, and the last program put always goes through a
  workqueue. Neither is so.

## What the readers already knew

The entry points for each job, the selftest layout, when a skeleton's file
descriptors need checking (reader A), the register types, the limits apart from
call depth, how to add a map or program type.

## Where the hand-written guide is stale

`bpf.md` says per-CPU maps need bpf_get_cpu_ptr/bpf_put_cpu_ptr, which exist
nowhere in the tree. It names BPF_RET_PTR_TO_MAP_VALUE_OR_NULL; the type is
`RET_PTR_TO_MAP_VALUE_OR_NULL`. It says the context pointer is read-only;
kprobe programs may write theirs. Its long section on scalar and enum kfunc
arguments is correct and is kept as two questions. It was never onboarded to
the drift checker.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 97 corrections, 38% rewritten on average
reader B: 121 corrections, 76% rewritten on average

question                       reader A        reader B
bpf.core-files                  18% ( 5)        33% ( 5)
bpf.entry-points                 0% ( 0)        10% ( 2)
bpf.docs                        26% ( 1)        42% ( 1)
bpf.verifier-phases             35% ( 4)        79% ( 3)
bpf.reg-types                    5% ( 1)        53% ( 2)
bpf.bounds-tracking             42% ( 2)        84% ( 2)
bpf.state-pruning               19% ( 3)        85% ( 4)
bpf.limits                       4% ( 1)        49% ( 3)
bpf.stack-slots                 33% ( 1)        80% ( 2)
bpf.null-checks                 18% ( 1)        90% ( 2)
bpf.ctx-access                  27% ( 3)        85% ( 4)
bpf.trusted-pointers            52% ( 4)        86% ( 5)
bpf.reference-tracking          69% ( 3)        88% ( 3)
bpf.locks-in-progs              82% ( 4)        78% ( 3)
bpf.sleepable                   59% ( 4)        81% ( 4)
bpf.rcu-in-progs                65% ( 2)        93% ( 4)
bpf.helper-protos               40% ( 4)        90% ( 4)
bpf.helper-availability         28% ( 1)        81% ( 2)
bpf.new-helpers-policy          73% ( 1)        89% ( 1)
bpf.kfunc-definition            34% ( 1)        88% ( 2)
bpf.kfunc-flags                 40% ( 1)        62% ( 4)
bpf.kfunc-trusted-default       55% ( 2)        87% ( 3)
bpf.kfunc-arg-annotations       25% ( 6)        68% ( 2)
bpf.kfunc-scalar-args           22% ( 2)        85% ( 1)
bpf.kfunc-index-usage           48% ( 2)        68% ( 1)
bpf.kfunc-returns               40% ( 2)        80% ( 2)
bpf.kfunc-stability             32% ( 1)        82% ( 1)
bpf.iterators                   24% ( 1)        85% ( 1)
bpf.map-ops                     60% ( 1)        95% ( 4)
bpf.map-lookup-null             35% ( 1)        73% ( 1)
bpf.map-update-flags            33% ( 1)        60% ( 2)
bpf.percpu-maps                 36% ( 1)        74% ( 1)
bpf.map-memory                  61% ( 1)        78% ( 2)
bpf.map-lifetime                57% ( 1)        87% ( 2)
bpf.arena                       48% ( 1)        75% ( 1)
bpf.prog-lifetime               60% ( 1)        77% ( 4)
bpf.tail-calls                  83% ( 1)        88% ( 3)
bpf.subprogs                    70% ( 1)        77% ( 2)
bpf.struct-ops                  42% ( 1)        83% ( 1)
bpf.trampoline                  52% ( 1)        81% ( 3)
bpf.jit-requirements            60% ( 1)        74% ( 1)
bpf.privileges                  62% ( 1)        87% ( 3)
bpf.comment-style               46% ( 1)        92% ( 1)
bpf.patch-process               34% ( 3)        78% ( 3)
bpf.uapi-stability              52% ( 4)        91% ( 3)
bpf.selftest-layout              0% ( 0)        70% ( 1)
bpf.skeleton-api                19% ( 1)        65% ( 1)
bpf.skeleton-fd-usage            0% ( 0)        84% ( 1)
bpf.assert-macros               27% ( 3)        84% ( 1)
bpf.test-loader                 38% ( 3)        87% ( 1)
bpf.verifier-change-checklist   10% ( 4)        66% ( 4)
bpf.new-map-type                 5% ( 1)        51% ( 1)
bpf.new-prog-type               13% ( 0)        71% ( 1)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `bpf.map-ops`, `bpf.map-memory`, `bpf.map-lifetime`, `bpf.percpu-maps`, `bpf.state-pruning`, `bpf.helper-protos`, `bpf.kfunc-definition`, `bpf.prog-lifetime`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `bpf.reg-types`.

## Questions reorganised

The build set is organised by subject, each question's section named after its part: the verifier
(phases, pruning, limits, what a change must keep working), register state (type flags, scalar
bounds, references, trusted pointers), programs, helpers and kfuncs, maps, stable ABI and
conventions, selftests. 31 questions became 30: `bpf.kfunc-scalar-args` and `bpf.kfunc-index-usage`
are now `bpf.kfunc-scalar-usage`, the unsafe index following from what the verifier does not check.
Nothing was dropped. `bpf.reg-types`, `bpf.map-ops`, `bpf.limits` and `bpf.verifier-phases` asked
for inventories and now ask for a contract or a hazard. The pointer is_state_visited() became
`bpf_is_state_visited()`, and the BTF_TYPE_SAFE_ prefix the two macros the tree defines.
