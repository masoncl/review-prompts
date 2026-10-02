# Questions: Scope-Based Cleanup and Guards (measurement set)

- guide: cleanup.md
- title: Scope-Based Cleanup and Guards

A wide set of questions about the scope-based cleanup helpers, used to measure
what a model already knows before deciding what the built guide should spend
its words on. The hand-written guide it will replace is 934 words and covers
five things: whether a `DEFINE_FREE()` wrapper tolerates every value its
variable can hold, the order in which cleanups run, how long a guard holds its
lock, handing a pointer to another owner, and mixing `goto` with the helpers.
It is loaded when a diff uses `__free()`, `guard()`, `scoped_guard()`,
`DEFINE_FREE()`, `DEFINE_GUARD()`, `no_free_ptr()` or `return_ptr()`. The
questions here also cover the class and guard machinery, conditional guards
and what a change to the header must preserve. Format:
`../../../docs/subsystem-questions.md`.

# The helpers

## cleanup.core-files: Core files

- section: Finding your way
- relevance: 4 - the wrappers and guard classes are spread over many headers
- words: 80

Which files define the scope-based cleanup helpers, the compiler attribute
they rest on, the wrappers for the slab allocators, and the guard classes for
mutexes, spinlocks, read-write semaphores, RCU, preemption and interrupts? A
table. Start from `include/linux/cleanup.h`.

## cleanup.docs: Documentation and tooling

- section: Finding your way
- relevance: 3 - the rules live in a header comment, not in an rst file
- words: 60

Where is the documentation for the cleanup helpers kept, how does it reach the
rendered documentation under `Documentation/`, and which other documents or
scripts in the tree set rules about using the helpers? Start from
`Documentation/core-api/cleanup.rst`.

## cleanup.macro-families: Macro families

- section: Finding your way
- relevance: 4 - the families look alike and are used differently
- words: 100

List the families of macros the cleanup header provides (freeing a variable,
classes with a constructor and destructor, lock guards, conditional lock
guards, scoped forms) and say in a phrase what each family is for, which macro
defines a member and which uses one. A table.

## cleanup.free-expansion: Generated cleanup function

- section: Freeing variables
- relevance: 4 - what `_T` is decides what a wrapper body may do
- words: 70

What do `DEFINE_FREE()` and `__free()` expand to: what is the generated
function called, what argument does the compiler pass it, and how does the
body get at `_T`? Can the type given to `DEFINE_FREE()` be something other than
a pointer, and does in-tree code do that?

## cleanup.free-without-define: Cleanup names without a wrapper

- section: Freeing variables
- relevance: 2 - rare, but a reader who has not seen it takes it for a bug
- words: 50

Is `DEFINE_FREE()` the only way to make a name usable with `__free()`? If
in-tree code does it another way, name an example and say what a user of that
name must be careful about. Start from `include/linux/path.h`.

## cleanup.null-test-reason: Reason for the NULL test

- section: Freeing variables
- relevance: 3 - explains why a redundant-looking test is asked for in review
- words: 60

The header's example wrapper tests the pointer before calling a release
function. What reason does the header give for the test, and what is lost if a
wrapper leaves it out? Start from the comment above `DEFINE_FREE()`.

## cleanup.when-cleanup-runs: Scope exits

- section: Freeing variables
- relevance: 4 - every other rule rests on when the function runs
- words: 70

On which ways of leaving a scope does the compiler run a variable's cleanup
function (return, break, continue, goto out of the scope, falling off the
end), and on which does it not? Is the cleanup function called when the
variable holds NULL, and what decides whether anything is released then?

# Wrappers and the values they tolerate

## cleanup.slab-wrappers: Slab wrappers

- section: Wrapper definitions
- relevance: 5 - the wrappers differ and the difference crashes
- words: 80

Which `DEFINE_FREE()` wrappers does `include/linux/slab.h` define, and for
each, which values may the variable hold at scope exit without the release
function being called on them: NULL, an error pointer, both? Quote each test.
A table.

## cleanup.common-wrappers: Common wrappers elsewhere

- section: Wrapper definitions
- relevance: 4 - each wrapper has to be looked up, and this says where
- words: 120

For the `DEFINE_FREE()` wrappers most used outside the slab header (device
tree and firmware node references, struct device, struct file, file names,
credentials, firmware images, pages, per-CPU memory, bitmaps, cpumasks, PCI
devices, network devices, modules), give the name, the header, and whether the
wrapper tests for NULL, for an error pointer as well, or for nothing. A table.

## cleanup.errptr-usage: Error pointers under a cleanup attribute

- section: Wrapper definitions
- relevance: 5 - a wrapper that only tests for NULL releases an error pointer
- words: 80

When the function that initialises a `__free()` variable can return an error
pointer, what usage is unsafe, and what that looks similar is correct? Say how
to tell from the wrapper's definition, what an early return on `IS_ERR()` does
with the variable, and name in-tree code that shows a correct form.

## cleanup.uninitialised-usage: Declarations without an initialiser

- section: Wrapper definitions
- relevance: 4 - the cleanup runs on whatever the stack held
- words: 60

What happens when a `__free()` variable is declared without an initialiser and
the function returns before it is assigned? Which script in the tree flags the
declaration and under what name, and does either compiler catch it? Start from
`scripts/checkpatch.pl`.

## cleanup.reassignment-usage: Assigning over a held value

- section: Wrapper definitions
- relevance: 3 - the attribute acts at scope exit only
- words: 60

What happens to the old value when a `__free()` variable that already holds a
resource is assigned a new one, for example in a loop or on a retry? What
usage is unsafe, and what that looks similar is correct?

# Order and scope

## cleanup.unwind-order: Unwind order

- section: Order of cleanup
- relevance: 5 - the order is fixed by the declarations, not by the code
- words: 50

In what order do the cleanup functions of several variables in one scope run,
and how do nested scopes fit into that order? What does the header's
documentation quote as the authority?

## cleanup.return-expression-order: Return value and cleanup

- section: Order of cleanup
- relevance: 5 - decides whether returning a field under a guard is safe
- words: 60

In a function that returns a value, is the return expression evaluated before
or after the cleanup functions of the variables going out of scope run? What
does that mean for returning a field of a locked object under a guard, and for
returning the pointer a `__free()` variable holds?

## cleanup.declare-at-init: Declaring at the point of initialisation

- section: Order of cleanup
- relevance: 5 - the header's main recommendation, and it overrides coding style
- words: 80

What does the header's documentation recommend about where a `__free()`
variable is declared relative to where it is initialised, and about grouping
declarations at the top of a function? What goes wrong with the pattern it
warns about, and what that looks similar is harmless?

## cleanup.lock-resource-order: Locks and the resources they protect

- section: Order of cleanup
- relevance: 5 - the release runs with or without the lock depending on a line's position
- words: 80

When a function uses both a lock guard and a `__free()` variable whose release
function needs that lock held, what declaration order is unsafe, and what is
correct? What about a resource whose release must happen after the lock is
dropped, because it sleeps or takes the same lock? Name in-tree code for each.

## cleanup.guard-scope: Guard lifetime

- section: Scope of a guard
- relevance: 4 - the lock follows the braces, not the function
- words: 70

How long does a lock taken with `guard()` stay held when the guard is declared
at function level, inside the body of an `if` or a loop, and with
`scoped_guard()`? What usage of the protected data is unsafe, and what that
looks similar is correct?

## cleanup.widened-critical-section: Hold time after conversion

- section: Scope of a guard
- relevance: 4 - a conversion moves code under the lock without touching it
- words: 70

When explicit lock and unlock calls are replaced with `guard()`, which code
that used to run after the unlock now runs with the lock held? What
conversions are unsafe (consider sleeping calls, calls that take the same
lock, copies to user space), and what form keeps the old hold time?

## cleanup.scoped-guard-loop: Control flow inside a scoped guard

- section: Scope of a guard
- relevance: 4 - the macro is a loop, so loop keywords bind to it
- words: 70

How is `scoped_guard()` built, and what do `break`, `continue`, `return` and
`goto` do inside its body? What usage inside an enclosing loop is unsafe, and
what that looks similar is correct? Start from `__scoped_guard()`.

## cleanup.case-label-usage: Declarations under a case label

- section: Scope of a guard
- relevance: 3 - the compilers disagree, so it passes one build and fails another
- words: 50

What happens when `guard()` or a `__free()` declaration is placed directly
under a `case` label of a `switch` without braces, with each compiler the
kernel supports? What form is correct?

# Ownership transfer

## cleanup.no-free-ptr: Inhibiting the cleanup

- section: Transfer primitives
- relevance: 4 - the success path of every constructor uses it
- words: 60

What does `no_free_ptr()` do to the variable and what does it evaluate to? How
is ignoring its value made to warn, and which helper does it share with the
other transfer macros? Start from `__get_and_null()`.

## cleanup.return-usage: Returning a held pointer

- section: Transfer primitives
- relevance: 5 - a plain return hands the caller freed memory
- words: 60

A function holds a pointer in a `__free()` variable and wants to return it to
its caller on success. What way of returning it is unsafe, and what is
correct? What does `return_ptr()` expand to?

## cleanup.retain-and-null: Pointer consumed by a callee

- section: Transfer primitives
- relevance: 4 - newer than the other two and easy to confuse with them
- words: 70

What is `retain_and_null_ptr()` for, how does it differ from `no_free_ptr()`,
and what does the comment above it say about when it may be used? What usage is
unsafe, and what that looks similar is correct? If this tree does not have it,
say so.

## cleanup.transfer-usage: Transfer to another owner

- section: Transfer primitives
- relevance: 5 - double free or leak, and neither shows in the diff
- words: 80

When a `__free()` pointer is handed to another owner (put on a list, stored in
a longer-lived structure, passed to a function that keeps it), what usage leads
to a double free or a leak, and what is correct? Cover a callee that can fail
after `no_free_ptr()` was evaluated in its argument list. Name in-tree code.

## cleanup.non-pointer-transfer: Transfer of a non-pointer

- section: Transfer primitives
- relevance: 3 - file descriptors use the same machinery with a different null value
- words: 70

How is ownership taken away from a class instance that is not a pointer, such
as a file descriptor number? Which macro does it, what value does it leave
behind, and which destructor test makes that value harmless? Start from
`include/linux/file.h`.

# Classes and guards

## cleanup.class-expansion: Class machinery

- section: Classes
- relevance: 4 - the generated names are what error messages and tags show
- words: 90

What do `DEFINE_CLASS()` and `CLASS()` generate: the type names, the
constructor and the destructor? What do `EXTEND_CLASS()`, `CLASS_INIT()` and
`scoped_class()` add? If this tree lacks any of them, say so.

## cleanup.guard-definers: Guard definition macros

- section: Classes
- relevance: 4 - picking the wrong definer changes what `_T` is
- words: 90

What is the difference between `DEFINE_GUARD()`, `DEFINE_LOCK_GUARD_1()` and
`DEFINE_LOCK_GUARD_0()`: what type is the class instance in each, what is `_T`
in the lock and unlock expressions, where is extra state such as saved
interrupt flags kept, and which is used for a lock with no object such as RCU
or preemption?

## cleanup.guard-names: Guard class names

- section: Classes
- relevance: 4 - a wrong class name does not compile, a wrong variant deadlocks
- words: 120

Give the guard class names this tree defines for mutexes, spinlocks and raw
spinlocks in their plain, bh, irq and irqsave forms, read-write locks,
read-write semaphores, RCU, SRCU, preemption, migration, interrupts, local
locks and the device lock, with the header for each. A table.

## cleanup.init-guards: Initialisation guards

- section: Classes
- relevance: 3 - looks like a lock being taken and is not
- words: 50

Does this tree define guard classes whose name ends in `_init`, for a mutex or
a spinlock for example? If so, what does `guard()` on one of them do, is any
lock held afterwards, and what are they for? Start from
`include/linux/mutex.h` and `Documentation/dev-tools/context-analysis.rst`.

## cleanup.null-lock-argument: NULL lock argument

- section: Classes
- relevance: 3 - some callers pass an optional lock
- words: 60

What happens when a NULL pointer is passed as the lock to `guard()` or
`scoped_guard()`: is it rejected at build time, does the constructor lock it,
and does the destructor unlock it? Does the answer differ between
`DEFINE_GUARD()` and `DEFINE_LOCK_GUARD_1()` classes and their conditional
forms?

## cleanup.context-analysis-hooks: Lock context analysis

- section: Classes
- relevance: 3 - a new guard needs more than one line now
- words: 80

How do the guard classes cooperate with the compiler's lock context analysis:
what are `__no_context_analysis`, `DECLARE_LOCK_GUARD_1_ATTRS()` and
`WITH_LOCK_GUARD_1_ATTRS()` for, and what must someone adding a guard for a
new lock type write besides the `DEFINE_LOCK_GUARD_1()` line? If this tree has
none of this, say so.

# Conditional guards

## cleanup.cond-guard-definition: Conditional guard definition

- section: Conditional locks
- relevance: 4 - how failure is stored decides what every user must test
- words: 90

How are conditional guard classes defined: what arguments do
`DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()` take, what decides
whether the lock was taken, how is failure recorded in the class instance, and
how does the destructor know not to unlock?

## cleanup.cond-guard-names: Conditional guard names

- section: Conditional locks
- relevance: 4 - the suffixes are a convention, not a rule
- words: 70

Which conditional guard classes does this tree define for mutexes, read-write
semaphores, spinlocks and the device lock, and what does each suffix mean? A
table.

## cleanup.cond-with-guard: Conditional class under a plain guard

- section: Conditional locks
- relevance: 5 - the code after it runs whether or not the lock was taken
- words: 60

What happens when `guard()` is used with a conditional class, such as a
trylock or interruptible form, and the lock is not acquired? Is there a
build-time or run-time check, and what does the header say about it?

## cleanup.cond-with-scoped-guard: Conditional class under a scoped guard

- section: Conditional locks
- relevance: 5 - a body that is silently skipped looks like success
- words: 70

What does `scoped_guard()` do with a conditional class when the lock is not
acquired? What usage is unsafe, and what that looks similar is correct? How
does `scoped_cond_guard()` differ, and what does it do when given an
unconditional class?

## cleanup.acquire: Named conditional acquisition

- section: Conditional locks
- relevance: 4 - the newest of the forms, and the one that returns an error code
- words: 80

What do `ACQUIRE()` and `ACQUIRE_ERR()` expand to, what argument does
`ACQUIRE_ERR()` take, and what value does it give on success, when a trylock
form fails, and when an interruptible or killable form fails? What usage is
unsafe? If this tree has no `ACQUIRE()`, say so.

# Goto

## cleanup.goto-documentation: Documented position on goto

- section: Mixing with goto
- relevance: 4 - reviewers quote it, and the tree does not uniformly follow it
- words: 50

What does the header's documentation say about using `goto` and the cleanup
helpers in the same function, and what reason does it give? Does in-tree code
follow it everywhere?

## cleanup.goto-usage: Goto and cleanup in one function

- section: Mixing with goto
- relevance: 5 - one jump runs a cleanup on a variable that was never initialised
- words: 90

In a function that has both `goto` labels and `__free()` or `guard()`
declarations, what usage is unsafe, and what that looks similar is correct?
Cover a forward jump over a declaration to a label inside its scope, a jump
out of the scope, and a label placed before the declaration. How does each
compiler the kernel supports treat the first case? Name in-tree code.

## cleanup.mixed-unwind-usage: Partial conversions

- section: Mixing with goto
- relevance: 4 - the same resource ends up released twice or not at all
- words: 60

When a function converted to `__free()` keeps an error label that also
releases the same resource by hand, what goes wrong? For a partly converted
function, what has to be checked for each resource on each exit path?

# Conventions and changes

## cleanup.scoped-iterators: Scoped iterators

- section: Conventions
- relevance: 3 - the commonest use of the attribute in drivers
- words: 70

How are the scoped iterator macros, such as the ones for device tree child
nodes, built on `__free()`? What happens to the reference on `break` and
`return` inside the loop, what use of the node after leaving the loop is
unsafe, and how does code keep the node? Start from
`for_each_child_of_node_scoped()`.

## cleanup.subsystem-policy: Subsystem policy

- section: Conventions
- relevance: 3 - the same patch is welcome in one tree and refused in another
- words: 50

Does any subsystem's documentation restrict or discourage the cleanup helpers?
Say which document, and what it says about `guard()`, `scoped_guard()`,
`__free()` and declaring variables in the middle of a function.

## cleanup.conversion-checklist: Converting a function

- section: What a change must preserve
- relevance: 4 - most patches that touch these helpers are conversions
- words: 80

What must a patch that converts a function from goto-based unwinding to the
cleanup helpers preserve? List what to compare between the old and the new
function: release order, which releases run under which lock, hold times,
ownership on the success path, the value returned.

## cleanup.header-change-checklist: Changing the header

- section: What a change must preserve
- relevance: 3 - the header is included almost everywhere
- words: 80

What must a change to `include/linux/cleanup.h` keep working: both compilers,
the sparse annotations, the context analysis attributes, unique variable and
label names, the documentation rendered from the header, the patterns in
`scripts/tags.sh`, and classes outside the header that define their own
conditional flag? Are there copies of the header under `tools/`?
