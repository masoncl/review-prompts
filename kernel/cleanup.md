# cleanup and guard API details

**When to check**: mandatory when cleanup.h helpers (__free, guard, DEFINE_FREE, DEFINE_GUARD) are used

**Common location**: Functions using __free, guard(), DEFINE_FREE, DEFINE_GUARD, no_free_ptr, return_ptr

**Mandatory cleanup function compatibility validation:**
- step 1: For EVERY __free() variable, identify the cleanup function
  - Place each cleanup function in TodoWrite
  - Output: variable name, cleanup function and what it can safely handle (NULL, ERR_PTR, valid pointer, or combinations)
  - Output: Early return paths where cleanup will trigger
- step 2: For EVERY __free() variable, identify the allocator function
  - Place each allocator function in TodoWrite
  - Output variable name, allocator function and what it can return (NULL, ERR_PTR, valid pointer, or combinations)
- step 3: Verify cleanup function can handle ALL possible values the variable might hold:
  - If allocator returns ERR_PTR, cleanup function MUST handle ERR_PTR safely
  - If allocator returns NULL, cleanup function MUST handle NULL safely
  - Common issue: kfree() only handles NULL/ZERO_SIZE_PTR, NOT ERR_PTR
  - Common issue: devlink_free() only handles valid pointers, NOT NULL or ERR_PTR
- step 4: Check all early return paths:
  - Output: early return path location
  - On IS_ERR() check returning early, does variable hold ERR_PTR?
  - On NULL check returning early, does variable hold NULL?
  - Will cleanup function handle the value correctly?
- step 5: Look for mitigation patterns:
  - Setting variable to NULL before early return
  - Using no_free_ptr() before early return
  - Having cleanup function check IS_ERR() or similar

**Recommended definition-initialization pattern:**
- step 1: identify all __free() variables in function
  - Add function list to TodoWrite
  - Output: function list
- step 2: check if variables defined with "= NULL" at top, then assigned later
  - This pattern is ALLOWED but DISCOURAGED per include/linux/cleanup.h:
    "the recommendation is to always define and assign variables in one
    statement and not group variable definitions at the top of the
    function when __free() is used"
  - Risk: makes LIFO ordering mistakes more likely
  - Recommendation: define and initialize in single statement when practical
- step 3: if split definition-initialization is used, verify LIFO ordering is correct:
  - Variables requiring locks must be defined AFTER guard() for that lock
  - From include/linux/cleanup.h DOC comment explaining LIFO bug pattern
  - Cleanup runs in reverse definition order (LIFO)
  - If lock guard defined before resource, lock releases before resource cleanup
- step 4: Flag as potential issue if:
  - Variables defined at top with "= NULL" AND
  - Depend on locks/resources defined later in the function
  - Only report if LIFO ordering is provably wrong, not just "risky"

**Mandatory goto mixing validation:**
- step 1: scan entire function for goto statements
- step 2: scan entire function for __free() or guard() usage
- step 3: if BOTH found in same function, flag as violation
- step 4: from include/linux/cleanup.h DOC comment:
  "the expectation is that usage of 'goto' and cleanup helpers is never
  mixed in the same function. I.e. for a given routine, convert all
  resources that need a 'goto' cleanup to scope-based cleanup, or
  convert none of them."
  - Either convert ALL resources to cleanup helpers
  - Or convert NONE of them
  - No partial conversions allowed

**Mandatory LIFO ordering validation:**
- step 1: list all __free() and guard() variables in order of definition
- step 2: identify dependencies between resources
  - Locks must be acquired BEFORE resources they protect
  - Resources that reference other resources must be defined AFTER
- step 3: verify cleanup order (reverse of definition order) is safe
  - Last defined = first cleaned up
  - First defined = last cleaned up
  - From include/linux/cleanup.h: "When multiple variables in the same
    scope have cleanup attributes, at exit from the scope their
    associated cleanup functions are run in reverse order of definition
    (last defined, first cleanup)."
- step 4: common patterns requiring specific order:
  - guard(mutex)(&lock) MUST come before struct obj *p __free(remove_free)
  - if remove_free() requires the lock to be held
- step 5: verify interdependent resources using DOC example from include/linux/cleanup.h

**Mandatory guard() scope validation:**
- step 1: identify all guard() invocations
  - Add every guard() invocation to TodoWrite
  - Output: guard location and line
- step 2: determine the scope where guard() is called:
  - Function scope: lock held until function returns
  - Block scope: lock held only until closing brace
  - For-loop scope: lock held only for loop body
  - Output: function scope determined
- step 3: verify scope matches intended lock lifetime
- step 4: check for block scoping issues:
  - guard(lock)(foo) in if-statement only holds lock in that if-block
  - NOT for the rest of the function
  - From include/linux/cleanup.h: "The lifetime of the lock obtained by
    the guard() helper follows the scope of automatic variable declaration."
- step 5: verify understanding of automatic variable scope from include/linux/cleanup.h DOC

**Mandatory ownership transfer validation:**
- step 1: identify all __free() variables
  - Add every __free() variable to TodoWRite
  - Output: variable name, location
- step 2: scan for functions that consume/take ownership of the resource
  - Output: any functions found
- step 3: verify ownership transfer uses no_free_ptr() or return_ptr()
  - From include/linux/cleanup.h:
    "no_free_ptr(var): like a non-atomic xchg(var, NULL), such that the
    cleanup function will be inhibited"
  - no_free_ptr(p): returns p and sets p to NULL (inhibits cleanup)
  - return_ptr(p): shorthand for "return no_free_ptr(p)"
- step 4: verify consumed resources don't get double-freed
- step 5: verify no_free_ptr() usage follows pattern from include/linux/cleanup.h DOC
- step 6: check for retain_and_null_ptr() pattern for conditional consumption

**Examples of correct usage:**

```c
// CORRECT: ERR_PTR-safe cleanup
DEFINE_FREE(kfree, void *, if (_T) kfree(_T))
void *alloc_obj(...)
{
    struct obj *p __free(kfree) = kmalloc(...);
    if (!p)
        return NULL;  // kfree(NULL) is safe

    if (!init_obj(p))
        return NULL;  // kfree(valid ptr) is safe

    return_ptr(p);    // inhibits cleanup, returns p
}

// CORRECT: LIFO ordering with lock
int init(void)
{
    guard(mutex)(&lock);  // acquired first
    struct object *obj __free(remove_free) = alloc_add();  // defined second

    if (!obj)
        return -ENOMEM;  // lock unlocked, then cleanup runs (no-op)

    return_ptr(obj);  // success path
}
```

**Examples of INCORRECT usage:**

```c
// INCORRECT: kfree() cannot handle ERR_PTR
int bad_init(...)
{
    u8 *data __free(kfree) = NULL;

    data = pci_vpd_alloc(pdev, &size);  // returns ERR_PTR or valid pointer
    if (IS_ERR(data))
        return PTR_ERR(data);  // BUG: kfree(ERR_PTR) called!

    return 0;
}

// INCORRECT: Wrong LIFO order
int bad_init(void)
{
    struct object *obj __free(remove_free) = NULL;  // defined first
    guard(mutex)(&lock);  // acquired second
    obj = alloc_add();

    if (!obj)
        return -ENOMEM;  // BUG: cleanup runs before unlock!
                         // remove_free() called without lock held!

    return_ptr(obj);
}

// RISKY: Definition-initialization split (not inherently wrong, but risky)
int risky_init(void)
{
    struct obj *p __free(kfree) = NULL;  // defined with NULL
    guard(mutex)(&lock);

    p = kmalloc(...);  // initialized later

    // This works, but makes LIFO mistakes more likely
    // Better: define p after guard(mutex)
    return_ptr(p);
}

// INCORRECT: Definition-initialization split causing LIFO bug
int bad_init(void)
{
    struct object *obj __free(remove_free) = NULL;  // defined first
    guard(mutex)(&lock);  // guard defined second
    obj = alloc_add();

    if (!obj)
        return -ENOMEM;  // BUG: remove_free() runs before unlock!

    return_ptr(obj);
}

// INCORRECT: Mixing goto with cleanup helpers
int bad_init(void)
{
    struct obj *p __free(kfree) = kmalloc(...);
    struct obj *q = kmalloc(...);

    if (!p || !q)
        goto cleanup;  // BUG: mixing goto with __free()

    return 0;

cleanup:
    kfree(q);  // BUG: partial conversion to cleanup helpers
    return -ENOMEM;
}
```

**Mandatory Self-verification gate:**

**After analysis:** Issues found: [none OR list]
