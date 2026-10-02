# Questions: Scope-Based Cleanup and Guards

- guide: cleanup.md
- title: Scope-Based Cleanup and Guards

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/cleanup-measurement.md` is the
wider set the readers were measured on and `catalogue/cleanup-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## cleanup.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## cleanup.core-files: Core files

- section: Finding your way
- relevance: 4 - the wrappers and guard classes are spread over many headers

A table and nothing else, job to file: the scope-based cleanup helpers and their documentation;
the compiler attribute they rest on; the wrappers for the slab allocators; the guard classes for
mutexes, for spinlocks and read-write locks, for read-write semaphores, for RCU, for preemption
and migration, and for interrupts; the script that checks a declaration. Where a reader is likely
to look in a header that does not hold the guard, say so in the row. Start from
`include/linux/cleanup.h`.

## cleanup.macro-families: Macro families

- section: Finding your way
- relevance: 4 - the families look alike and are used differently

A table of the families of macros that `include/linux/cleanup.h` defines: in a phrase what each
family is for, which macro defines a member and which uses one.

# Freeing a variable

## cleanup.free-expansion: Generated cleanup function

- section: Freeing a variable
- relevance: 4 - what `_T` is, and who tests it, decides what a wrapper body may do

What argument does the compiler pass to the function that `DEFINE_FREE()` generates, what is `_T`
in the wrapper's expression, and does the generated function test anything before it evaluates
that expression?

## cleanup.free-type: Types other than pointers

- section: Freeing a variable
- relevance: 4 - decides whether a wrapper for a structure held by value is correct

What are the requirements for the type given to `DEFINE_FREE()`: may it be something other than a
pointer, and what is `_T` then? Name in-tree code that shows it.

## cleanup.when-cleanup-runs: Scope exits

- section: Freeing a variable
- relevance: 4 - every other rule rests on when the function runs

On which ways of leaving a scope does the compiler run the cleanup function of a variable declared
with `__cleanup()`, and on which does it not? Is the cleanup function called when the variable
holds NULL, and what decides whether anything is released then?

## cleanup.slab-wrappers: Slab wrappers

- section: Freeing a variable
- relevance: 5 - the wrappers differ and the difference crashes

A table of the `DEFINE_FREE()` wrappers `include/linux/slab.h` defines: for each, which values may
the variable hold at scope exit without the release function being called on them? Quote each
test.

## cleanup.common-wrappers: Common wrappers elsewhere

- section: Freeing a variable
- relevance: 4 - each wrapper has to be looked up, and this says how and what to expect

Outside `include/linux/slab.h`, which tests do `DEFINE_FREE()` wrappers make before they call the
release function, and what does the choice of test mean for a variable that holds NULL or an error
pointer at scope exit? How is a wrapper's definition found from the name given to `__free()`?

## cleanup.errptr-usage: Error pointers under a cleanup attribute

- section: Freeing a variable
- relevance: 5 - a wrapper that only tests for NULL releases an error pointer

What are the requirements for a `__free()` variable that is initialised from a function that can
return an error pointer in order to assure safe usage? What does the cleanup function do with the
variable on an early return taken when `IS_ERR()` is true? Name in-tree code that shows it.

## cleanup.uninitialised-usage: Declarations without an initialiser

- section: Freeing a variable
- relevance: 4 - the cleanup runs on whatever the stack held

What happens when a `__free()` variable is declared without an initialiser and the function
returns before it is assigned? Does `scripts/checkpatch.pl` flag the declaration, and under what
message type? Does either compiler the kernel supports catch it? Start from
`scripts/checkpatch.pl`.

# Cleanup order and guard scope

## cleanup.guard-scope: Guard lifetime

- section: Cleanup order and guard scope
- relevance: 4 - the lock follows the braces, not the function

How long does a lock taken with `guard()` stay held when the guard is declared at function level
and when it is declared inside the body of an `if` or a loop, and how long with `scoped_guard()`?
What are the requirements for code that reads or writes the protected data in order to assure safe
usage?

## cleanup.scoped-guard-loop: Control flow inside a scoped guard

- section: Cleanup order and guard scope
- relevance: 4 - the macro is a loop, so loop keywords bind to it

What kind of statement does `scoped_guard()` expand to, and what do `break` and `continue` do
inside its body? What are the requirements for a `scoped_guard()` body inside an enclosing loop,
in order to assure safe usage? Start from `__scoped_guard()`.

## cleanup.declare-at-init: Declaring at the point of initialisation

- section: Cleanup order and guard scope
- relevance: 5 - the header's main recommendation, and it overrides coding style

What does the documentation in `include/linux/cleanup.h` say about where a `__free()` variable is
declared relative to where it is initialised, and what reason does it give? What does it say about
grouping such declarations at the top of a function?

## cleanup.lock-resource-order: Guard and resource declaration order

- section: Cleanup order and guard scope
- relevance: 5 - the release runs with or without the lock depending on a line's position

What are the requirements for the declaration order of a lock guard and a `__free()` variable in
one function, in order to assure safe usage, when the release function needs the lock held and
when it must run after the lock is dropped? Name in-tree code that shows each.

## cleanup.widened-critical-section: Converting lock calls to guards

- section: Cleanup order and guard scope
- relevance: 4 - a conversion moves code under the lock without touching it

When explicit lock and unlock calls are replaced with `guard()`, which code that used to run after
the unlock now runs with the lock held? What are the requirements for such a conversion in order
to assure safe usage, and which form keeps the old hold time?

# Ownership transfer

## cleanup.no-free-ptr: no_free_ptr and return_ptr

- section: Ownership transfer
- relevance: 4 - the success path of every constructor uses it

What does `no_free_ptr()` do to the variable and what does it evaluate to, and what happens when
its value is ignored? Which of it and `return_ptr()` is used when? Start from
`__get_and_null()`.

## cleanup.retain-and-null: Disarming with retain_and_null_ptr

- section: Ownership transfer
- relevance: 4 - newer than the other two and easy to confuse with them

What is `retain_and_null_ptr()` for, and how does it differ from `no_free_ptr()`? What are the
requirements for a call to `retain_and_null_ptr()` in order to assure safe usage, according to the
comment above it? If this tree does not have it, say so.

## cleanup.transfer-usage: Transfer to another owner

- section: Ownership transfer
- relevance: 5 - double free or leak, and neither shows in the diff

What are the requirements for handing the pointer in a `__free()` variable to another owner, in
order to assure safe usage, and what are they when `no_free_ptr()` is evaluated in the argument
list of a function that can fail? Name in-tree code that shows it.

# Guard classes

## cleanup.guard-definers: Guard definition macros

- section: Guard classes
- relevance: 4 - picking the wrong definer changes what `_T` is

Which of `DEFINE_GUARD()`, `DEFINE_LOCK_GUARD_1()` and `DEFINE_LOCK_GUARD_0()` is used when? What
is `_T` in the lock and unlock expressions of each, and where does each keep state beyond the lock
pointer?

## cleanup.class-expansion: Class macros and generated names

- section: Guard classes
- relevance: 4 - the generated names are what error messages and tags show

What names do `DEFINE_CLASS()` and `CLASS()` generate (the type, the constructor, the destructor),
so that an error message or a tag can be traced to the definition? Which of `EXTEND_CLASS()`,
`CLASS_INIT()` and `scoped_class()` is used when? If this tree lacks any of them, say so.

## cleanup.init-guards: Initialisation guards

- section: Guard classes
- relevance: 3 - looks like a lock being taken and is not

Does this tree define guard classes whose name ends in `_init`, for a mutex or a spinlock for
example? If so, what does `guard()` on one of them do, is any lock held afterwards, and what are
they for? Start from `include/linux/mutex.h` and `Documentation/dev-tools/context-analysis.rst`.

## cleanup.header-change-checklist: Dependents of the header

- section: Guard classes
- relevance: 3 - classes, helpers and tools outside the header lean on its internals

What outside `include/linux/cleanup.h` depends on the names that the header generates, such as
those of `__is_cond_ptr()` and `__guard_ptr()`, so that a change to the header has to keep it in
step? What does a guard for a new lock type have to declare so that context analysis accepts it?

# Conditional guards

## cleanup.cond-guard-names: Conditional guard names

- section: Conditional guards
- relevance: 4 - the suffixes are a convention, not a rule

A table of the suffixes that conditional guard classes carry in this tree: which kind of lock
function each calls and what value marks a failure. For the `mutex`, `rwsem_read`, `rwsem_write`,
`spinlock` and `device` classes, which of those suffixes has no class defined?

## cleanup.cond-guard-definition: Conditional guard definition

- section: Conditional guards
- relevance: 4 - how failure is stored decides what every user must test

How is a conditional guard class made from its base class: what decides whether the lock was
taken, what value does the class instance hold after a failure, and how does the destructor know
not to unlock? Start from `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`.

## cleanup.cond-with-guard: Conditional class under a plain guard

- section: Conditional guards
- relevance: 5 - the code after it runs whether or not the lock was taken

What happens when `guard()` is used with a conditional class, such as a trylock or interruptible
form, and the lock is not acquired? Is there a build-time or run-time check, and what does the
header say about it?

## cleanup.cond-with-scoped-guard: Conditional class under a scoped guard

- section: Conditional guards
- relevance: 5 - a body that is silently skipped looks like success

What does `scoped_guard()` do with a conditional class when the lock is not acquired, and what are
the requirements for the code that follows the `scoped_guard()` statement in order to assure safe
usage? How does `scoped_cond_guard()` differ?

## cleanup.acquire: Named conditional acquisition

- section: Conditional guards
- relevance: 4 - the newest of the forms, and the one that returns an error code

What are the requirements for code that takes a lock with `ACQUIRE()` in order to assure safe
usage, and how does that differ from `scoped_cond_guard()` on the same class? What does
`ACQUIRE_ERR()` return on success and on each kind of failure? If this tree has no `ACQUIRE()`,
say so.

# Goto and policy

## cleanup.goto-documentation: Documented position on goto

- section: Goto and policy
- relevance: 4 - reviewers quote it, and the tree does not uniformly follow it

What does the header's documentation say about using `goto` and the cleanup helpers in the same
function, and what reason does it give? Does in-tree code follow it everywhere?

## cleanup.subsystem-policy: Subsystem policy

- section: Goto and policy
- relevance: 3 - the same patch is welcome in one tree and refused in another

Does any subsystem's documentation restrict or discourage the cleanup helpers? Say which
document, and what it says about `guard()`, `scoped_guard()`, `__free()` and declaring variables
in the middle of a function.

## cleanup.goto-usage: Goto and cleanup in one function

- section: Goto and policy
- relevance: 5 - one jump runs a cleanup on a variable that was never initialised

What are the requirements for a function that has both `goto` labels and `__free()` or `guard()`
declarations in order to assure safe usage? How does each compiler the kernel supports treat a
`goto` that jumps forward over such a declaration to a label inside its scope? Name in-tree code
that shows it.

# Model gaps

## cleanup.model-gaps: Other mistakes models make

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
