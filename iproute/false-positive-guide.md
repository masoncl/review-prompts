# False Positive Guide

This guide helps reviewers avoid flagging legitimate code as violations.

## Legacy Code vs New Code

### matches() Function

**Only flag matches() in NEW code.**

```c
/* DO NOT flag - this is existing legacy code */
if (matches(*argv, "broadcast") == 0) {
	/* Existing code uses matches() - leave it alone */
}

/* FLAG THIS - new code should use strcmp() */
+	if (matches(*argv, "device") == 0) {
+		/* New code added in this patch */
+	}
```

**How to tell**: Look for the `+` prefix in diff. Only new lines (with `+`) should be reviewed
for matches() usage. Legacy code is grandfathered in.

### Designated Initializers

**DO NOT flag existing code that doesn't use designated initializers.**

```c
/* DO NOT flag - existing code */
struct ifinfomsg i = { 0 };

/* This is fine in new code */
struct ifinfomsg i = {
	.ifi_family = AF_UNSPEC,
};
```

Designated initializers are preferred for new code but not required for existing code.

## Conditional JSON/Text Output

### When Separate Paths Are Acceptable

Some cases legitimately require different output in JSON vs text mode:

```c
/* ACCEPTABLE - fundamentally different representations */
if (is_json_context()) {
	print_uint(PRINT_JSON, "operstate_index", NULL, state);
} else {
	print_string(PRINT_FP, NULL, "state %s", oper_state_name(state));
}
```

```c
/* ACCEPTABLE - JSON needs array, text doesn't */
if (is_json_context())
	open_json_array(PRINT_JSON, "addresses");

/* ... print addresses ... */

if (is_json_context())
	close_json_array(PRINT_JSON, NULL);
```

### When to Flag

```c
/* FLAG THIS - should use PRINT_ANY */
if (is_json_context())
	print_uint(PRINT_JSON, "mtu", NULL, mtu);
else
	print_uint(PRINT_FP, NULL, "mtu %u", mtu);

/* Should be: */
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
```

**Rule**: If the same data can be represented in both modes with same formatting,
use `PRINT_ANY`. Only use separate paths when truly necessary.

## Error Messages

### fprintf(stderr) Is Correct

**DO NOT flag stderr usage for errors.**

```c
/* CORRECT - errors go to stderr */
fprintf(stderr, "Error: device not specified\n");

/* CORRECT - also acceptable for errors */
fprintf(stderr, "Cannot open file: %s\n", strerror(errno));
```

### Flag stdout Usage

```c
/* FLAG THIS - errors should not go to stdout */
printf("Error: invalid argument\n");
fprintf(stdout, "Error: %s\n", msg);
```

## Comments and Documentation

### Simple Comments Are Fine

**DO NOT flag lack of docbook format** - iproute2 doesn't use it.

```c
/* ACCEPTABLE - simple comment */
/*
 * Set the interface MTU.
 * Returns 0 on success, -1 on error.
 */
static int set_mtu(const char *dev, unsigned int mtu)
```

## Line Length

### User Strings Can Exceed 100 Columns

**DO NOT flag long lines for user-visible strings.**

```c
/* ACCEPTABLE - must be grep-able */
fprintf(stderr, "Error: device name must be less than %d characters\n", IFNAMSIZ);
```

Even if this exceeds 100 columns, it's correct because the string must not be broken.

### Flag Other Long Lines

```c
/* FLAG THIS - code line too long */
if (strcmp(very_long_variable_name, another_very_long_variable_name) == 0 && some_other_condition && yet_another_thing) {
```

**Exception**: Strings must stay unbroken for grep-ability.

## Memory Management

### Free on All Error Paths

**Only flag if memory is leaked on error paths.**

```c
/* FLAG THIS - memory leaked */
char *buf = malloc(size);
if (error_condition)
	return -1;  /* buf leaked! */

/* ACCEPTABLE - memory freed */
char *buf = malloc(size);
if (error_condition) {
	free(buf);
	return -1;
}
```

### goto for Cleanup Is Correct

```c
/* ACCEPTABLE - good pattern */
char *buf = malloc(size);
if (error_condition)
	goto out_free;

/* ... */

out_free:
	free(buf);
	return ret;
```

## Netlink Patterns

### NLA_F_NESTED Is Sometimes Required

**DO NOT flag all nested attributes for missing NLA_F_NESTED.**

```c
/* ACCEPTABLE - many nested attributes don't need the flag */
nest = addattr_nest(&req.n, sizeof(req), IFLA_LINKINFO);

/* REQUIRED for certain attributes */
proplist = addattr_nest(&req.n, sizeof(req), IFLA_PROP_LIST | NLA_F_NESTED);
```

**How to tell**: Check kernel documentation or existing code for the specific attribute.

### sizeof(req) Is Correct

**DO NOT flag sizeof(req) as wrong size.**

```c
/* ACCEPTABLE - this is the standard pattern */
struct {
	struct nlmsghdr n;
	struct ifinfomsg i;
	char buf[1024];
} req;

addattr32(&req.n, sizeof(req), IFLA_MTU, mtu);
```

The `sizeof(req)` is the maximum buffer size, which is correct.

## String Handling

### strncpy Is Sometimes Appropriate

```c
/* ACCEPTABLE - with explicit null termination */
strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);
ifr.ifr_name[IFNAMSIZ - 1] = '\0';
```

**Flag if**: No null termination or potential overflow.

## Return Value Checking

### Some Functions Don't Need Checking

**DO NOT flag all unchecked return values.**

```c
/* ACCEPTABLE - close() failures often ignored */
close(fd);

/* ACCEPTABLE - print functions rarely checked */
printf("Informational message\n");
```

### Flag Important Unchecked Returns

```c
/* FLAG THIS - must check netlink operations */
rtnl_talk(&rth, &req.n, NULL);

/* FLAG THIS - must check allocation */
buf = malloc(size);
strcpy(buf, src);
```

**Rule**: Check returns for:
- Memory allocation (malloc, calloc, realloc)
- Netlink operations (rtnl_talk, rtnl_dump_request)
- File operations (fopen, read, write)
- Critical system calls

## Kernel Version Checks

### Never in Runtime Code

```c
/* FLAG THIS - no version checks in code */
#ifdef KERNEL_VERSION
#if LINUX_VERSION_CODE >= KERNEL_VERSION(5,10,0)
	/* use new feature */
#endif
#endif
```

### Acceptable in Build System

Version checks in Makefiles or configure scripts are acceptable for build-time
feature detection, but not in C code.

## Variable Declarations

### Christmas Tree NOT Required

**DO NOT flag non-ordered variable declarations.**

```c
/* ACCEPTABLE - iproute2 doesn't require ordering */
int ret;
struct nlmsghdr *answer;
const char *filter_dev = NULL;
unsigned int mtu;
```

This is different from kernel code which requires reverse-length ordering.

## Braces

### Consistency Within Function

```c
/* ACCEPTABLE - consistent use */
if (condition) {
	do_this();
	do_that();
} else {
	otherwise();
}

/* FLAG THIS - inconsistent */
if (condition) {
	do_this();
} else
	otherwise();  /* Should have braces since if-branch has them */
```

## Common False Positives Summary

1. **matches() in old code** - Only flag in new additions (lines with `+`)
2. **Long user strings** - Acceptable, must be grep-able
3. **Simple comments** - Docbook format not required
4. **fprintf(stderr)** - Correct for errors
5. **No Christmas tree** - Variable ordering not required
6. **Conditional JSON** - Sometimes legitimately needed
7. **sizeof(req)** - Standard pattern for netlink
8. **NLA_F_NESTED** - Only some attributes need it
9. **goto for cleanup** - Recommended pattern
10. **close() unchecked** - Often acceptable

## When Uncertain

If unsure whether something is a violation:
1. Check if it's in existing code (no `+` prefix) - likely acceptable
2. Look for similar patterns in the same file or subsystem
3. Check if there's a good reason for the pattern
4. Consider if flagging would improve the code
5. When in doubt, don't flag - ask for clarification instead
