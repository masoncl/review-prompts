# Common Bug Patterns in iproute2

## Argument Parsing Bugs

### Using matches() in New Code

**Bug**: Using `matches()` instead of `strcmp()` for argument comparison.

**Why it's wrong**: The `matches()` function allows abbreviations, which can
cause unexpected behavior when new arguments are added that share a prefix.

**Example (BAD)**:
```c
if (matches(*argv, "device") == 0) {  /* Matches "d", "de", "dev", etc. */
```

**Example (GOOD)**:
```c
if (strcmp(*argv, "device") == 0) {  /* Only matches "device" exactly */
```

### Missing NEXT_ARG()

**Bug**: Forgetting to call `NEXT_ARG()` after accepting a keyword.

**Example (BAD)**:
```c
if (strcmp(*argv, "mtu") == 0) {
    mtu = atoi(*argv);  /* Still pointing at "mtu", not the value! */
}
```

**Example (GOOD)**:
```c
if (strcmp(*argv, "mtu") == 0) {
    NEXT_ARG();
    mtu = atoi(*argv);
}
```

## JSON Output Bugs

### Missing close_json_object()

**Bug**: Opening a JSON object but not closing it.

```c
open_json_object("link");
print_string(PRINT_ANY, "name", "%s", name);
/* Missing: close_json_object(); */
```

### Error Messages to stdout

**Bug**: Using `printf()` or `fprintf(stdout, ...)` for error messages.

**Why it's wrong**: Corrupts JSON output when `-json` flag is used.

**Example (BAD)**:
```c
printf("Error: invalid argument\n");
```

**Example (GOOD)**:
```c
fprintf(stderr, "Error: invalid argument\n");
```

### Using fprintf for Display Output

**Bug**: Using `fprintf(fp, ...)` instead of `print_XXX()` helpers.

**Example (BAD)**:
```c
fprintf(fp, "mtu %u ", mtu);
```

**Example (GOOD)**:
```c
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
```

## Memory Bugs

### Missing NULL Check

**Bug**: Not checking malloc return value.

```c
char *buf = malloc(size);
strcpy(buf, src);  /* Crash if malloc failed! */
```

### Memory Leak on Error Path

**Bug**: Returning early without freeing allocated memory.

```c
char *buf = malloc(size);
if (some_error) {
    return -1;  /* Leaks buf! */
}
```

**Fix**: Use goto for centralized cleanup.

## Netlink Bugs

### Missing Nested Attribute End

**Bug**: Opening a nested attribute but not closing it.

```c
addattr_nest(&req.n, sizeof(req), IFLA_PROP_LIST);
addattr_l(&req.n, sizeof(req), IFLA_ALT_IFNAME, name, strlen(name) + 1);
/* Missing: addattr_nest_end(&req.n, proplist); */
```

### Ignoring Netlink Errors

**Bug**: Not checking return value from netlink operations.

```c
rtnl_talk(&rth, &req.n, NULL);  /* Ignoring return value! */
```

## String Handling Bugs

### Breaking User-Visible Strings

**Bug**: Splitting strings that users might grep for.

**Example (BAD)**:
```c
fprintf(stderr, "Error: could not find "
                "device\n");
```

**Example (GOOD)**:
```c
fprintf(stderr, "Error: could not find device\n");
```

## Kernel Compatibility Bugs

### Assuming Feature Exists

**Bug**: Using a kernel feature without checking if it's available.

**Fix**: Check return values, handle `EOPNOTSUPP` gracefully.

### uapi Update Without Reference

**Bug**: Updating uapi headers without referencing the upstream kernel commit.

**Fix**: Always include the kernel commit hash in the patch description.
