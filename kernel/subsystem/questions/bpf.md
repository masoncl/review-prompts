# Questions: BPF Subsystem

- guide: bpf.md
- title: BPF Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/bpf-measurement.md` is the wider
set the readers were measured on and `catalogue/bpf-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## bpf.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## bpf.core-files: Core files

- section: Finding your way
- relevance: 4 - the verifier is no longer one file

A table and nothing else, job to file: the verifier's main pass; its control flow check, state
pruning, precision backtracking, liveness and the rewrites done after verification; the verifier
log; the bpf system call; the helpers; the hash and array maps; the element allocator; BTF;
trampolines; struct_ops; the arena; the x86 and arm64 JITs; libbpf; the selftests and their
verifier test loader. Where a reader is likely to look in a file that no longer holds the code,
say so in the row. Start from `kernel/bpf/`.

# The verifier

## bpf.verifier-phases: Verifier phases

- section: The verifier
- relevance: 4 - a change has to go in the right phase

In what order does the verifier take a program through its phases, from the control flow check to
the rewrites done after verification, and what does this tree call the function for each, where a
reader remembers them as static functions in one file? Which phases run after the main pass, so
that the instructions they produce are never verified? Start from `bpf_check()`.

## bpf.state-pruning: State pruning and precision

- section: The verifier
- relevance: 4 - wrong pruning accepts unsafe programs

What must hold for the verifier to treat a state it reaches as already proven safe, and what do
liveness and precision marks each let that comparison ignore? Where is each mark computed in this
tree, where a reader expects read marks propagated to parent states? Start from
`bpf_is_state_visited()` and `mark_chain_precision()`.

## bpf.state-comparison-fields: New fields and state comparison

- section: The verifier
- relevance: 4 - a field that the comparison skips lets pruning accept an unsafe program

What are the requirements for a patch that adds to or changes what `struct bpf_reg_state` or
`struct bpf_stack_state` holds, in order that `states_equal()` still tells two different states
apart? Start from `regsafe()` and `stacksafe()` in `kernel/bpf/states.c`.

## bpf.limits: Stack, call and tail-call limits

- section: The verifier
- relevance: 3 - numbers people quote from memory

What bounds the stack one frame may use, how deep calls may nest, how many subprograms and
processed instructions a program may have and how many tail calls may chain? Give the constant
and its value in this tree for each, and say which are enforced when the program runs and not
when it is loaded.

## bpf.verifier-change-checklist: Changing the verifier

- section: The verifier
- relevance: 4 - a verifier change touches more than the verifier

What else must a patch update when it changes the text of the verifier log, what the verifier
accepts from an unprivileged loader, or the instructions that the verifier leaves for the JITs?
Name the selftests that check each. Start from `tools/testing/selftests/bpf/`.

# Register state

## bpf.reg-types: Register types and type flags

- section: Register state
- relevance: 4 - every check is phrased in these

What are the requirements for testing a register's type in a verifier check, for its base type and
for a type flag, in order to assure safe usage? What do `MEM_RDONLY` and `MEM_ALLOC` each permit
or forbid? Start from `enum bpf_reg_type`, `enum bpf_type_flag` and `base_type()`.

## bpf.bounds-tracking: Scalar bounds

- section: Register state
- relevance: 4 - most verifier bugs are here

What does this tree call the representation of a scalar register's range, where a reader expects
signed and unsigned minimum and maximum members in `struct bpf_reg_state`, and how must code read
and set the bounds? What are the requirements for code that changes one representation, or that
refines a register at a conditional branch, in order that all representations agree afterwards?
Start from `reg_bounds_sync()`.

## bpf.reference-tracking: Acquired references

- section: Register state
- relevance: 4 - a leak or a double release is a kernel bug

What identifies an acquired reference in a register and in the verifier state in this tree, where
a reader expects a member of the register kept for that, and what does the verifier require of
references before the program exits? How does a helper, and how does a kfunc, declare that it
acquires or releases one? Start from `is_acquire_function()` and `is_kfunc_acquire()`.

## bpf.trusted-pointers: Trusted, RCU and untrusted pointers

- section: Register state
- relevance: 5 - decides what a kfunc may assume about its arguments

When is a pointer to a kernel object trusted, when is it only RCU protected and when untrusted,
and what may a program still do with an untrusted one? What happens to that status when a program
follows a field of the object to another pointer? Start from `PTR_TRUSTED`, `MEM_RCU` and the
`BTF_TYPE_SAFE_RCU()` and `BTF_TYPE_SAFE_TRUSTED()` lists in `kernel/bpf/verifier.c`.

# Programs

## bpf.sleepable: Sleepable programs

- section: Programs
- relevance: 4 - the wrong context crashes

What makes a program sleepable, and where is it decided which program and attach types may be? How
is a helper or a kfunc that may sleep marked? Start from `can_be_sleepable()`.

## bpf.sleepable-object-lifetime: Object lifetime while sleepable

- section: Programs
- relevance: 4 - code that assumes the protection of an ordinary program crashes under a sleepable one

What protects map values and kernel objects while a sleepable program runs, and what are the
requirements for kernel code that a sleepable program can call, in order to assure safe usage?
Start from `__bpf_prog_enter_sleepable()` in `kernel/bpf/trampoline.c`.

## bpf.locks-in-progs: Locks held by a program

- section: Programs
- relevance: 3 - the restrictions differ by lock kind

Which of the locks a BPF program can take is used when, what is a program forbidden to do while
it holds each, and how does the verifier know at a given instruction that a lock is held? Start
from `bpf_spin_lock()`, `bpf_res_spin_lock()` and `process_spin_lock()`.

## bpf.ctx-access: Context access

- section: Programs
- relevance: 3 - each program type supplies its own rules

What does a program type supply so that a load or store through the context pointer is checked
during verification and rewritten afterwards, and what has the verifier already established when
it calls the check? May a program write to its context, and what decides? Start from
`struct bpf_verifier_ops` and `check_ctx_access()`.

## bpf.prog-lifetime: Program lifetime

- section: Programs
- relevance: 4 - use after free if the wait is wrong

What keeps a loaded program alive, what is waited for between the last reference going and its
memory being freed, and how does that differ for a sleepable program? When is the final put
deferred to a workqueue and when is it not? Start from `bpf_prog_put()`.

# Helpers and kfuncs

## bpf.helper-protos: Helper prototypes

- section: Helpers and kfuncs
- relevance: 4 - the prototype is the contract the verifier enforces

What does the verifier enforce from a helper's prototype, and what is the helper left to check
for itself? How is a memory argument tied to its size argument, and what does this tree call the
argument types that do it, where a reader's memory offers older names? Start from
`struct bpf_func_proto` and `check_helper_call()`.

## bpf.kfunc-definition: Defining and registering a kfunc

- section: Helpers and kfuncs
- relevance: 4 - the most common kind of BPF patch outside the core

What must a patch that adds a kfunc do so that the function survives the build, appears in BTF
and is offered to a program type, and what goes wrong if the marker on the definition is left
off? How is a kfunc limited to some programs of a type? Start from `__bpf_kfunc`,
`BTF_KFUNCS_START` and `register_btf_kfunc_id_set()`.

## bpf.kfunc-flags: Kfunc flags

- section: Helpers and kfuncs
- relevance: 5 - each flag changes what the verifier enforces

A table of the kfunc flags this tree defines and what each makes the verifier enforce or allow.
Where a flag a reader is likely to reach for is not defined here, or the documentation and the
header disagree about one, say so. Start from `include/linux/btf.h` and
`Documentation/bpf/kfuncs.rst`.

## bpf.kfunc-arg-annotations: Kfunc argument name suffixes

- section: Helpers and kfuncs
- relevance: 4 - a suffix on a parameter name changes verification

Which suffixes on a kfunc's parameter names does the verifier act on, and what does each make
it check or skip? Which does the documentation describe that the code treats differently? Start
from the annotations section of `Documentation/bpf/kfuncs.rst` and `check_kfunc_args()`.

## bpf.kfunc-trusted-default: Kfunc pointer argument guarantees

- section: Helpers and kfuncs
- relevance: 5 - the default has changed and the old flag may be gone

With no flag and no annotation, what does the verifier guarantee about a pointer to a kernel
object that is passed to a kfunc? How does a kfunc declare that it accepts NULL, or a pointer that
is only RCU protected, and what must its body then do? Start from `check_kfunc_args()`.

## bpf.kfunc-scalar-usage: Kfunc scalar and enum arguments

- section: Helpers and kfuncs
- relevance: 4 - the verifier checks less than people assume, and the index is used in the kernel

What does the verifier guarantee about the value of a scalar or enum argument to a kfunc, and when
is the value guaranteed to be a constant? What are the requirements for a kfunc body that uses
such an argument as an array index, in order to assure safe usage? Name a kfunc that meets them
for an argument of a signed type.

# Maps

## bpf.map-ops: Map operations table

- section: Maps
- relevance: 3 - what a new map type must supply

What must a map type supply in `struct bpf_map_ops` before the system call will create a map of
it? What are the requirements for an operation that a running program can reach, in order to
assure safe usage, and how do they differ from those for an operation reached only from the system
call? Start from `struct bpf_map_ops`.

## bpf.map-memory: Memory for map elements

- section: Maps
- relevance: 4 - programs run where ordinary allocation is not allowed

How are map elements allocated for a preallocated and for a non-preallocated map, and how is the
memory charged? What are the requirements for allocating memory in a path that a BPF program can
reach, in order to assure safe usage? Start from `struct bpf_mem_alloc` and
`kernel/bpf/memalloc.c`.

## bpf.map-lifetime: Map lifetime

- section: Maps
- relevance: 4 - two counts, and freeing is deferred

Which reference counts does a map have and what does each keep alive, and what is waited for
between the last reference going and the map's memory being freed? Start from `bpf_map_put()` and
`bpf_map_put_with_uref()`.

## bpf.percpu-maps: Per-CPU maps

- section: Maps
- relevance: 3 - the syscall and the program see different shapes

How does a program reach its own CPU's value and another CPU's value in a per-CPU map, and how
is the value laid out in a system call lookup or update?

# Stable ABI and conventions

## bpf.uapi-stability: UAPI stability

- section: Stable ABI and conventions
- relevance: 4 - some things can never change and some can

Which parts of BPF are stable user-visible ABI and which are not, among the header, helper
numbers, program, map and attach types, and kfuncs? What rule governs adding to the enums, and
may a new helper still be added? Start from `include/uapi/linux/bpf.h`.

## bpf.comment-style: Comment style

- section: Stable ABI and conventions
- relevance: 2 - a maintainer preference reviewers enforce

Which multi-line comment style do the BPF maintainers ask for in new code, and is it written
down anywhere in the tree?

# Selftests

## bpf.test-loader: Test loader annotations

- section: Selftests
- relevance: 4 - how verifier behaviour is tested now

What decides whether a test that `RUN_TESTS` loads is run privileged, unprivileged or both, and
how are expected log messages matched? What are the requirements for the annotations of a test in
order that the test checks what it was written to check? Start from `RUN_TESTS` and
`tools/testing/selftests/bpf/progs/bpf_misc.h`.

## bpf.verifier-test-files: Verifier test files

- section: Selftests
- relevance: 4 - a test file that nothing runs checks nothing

How is a verifier test written as an annotated BPF program, and what must a patch add so that such
a file is run? Start from `RUN_TESTS` and `tools/testing/selftests/bpf/prog_tests/verifier.c`.

## bpf.assert-macros: Assertion macros

- section: Selftests
- relevance: 3 - new tests must use the current family

Which family of assertion macros do new selftests use and which older one is discouraged, and
what is the practical difference in what each does on failure? Start from
`tools/testing/selftests/bpf/test_progs.h`.

## bpf.skeleton-fd-usage: Skeleton file descriptors after load

- section: Selftests
- relevance: 3 - reviewers ask for checks that cannot fail

After a skeleton's load function has returned success, what does libbpf guarantee about the file
descriptors of the skeleton's programs and maps, and for which programs or maps does it give no
such guarantee? Start from `bpf_object__load_skeleton()` in `tools/lib/bpf/libbpf.c`.

# Model gaps

## bpf.model-gaps: Other mistakes models make

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
