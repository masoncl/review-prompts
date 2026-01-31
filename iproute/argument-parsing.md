# Command-Line Argument Parsing

## Critical Rule: strcmp() Not matches()

**New code must use `strcmp()` for exact string comparison only.**

The `matches()` function allows abbreviations and has caused problems when new
arguments are added that share prefixes with existing ones.

```c
/* CORRECT - New code should use strcmp() */
if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	/* ... */
}

/* LEGACY - matches() allows abbreviations, DO NOT use in new code */
if (matches(*argv, "broadcast") == 0) {  /* matches "b", "br", "bro", etc. */
	/* ... */
}
```

## Argument Processing Macros

Use the standard macros for argument iteration:

```c
NEXT_ARG();           /* Move to next argument, exit with error if none */
NEXT_ARG_OK();        /* Check if next argument exists */
PREV_ARG();           /* Move back one argument */
```

## Common Patterns

### Basic Argument Loop

```c
while (argc > 0) {
	if (strcmp(*argv, "dev") == 0) {
		NEXT_ARG();
		dev = *argv;
	} else if (strcmp(*argv, "mtu") == 0) {
		NEXT_ARG();
		if (get_unsigned(&mtu, *argv, 0))
			invarg("Invalid \"mtu\" value\n", *argv);
	} else if (strcmp(*argv, "help") == 0) {
		usage();
	} else {
		fprintf(stderr, "Unknown argument: %s\n", *argv);
		exit(-1);
	}
	argc--; argv++;
}
```

### Multiple Values

```c
if (strcmp(*argv, "via") == 0) {
	NEXT_ARG();
	if (get_addr(&gateway, *argv, family))
		invarg("Invalid gateway address\n", *argv);
} else if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	dev = *argv;
}
```

### Optional Arguments

```c
if (strcmp(*argv, "limit") == 0) {
	NEXT_ARG();
	if (get_unsigned(&limit, *argv, 0))
		invarg("Invalid limit\n", *argv);
} else if (strcmp(*argv, "burst") == 0) {
	NEXT_ARG();
	if (get_unsigned(&burst, *argv, 0))
		invarg("Invalid burst\n", *argv);
}
```

### Checking for Duplicates

```c
if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	if (dev)
		duparg("dev", *argv);
	dev = *argv;
}
```

## Standard Error Helpers

```c
invarg("invalid value", *argv);     /* Invalid argument value */
duparg("device", *argv);            /* Duplicate argument */
duparg2("dev", *argv);              /* Duplicate argument variant */
missarg("required argument");       /* Missing required argument */
nodev(devname);                     /* Device not found */
```

### Helper Usage Examples

```c
/* Invalid value */
if (get_unsigned(&mtu, *argv, 0))
	invarg("Invalid MTU value\n", *argv);

/* Duplicate argument */
if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	if (dev)
		duparg("dev", *argv);
	dev = *argv;
}

/* Missing required argument */
if (!dev)
	missarg("device");

/* Device not found */
idx = ll_name_to_index(dev);
if (!idx)
	nodev(dev);
```

## Usage Functions

Each command should have a `usage()` function that displays help:

```c
static void usage(void) __attribute__((noreturn));

static void usage(void)
{
	fprintf(stderr,
		"Usage: ip address {add|change|replace} IFADDR dev IFNAME\n"
		"       ip address del IFADDR dev IFNAME\n"
		"       ip address show [ dev IFNAME ]\n"
		"       ip address flush [ dev IFNAME ]\n"
		"\n"
		"IFADDR := PREFIX | ADDR peer PREFIX\n"
		"          [ broadcast ADDR ] [ anycast ADDR ]\n"
		"          [ label STRING ] [ scope SCOPE-ID ]\n");
	exit(-1);
}
```

### Usage Guidelines

- Mark function as `__attribute__((noreturn))`
- Write to stderr using `fprintf(stderr, ...)`
- Always call `exit(-1)` at the end
- Show command structure clearly
- Include common options
- Use uppercase for placeholders (IFNAME, ADDR, etc.)

## Validation Helpers

### Numeric Values

```c
/* Unsigned integer */
unsigned int value;
if (get_unsigned(&value, *argv, 0))
	invarg("Invalid value\n", *argv);

/* Unsigned with base */
unsigned int hex_value;
if (get_unsigned(&hex_value, *argv, 16))
	invarg("Invalid hex value\n", *argv);

/* Signed integer */
int signed_value;
if (get_integer(&signed_value, *argv, 0))
	invarg("Invalid integer\n", *argv);
```

### Addresses

```c
inet_prefix addr;

/* Get address */
if (get_addr(&addr, *argv, family))
	invarg("Invalid address\n", *argv);

/* Get prefix */
if (get_prefix(&addr, *argv, family))
	invarg("Invalid prefix\n", *argv);
```

### Strings

```c
/* Simple string copy */
name = *argv;

/* Limited length string */
if (strlen(*argv) >= IFNAMSIZ)
	invarg("Name too long\n", *argv);
strncpy(ifr.ifr_name, *argv, IFNAMSIZ - 1);
```

## Common Bugs

### Missing NEXT_ARG()

```c
/* WRONG - still pointing at keyword */
if (strcmp(*argv, "mtu") == 0) {
	if (get_unsigned(&mtu, *argv, 0))  /* *argv is "mtu"! */
		invarg("Invalid MTU\n", *argv);
}

/* CORRECT - advance to value */
if (strcmp(*argv, "mtu") == 0) {
	NEXT_ARG();
	if (get_unsigned(&mtu, *argv, 0))
		invarg("Invalid MTU\n", *argv);
}
```

### Using matches() in New Code

```c
/* WRONG - allows abbreviations */
if (matches(*argv, "device") == 0) {
	/* Will match "d", "de", "dev", "devi", etc. */
}

/* CORRECT - exact match only */
if (strcmp(*argv, "device") == 0) {
	/* Only matches "device" exactly */
}
```

### Not Checking for Duplicates

```c
/* WRONG - silently accepts duplicate */
if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	dev = *argv;
}

/* BETTER - warn about duplicate */
if (strcmp(*argv, "dev") == 0) {
	NEXT_ARG();
	if (dev)
		duparg("dev", *argv);
	dev = *argv;
}
```

### Missing Validation

```c
/* WRONG - no validation */
if (strcmp(*argv, "mtu") == 0) {
	NEXT_ARG();
	mtu = atoi(*argv);  /* Accepts invalid input */
}

/* CORRECT - validate input */
if (strcmp(*argv, "mtu") == 0) {
	NEXT_ARG();
	if (get_unsigned(&mtu, *argv, 0))
		invarg("Invalid MTU\n", *argv);
}
```

## Complete Example

```c
static void usage(void) __attribute__((noreturn));

static void usage(void)
{
	fprintf(stderr,
		"Usage: ip link set DEVICE [ up | down ]\n"
		"                          [ mtu MTU ]\n"
		"                          [ address LLADDR ]\n");
	exit(-1);
}

static int do_set(int argc, char **argv)
{
	char *dev = NULL;
	unsigned int mtu = 0;
	char *addr = NULL;
	int up = -1;

	while (argc > 0) {
		if (strcmp(*argv, "dev") == 0) {
			NEXT_ARG();
			if (dev)
				duparg("dev", *argv);
			dev = *argv;
		} else if (strcmp(*argv, "up") == 0) {
			up = 1;
		} else if (strcmp(*argv, "down") == 0) {
			up = 0;
		} else if (strcmp(*argv, "mtu") == 0) {
			NEXT_ARG();
			if (mtu)
				duparg("mtu", *argv);
			if (get_unsigned(&mtu, *argv, 0))
				invarg("Invalid MTU\n", *argv);
		} else if (strcmp(*argv, "address") == 0) {
			NEXT_ARG();
			if (addr)
				duparg("address", *argv);
			addr = *argv;
		} else if (strcmp(*argv, "help") == 0) {
			usage();
		} else {
			fprintf(stderr, "Unknown argument: %s\n", *argv);
			usage();
		}
		argc--; argv++;
	}

	if (!dev) {
		fprintf(stderr, "Error: device not specified\n");
		return -1;
	}

	/* Perform operations with validated arguments */
	return 0;
}
```

## No Kernel Docbook Format

iproute2 does **not** use the kernel's docbook documentation format.
Function documentation should use simple C comments:

```c
/*
 * Brief description of what the function does.
 *
 * Longer description if needed.
 * Returns 0 on success, negative on failure.
 */
static int my_function(int argc, char **argv)
```

## Boolean and Toggle Arguments

```c
/* Boolean flags */
if (strcmp(*argv, "verbose") == 0) {
	verbose = 1;
} else if (strcmp(*argv, "quiet") == 0) {
	quiet = 1;
}

/* On/Off arguments */
if (strcmp(*argv, "learning") == 0) {
	NEXT_ARG();
	if (strcmp(*argv, "on") == 0) {
		learning = 1;
	} else if (strcmp(*argv, "off") == 0) {
		learning = 0;
	} else {
		invarg("Invalid learning value\n", *argv);
	}
}
```

## Argument Checklist

- [ ] Use `strcmp()`, not `matches()`
- [ ] Call `NEXT_ARG()` after keyword before reading value
- [ ] Validate all numeric inputs with get_unsigned/get_integer
- [ ] Check for duplicate arguments where appropriate
- [ ] Provide clear error messages
- [ ] Include `usage()` function
- [ ] Handle "help" argument
- [ ] Check required arguments are present
