# Questions: BPF (measurement set)

- guide: bpf.md
- title: BPF Subsystem

A wide set of questions about the BPF core, used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 1,214 words. Special fields in map
values and libbpf have their own sets. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## bpf.core-files: Core files

- section: Finding your way
- relevance: 4 - the verifier is no longer one file
- words: 110

Which files hold the verifier and its parts, the bpf system call, the helpers,
the map implementations, BTF, trampolines, struct_ops, the arena, the JITs,
libbpf and the selftests? A table. Start from `kernel/bpf/`.

## bpf.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 100

For each job (load a program, create a map, verify a helper call, verify a
kfunc call, attach through a link, run a program for testing), which function
do you start reading from? A table.

## bpf.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several rules live only there
- words: 60

Which files under `Documentation/bpf/` are the authority on kfuncs, on the
verifier, on the development process and on design decisions?

## bpf.verifier-phases: Verifier phases

- section: The verifier
- relevance: 4 - a change has to go in the right phase
- words: 100

List in order the phases a program goes through in the verifier, from checking
the control flow graph to the rewrites done after verification, and name the
function for each. Start from `bpf_check()`.

## bpf.reg-types: Register types and type flags

- section: The verifier
- relevance: 4 - every check is phrased in these
- words: 100

What are the base register types, and what do the flags that modify a pointer
type mean (maybe null, read only, trusted, RCU protected, untrusted, per-CPU,
allocated object)? Start from `enum bpf_reg_type` and `enum bpf_type_flag`.

## bpf.bounds-tracking: Scalar bounds

- section: The verifier
- relevance: 4 - most verifier bugs are here
- words: 90

What does the verifier track about a scalar register's possible values, how
are those refined at a conditional branch, and which function keeps the
different representations consistent? Start from `struct bpf_reg_state` and
`reg_bounds_sync()`.

## bpf.state-pruning: State pruning and precision

- section: The verifier
- relevance: 4 - wrong pruning accepts unsafe programs
- words: 100

How does the verifier decide that a state it has reached was already proven
safe, what role do liveness and precision marks play, and where does that code
live now? Start from `is_state_visited()` and `mark_chain_precision()`.

## bpf.limits: Hard limits

- section: The verifier
- relevance: 3 - numbers people quote from memory
- words: 60

What are the limits on stack size per frame, on tail calls, on processed
instructions, on subprograms and on call depth, and where is each defined?

## bpf.stack-slots: Stack slots

- section: The verifier
- relevance: 3 - spills and partial writes have their own rules
- words: 70

What kinds of stack slot does the verifier track, what happens when a register
is spilled and filled, and what is required before a stack slot may be read or
passed to a helper? Start from `enum bpf_stack_slot_type`.

## bpf.null-checks: Pointers that may be NULL

- section: The verifier
- relevance: 3 - the oldest rule in the book
- words: 60

How does the verifier represent a pointer that may be NULL, what turns it into
a usable pointer, and which helper and kfunc return kinds produce one?

## bpf.ctx-access: Context access

- section: The verifier
- relevance: 3 - each program type supplies its own rules
- words: 80

How is an access to a program's context checked and then rewritten, which
callbacks does a program type supply for that, and can a program write to its
context? Start from `struct bpf_verifier_ops`.

## bpf.trusted-pointers: Trusted, RCU and untrusted pointers

- section: The verifier
- relevance: 5 - decides what a kfunc may assume about its arguments
- words: 100

When is a pointer to a kernel object trusted, when is it only RCU protected and
when untrusted, and what happens to that status when a program follows a field
of the object to another pointer? Start from `PTR_TRUSTED`, `MEM_RCU` and the
`BTF_TYPE_SAFE_` lists in `kernel/bpf/verifier.c`.

## bpf.reference-tracking: Acquired references

- section: The verifier
- relevance: 4 - a leak or a double release is a kernel bug
- words: 80

How does the verifier track a reference a program has acquired, what must
happen before the program exits, and how do helpers and kfuncs each declare
that they acquire or release one?

## bpf.locks-in-progs: Locks held by a program

- section: The verifier
- relevance: 3 - the restrictions differ by lock kind
- words: 80

Which locks can a BPF program take, what is a program forbidden to do while it
holds each, and how does the verifier track that a lock is held? Start from
`bpf_spin_lock()`, `bpf_res_spin_lock()` and `process_spin_lock()`.

## bpf.sleepable: Sleepable programs

- section: The verifier
- relevance: 4 - the wrong context crashes
- words: 80

What makes a program sleepable, how are helpers and kfuncs that may sleep
marked, what protects map values and objects while a sleepable program runs,
and which attach types allow it?

## bpf.rcu-in-progs: RCU sections inside a program

- section: The verifier
- relevance: 3 - newer and easy to misremember
- words: 70

How does a program open and close an RCU read-side section, what happens to
RCU protected pointers when it ends, and which kfunc flags refer to RCU?

## bpf.helper-protos: Helper prototypes

- section: Helpers and kfuncs
- relevance: 4 - the prototype is the contract the verifier enforces
- words: 100

What does a helper's prototype declare (argument types, return type, flags),
how is a memory argument tied to its size argument, and what does the verifier
check for each? Start from `struct bpf_func_proto` and `check_helper_call()`.

## bpf.helper-availability: Helper availability

- section: Helpers and kfuncs
- relevance: 3 - a helper exposed to the wrong program type is a hole
- words: 70

How does a program type decide which helpers its programs may call, and how do
capabilities change that? Start from `bpf_base_func_proto()`.

## bpf.new-helpers-policy: Adding helpers

- section: Helpers and kfuncs
- relevance: 3 - policy, stated in the documentation
- words: 50

May new helpers still be added, and what does the documentation say to use
instead and why?

## bpf.kfunc-definition: Defining and registering a kfunc

- section: Helpers and kfuncs
- relevance: 4 - the most common kind of BPF patch outside the core
- words: 100

What does defining a kfunc involve: the marker on the function, the id set and
its flags, registering it for a program type, and restricting it with a filter?
Start from `__bpf_kfunc`, `BTF_KFUNCS_START` and
`register_btf_kfunc_id_set()`.

## bpf.kfunc-flags: Kfunc flags

- section: Helpers and kfuncs
- relevance: 5 - each flag changes what the verifier enforces
- words: 140

Give a table of the kfunc flags this tree defines, saying what each makes the
verifier enforce or allow. Start from `include/linux/btf.h` and
`Documentation/bpf/kfuncs.rst`.

## bpf.kfunc-trusted-default: Kfunc pointer argument guarantees

- section: Helpers and kfuncs
- relevance: 5 - the default has changed and the old flag may be gone
- words: 70

By default, what does the verifier guarantee about a pointer to a kernel object
passed to a kfunc: non-NULL, trusted, a particular type? Is a flag needed to get
that, and how does a kfunc accept NULL?

## bpf.kfunc-arg-annotations: Argument name annotations

- section: Helpers and kfuncs
- relevance: 4 - a suffix on a parameter name changes verification
- words: 110

Which suffixes on a kfunc's parameter names does the verifier act on, and what
does each mean? A table. Start from the annotations section of
`Documentation/bpf/kfuncs.rst` and `check_kfunc_args()`.

## bpf.kfunc-scalar-args: Scalar and enum arguments

- section: Helpers and kfuncs
- relevance: 4 - the verifier checks less than people assume
- words: 70

What does the verifier check about a scalar or enum argument to a kfunc, does
it check that an enum value is one of the enumerators, and when is the value
guaranteed to be a constant?

## bpf.kfunc-index-usage: Kfunc arguments as indexes

- section: Helpers and kfuncs
- relevance: 4 - out-of-bounds access in the kernel
- words: 70

What usage of an integer or enum kfunc argument as an array index is unsafe,
and what does a correct check look like for a signed type? Name a kfunc that
does it correctly.

## bpf.kfunc-returns: Kfunc return values

- section: Helpers and kfuncs
- relevance: 3 - the return type decides what the program may do with it
- words: 70

What may a kfunc return, how is a return that may be NULL declared, and what is
required for it to return a pointer to a kernel object that the program may
then dereference?

## bpf.kfunc-stability: Kfunc stability

- section: Helpers and kfuncs
- relevance: 3 - reviewers argue about this
- words: 50

What stability do kfuncs promise to BPF programs, and how is one deprecated?
Start from the lifecycle section of `Documentation/bpf/kfuncs.rst`.

## bpf.iterators: Open-coded iterators

- section: Helpers and kfuncs
- relevance: 3 - the naming is enforced
- words: 70

What must a set of kfuncs look like to form an open-coded iterator: the flags,
the naming, the state structure? Start from `KF_ITER_NEW`.

## bpf.map-ops: Map operations table

- section: Maps
- relevance: 3 - what a new map type must supply
- words: 80

Which callbacks does a map type supply, which are required, and which are
called from a program as opposed to from the system call? Start from
`struct bpf_map_ops`.

## bpf.map-lookup-null: Lookup results

- section: Maps
- relevance: 3 - enforced, but the rule has exceptions
- words: 50

What does a map lookup from a program return when there is no element, does the
verifier force a check, and for which map types can it not fail?

## bpf.map-update-flags: Update flags

- section: Maps
- relevance: 2 - user-visible semantics
- words: 60

What do the update flags mean, which map types reject which flags, and what is
returned when a map is full?

## bpf.percpu-maps: Per-CPU maps

- section: Maps
- relevance: 3 - the syscall and the program see different shapes
- words: 70

How does a program reach its own CPU's value and another CPU's value in a
per-CPU map, and how is the value laid out in a system call lookup or update?

## bpf.map-memory: Memory for map elements

- section: Maps
- relevance: 4 - programs run where ordinary allocation is not allowed
- words: 80

How are map elements allocated for preallocated and non-preallocated maps,
which allocator is safe from any context, and how is the memory charged?
Start from `bpf_mem_alloc` and `kernel/bpf/memalloc.c`.

## bpf.map-lifetime: Map lifetime

- section: Maps
- relevance: 4 - two counts, and freeing is deferred
- words: 80

Which two counts does a map have and what does each keep alive, and what is
waited for between the last reference going and the map's memory being freed?
Start from `bpf_map_put()` and `bpf_map_put_with_uref()`.

## bpf.arena: The arena

- section: Maps
- relevance: 2 - one map type with its own pointer rules
- words: 60

What is the arena map, how do programs and user space address memory in it, and
which kfunc flags and annotations refer to it?

## bpf.prog-lifetime: Program lifetime

- section: Programs
- relevance: 4 - use after free if the wait is wrong
- words: 80

What keeps a loaded program alive, what is waited for before its memory is
freed, and how does that differ for a sleepable program? Start from
`bpf_prog_put()`.

## bpf.tail-calls: Tail calls

- section: Programs
- relevance: 3 - the count and the restrictions
- words: 70

How is the tail call limit enforced, which combinations with subprogram calls,
trampolines or other features are restricted, and what must two programs have
in common for one to tail call the other?

## bpf.subprogs: Static and global functions

- section: Programs
- relevance: 3 - they are verified differently
- words: 80

How does verification of a static function differ from a global one, what may a
global function assume about its arguments, and how are callbacks passed to
helpers verified?

## bpf.struct-ops: struct_ops

- section: Programs
- relevance: 3 - a growing way to extend the kernel
- words: 70

What is a struct_ops map, what does a subsystem supply to support one, and
where does the verifier get the argument types of each member? Start from
`struct bpf_struct_ops`.

## bpf.trampoline: Trampolines

- section: Programs
- relevance: 3 - text patching under the programs
- words: 70

What uses BPF trampolines, how is a trampoline updated when a program is
attached or detached, and what limits apply? Start from
`kernel/bpf/trampoline.c`.

## bpf.jit-requirements: JIT feature gating

- section: Programs
- relevance: 3 - a feature not every JIT has must be gated
- words: 70

How does the core find out whether the JIT for this architecture supports a
feature, and what must a change that adds a new instruction or calling
convention do for JITs that lack it? Start from `bpf_jit_supports_kfunc_call()` and its siblings in
`kernel/bpf/core.c`.

## bpf.privileges: Capabilities and the token

- section: Programs
- relevance: 3 - decides what unprivileged users can reach
- words: 80

Which capabilities gate loading programs and using features, what is a BPF
token, and what extra restrictions apply to a program loaded without privilege?

# Conventions

## bpf.comment-style: Comment style

- section: Coding and process
- relevance: 2 - a maintainer preference reviewers enforce
- words: 50

Which multi-line comment style do the BPF maintainers ask for in new code, and
is it written down anywhere in the tree?

## bpf.patch-process: Trees and patch conventions

- section: Coding and process
- relevance: 3 - patches are bounced for getting these wrong
- words: 80

Which trees do fixes and features go to, how is that shown in the subject line,
what must accompany a feature, and what runs on every submission? Start from
`Documentation/bpf/bpf_devel_QA.rst`.

## bpf.uapi-stability: UAPI stability

- section: Coding and process
- relevance: 4 - some things can never change and some can
- words: 70

Which parts of BPF are stable user-visible ABI (the header, helper numbers,
program and map types, attach types) and which are not, and what rule governs
adding to the enums? Start from `include/uapi/linux/bpf.h`.

## bpf.selftest-layout: Selftest layout

- section: Selftests
- relevance: 3 - where a new test goes
- words: 80

How are the BPF selftests organised: which runner, where the user-space halves
and the BPF halves live, how a test is registered, and what makes a test run
serially?

## bpf.skeleton-api: Skeletons

- section: Selftests
- relevance: 3 - generated code with its own guarantees
- words: 80

What functions does a generated skeleton provide, and after a successful open
and load what is guaranteed about the programs' and maps' file descriptors?

## bpf.skeleton-fd-usage: Checking file descriptors in tests

- section: Selftests
- relevance: 3 - reviewers ask for checks that cannot fail
- words: 60

In a selftest, when is checking a program or map file descriptor redundant and
when is it needed?

## bpf.assert-macros: Assertion macros

- section: Selftests
- relevance: 3 - new tests must use the current family
- words: 70

Which assertion macros should new selftests use, which older ones are
discouraged, and what is the practical difference? Start from
`tools/testing/selftests/bpf/test_progs.h`.

## bpf.test-loader: Annotated verifier tests

- section: Selftests
- relevance: 4 - how verifier behaviour is tested now
- words: 100

How are verifier tests written as annotated BPF programs: what do the
annotations for expected success, failure, messages, return value and
privilege mean, and how is such a file run? Start from `RUN_TESTS` and
`tools/testing/selftests/bpf/progs/bpf_misc.h`.

# Changing the implementation

## bpf.verifier-change-checklist: Changing the verifier

- section: What a change must preserve
- relevance: 4 - a verifier change touches more than the verifier
- words: 90

What must a change to the verifier keep working besides the verifier itself:
privileged and unprivileged behaviour, the log text tests match on, the JITs,
state pruning, the selftests that pin current behaviour?

## bpf.new-map-type: Adding a map type

- section: What a change must preserve
- relevance: 2 - rare
- words: 70

What does adding a map type involve: the type list, the operations table, the
verifier's tables of which helpers work with which map, memory accounting,
documentation and tests? Start from `include/linux/bpf_types.h` and
`check_map_func_compatibility()`.

## bpf.new-prog-type: Adding a program or attach type

- section: What a change must preserve
- relevance: 2 - rare, and discouraged
- words: 60

What does adding a program type or attach type involve, and what do the
maintainers prefer instead?
