# iproute2 Coding Style

iproute2 follows Linux kernel coding style with userspace-specific exceptions.
Reference: https://www.kernel.org/doc/html/latest/process/coding-style.html

## File Headers

Every source file must start with:

```c
/* SPDX-License-Identifier: GPL-2.0-or-later */
/*
 * filename.c		Brief description
 *
 * Authors:	Name <email@example.org>
 */
```

## Indentation and Spacing

### Basic Rules
- Tabs (8 characters) for indentation
- No spaces for indentation (except continuation lines)
- Line length: prefer 80 columns, accept up to 100 for readability
- **Never break user-visible strings** - they must be grep-able

### Switch Statements

Align case labels with switch:

```c
switch (suffix) {
case 'G':
case 'g':
	mem <<= 30;
	break;
case 'M':
case 'm':
	mem <<= 20;
	break;
default:
	break;
}
```

### Spaces Around Operators

Use space after these keywords:
```c
if, switch, case, for, do, while
```

No space after these:
```c
sizeof, typeof, alignof, __attribute__
```

Examples:
```c
s = sizeof(struct file);      /* correct */
s = sizeof( struct file );    /* WRONG */
```

One space around binary/ternary operators:
```c
=  +  -  <  >  *  /  %  |  &  ^  <=  >=  ==  !=  ?  :
```

No space after unary operators:
```c
&  *  +  -  ~  !  sizeof  typeof  alignof  __attribute__
```

No space around `.` and `->` structure member operators.

## Braces

### Functions

Opening brace on new line:

```c
int function(int x)
{
	body of function
}
```

### Control Structures

Opening brace on same line:

```c
if (x is true) {
	we do y
}

for (i = 0; i < max; i++) {
	do_something(i);
}
```

### Single Statements

No braces when unnecessary:

```c
if (condition)
	action();
```

### Consistency Rule

If one branch needs braces, all branches get braces:

```c
if (condition) {
	do_this();
	do_that();
} else {
	otherwise();
}
```

## Pointers

The `*` is adjacent to the **variable name**, not the type:

```c
char *linux_banner;                          /* correct */
char* linux_banner;                          /* WRONG */
unsigned long long memparse(char *ptr, char **retptr);
```

## Naming Conventions

- Lowercase with underscores: `count_active_users()`
- **No** CamelCase or Hungarian notation
- Global variables/functions: descriptive names
- Local variables: short names (`i`, `tmp`, `ret`)
- Avoid `master/slave`, `blacklist/whitelist` terminology

## Variable Declarations

### No Christmas Tree Required

**Important**: Unlike the kernel, iproute2 does **NOT** require "Christmas tree"
(reverse-fir-tree) ordering by line length.

Acceptable:
```c
int ret;
struct nlmsghdr *answer;
const char *filter_dev = NULL;
__u32 filt_mask = IFLA_STATS_FILTER_BIT(IFLA_STATS_AF_SPEC);
```

One declaration per line to allow comments on each:

```c
int ret;                    /* return value */
struct nlmsghdr *answer;    /* netlink response */
```

### Structure Initialization

Use designated initializers:

```c
struct iplink_req req = {
	.n.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg)),
	.n.nlmsg_flags = NLM_F_REQUEST,
	.i.ifi_family = preferred_family,
};
```

## Comments

### Multi-line Format

```c
/*
 * This is the preferred style for multi-line
 * comments in iproute2 source code.
 *
 * Description: A column of asterisks on the left,
 * with beginning and ending almost-blank lines.
 */
```

### Content Guidelines

- Explain **what** the code does, not **how**
- Avoid comments inside function bodies (suggests function is too complex)
- **No** kernel docbook format - use simple C comments:

```c
/*
 * Brief description of what the function does.
 *
 * Longer description if needed.
 * Returns 0 on success, negative on failure.
 */
static int my_function(int argc, char **argv)
```

## Functions

### Design Principles

- Short functions that do one thing
- Limit to 5-10 local variables per function
- Separate functions with one blank line

### Centralized Cleanup

Use goto for cleanup with multiple exit points:

```c
int fun(int a)
{
	int result = 0;
	char *buffer;

	buffer = malloc(SIZE);
	if (!buffer)
		return -ENOMEM;

	if (condition1) {
		while (loop1) {
			...
		}
		result = 1;
		goto out_free_buffer;
	}
	...
out_free_buffer:
	free(buffer);
	return result;
}
```

Use descriptive label names like `out_free_buffer:`, not `err1:`.

## Macros and Constants

### Naming

- Macro constants: `CAPITALIZED_WITH_UNDERSCORES`
- Prefer enums over `#define` for related constants
- Prefer inline functions over function-like macros

### Multi-statement Macros

Must use do-while:

```c
#define MACROFUN(a, b, c)		\
	do {				\
		if (a == 5)		\
			do_this(b, c);	\
	} while (0)
```

## Error Messages

**Critical**: Use `fprintf(stderr, ...)` for all errors to avoid corrupting
JSON output on stdout:

```c
/* CORRECT */
fprintf(stderr, "Error: argument of \"%s\" must be \"on\" or \"off\", not \"%s\"\n",
	msg, realval);

/* WRONG - corrupts JSON output */
printf("Error: invalid argument\n");
fprintf(stdout, "Error: %s\n", msg);
```

## Usage Functions

Every command should provide help:

```c
static void usage(void) __attribute__((noreturn));

static void usage(void)
{
	fprintf(stderr,
		"Usage: ip address {add|change|replace} IFADDR dev IFNAME\n"
		"       ip address del IFADDR dev IFNAME\n"
		"       ip address show [ dev IFNAME ]\n"
		...);
	exit(-1);
}
```

## String Handling

### Never Break User-Visible Strings

```c
/* WRONG - user cannot grep for complete message */
fprintf(stderr, "Error: could not find "
                "device\n");

/* CORRECT - keep on one line even if >80 cols */
fprintf(stderr, "Error: could not find device\n");
```

This rule overrides line length limits for grep-ability.

## Complete Example

```c
/* SPDX-License-Identifier: GPL-2.0-or-later */
/*
 * iplink.c		Link configuration
 *
 * Authors:	Alexey Kuznetsov, <kuznet@ms2.inr.ac.ru>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "utils.h"
#include "ip_common.h"

static void usage(void) __attribute__((noreturn));

static void usage(void)
{
	fprintf(stderr, "Usage: ip link set DEVICE [ up | down ]\n");
	exit(-1);
}

int do_iplink(int argc, char **argv)
{
	int ret = 0;
	char *dev = NULL;

	while (argc > 0) {
		if (strcmp(*argv, "dev") == 0) {
			NEXT_ARG();
			dev = *argv;
		} else if (strcmp(*argv, "help") == 0) {
			usage();
		} else {
			fprintf(stderr, "Unknown argument: %s\n", *argv);
			usage();
		}
		argc--;
		argv++;
	}

	if (!dev) {
		fprintf(stderr, "Error: device not specified\n");
		return -1;
	}

	return ret;
}
```

## Style Checklist

- [ ] SPDX identifier present
- [ ] Tabs (not spaces) for indentation
- [ ] Lines ≤100 characters (prefer 80)
- [ ] User strings not broken
- [ ] Braces: functions on new line, control on same line
- [ ] `*` adjacent to variable name
- [ ] Lowercase_with_underscores naming
- [ ] Designated initializers for structs
- [ ] Error messages to stderr
- [ ] Comments explain what, not how
- [ ] goto used for cleanup when appropriate
