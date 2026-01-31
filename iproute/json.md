# JSON Output Support

**All commands must support JSON output.** Use the helper functions from
`json_print.h` to ensure consistent output in both regular and JSON modes.

## Key Principles

1. **Avoid special-casing JSON** - Let the library handle the differences
2. **Use print_XXX helpers** - Do not use `fprintf(fp, ...)` directly for display output
3. **Error messages to stderr** - Use `fprintf(stderr, ...)` for errors to avoid corrupting JSON
4. **Pair open/close calls** - Every `open_json_object()` needs `close_json_object()`,
   every `open_json_array()` needs `close_json_array()`
5. **Validate output** - Test JSON output is valid and well-formed

## JSON Validation Checklist

When reviewing JSON output code, verify:

- [ ] **Balanced brackets** - Every `{` has matching `}`, every `[` has matching `]`
- [ ] **Paired calls** - Every `open_json_object()` has `close_json_object()`
- [ ] **Paired arrays** - Every `open_json_array()` has `close_json_array()`
- [ ] **Valid structure** - Objects contain name/value pairs, arrays contain values
- [ ] **Unique keys** - No duplicate keys within same object
- [ ] **Proper quoting** - String values in double quotes
- [ ] **Valid values** - Booleans are `true`/`false`, null is `null` (lowercase)
- [ ] **No trailing commas** - Last member has no comma
- [ ] **Escaped characters** - Special characters properly escaped in strings
- [ ] **Valid numbers** - No leading zeros (except `0` itself)

## Validating JSON Output

### Manual Validation with jq

Test JSON output is valid using `jq`:

```bash
# Valid JSON - jq will pretty-print it
$ ip -json link show | jq .
[
  {
    "ifindex": 1,
    "ifname": "lo",
    "flags": ["LOOPBACK", "UP"],
    "mtu": 65536,
    "operstate": "UNKNOWN"
  }
]

# Invalid JSON - jq will report error
$ ip -json link show | jq .
parse error: Expected separator between values at line 2, column 5
```

### Validation with Python

```bash
# Quick validation
$ ip -json link show | python3 -m json.tool

# Or with error checking
$ ip -json link show > output.json
$ python3 << 'EOF'
import json
try:
    with open('output.json') as f:
        data = json.load(f)
    print("Valid JSON ✓")
    print(f"Contains {len(data)} items")
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
EOF
```

### Automated Testing

```bash
# Test all commands for valid JSON
for cmd in "ip link show" "ip addr show" "ip route show"; do
    echo "Testing: $cmd"
    if $cmd -json 2>/dev/null | jq . >/dev/null 2>&1; then
        echo "  ✓ Valid JSON"
    else
        echo "  ✗ Invalid JSON"
    fi
done
```

## Bracket/Brace Matching

### Tracking Open/Close Calls

Every open must have a matching close:

```c
/* CORRECT - balanced */
open_json_object("link");
    print_string(PRINT_ANY, "name", "%s", name);
    open_json_array(PRINT_ANY, "flags");
        print_string(PRINT_ANY, NULL, "%s", "UP");
    close_json_array(PRINT_ANY, "");
close_json_object();

/* WRONG - missing close_json_array */
open_json_object("link");
    print_string(PRINT_ANY, "name", "%s", name);
    open_json_array(PRINT_ANY, "flags");
        print_string(PRINT_ANY, NULL, "%s", "UP");
    /* Missing close_json_array() */
close_json_object();

/* WRONG - missing close_json_object */
open_json_object("link");
    print_string(PRINT_ANY, "name", "%s", name);
/* Missing close_json_object() */
```

### Manual Bracket Tracking

When reviewing code, count brackets:

```c
open_json_object(NULL);              // { depth=1
    open_json_object("stats");       // { depth=2
        print_u64(...);
    close_json_object();             // } depth=1
    open_json_array(PRINT_ANY, "flags"); // [ depth=2 (different type)
        print_string(...);
    close_json_array(PRINT_ANY, ""); // ] depth=1
close_json_object();                 // } depth=0 ✓
```

## JSON Structure Rules

### Name/Value Pairs in Objects

```c
/* CORRECT - object contains name/value pairs */
open_json_object("link");
print_string(PRINT_ANY, "ifname", "%s", name);  // "ifname": "eth0"
print_uint(PRINT_ANY, "mtu", "mtu %u", mtu);    // "mtu": 1500
close_json_object();

/* Result: {"ifname": "eth0", "mtu": 1500} */
```

### Arrays Contain Values

```c
/* CORRECT - array contains values */
open_json_array(PRINT_ANY, "flags");
print_string(PRINT_ANY, NULL, "%s", "UP");
print_string(PRINT_ANY, NULL, "%s", "BROADCAST");
close_json_array(PRINT_ANY, "");

/* Result: "flags": ["UP", "BROADCAST"] */
```

### Unique Keys

Each key within an object must be unique:

```c
/* WRONG - duplicate "mtu" key */
print_uint(PRINT_ANY, "mtu", "mtu %u", mtu);
print_uint(PRINT_ANY, "mtu", "qlen %u", qlen);  // BAD: reuses "mtu"

/* CORRECT - unique keys */
print_uint(PRINT_ANY, "mtu", "mtu %u", mtu);
print_uint(PRINT_ANY, "qlen", "qlen %u", qlen);
```

## String Handling

### Proper Quoting

String values must be in double quotes:

```c
/* CORRECT - produces "name": "eth0" */
print_string(PRINT_ANY, "name", "%s", "eth0");

/* WRONG - don't manually add quotes */
print_string(PRINT_ANY, "name", "\"%s\"", "eth0");  // Produces ""eth0""
```

### Escaping Special Characters

The print functions handle escaping automatically:

```c
/* Input with special chars */
const char *desc = "Interface \"eth0\"\nLine 2";

/* CORRECT - library handles escaping */
print_string(PRINT_ANY, "description", "%s", desc);
/* Produces: "description": "Interface \"eth0\"\nLine 2" */
```

Special characters that are escaped:
- `"` → `\"`
- `\` → `\\`
- `/` → `\/` (optional)
- `\b` → backspace
- `\f` → form feed
- `\n` → newline
- `\r` → carriage return
- `\t` → tab

## Number Handling

### No Leading Zeros

```c
/* CORRECT */
print_uint(PRINT_ANY, "mtu", "mtu %u", 1500);  // "mtu": 1500

/* WRONG - would produce leading zero */
print_uint(PRINT_ANY, "mtu", "mtu %04u", 1500);  // Text: "mtu 1500", JSON: 1500
```

The JSON output ignores format specifiers for numbers, but avoid confusion.

### Floating Point

```c
/* CORRECT - double precision */
print_float(PRINT_ANY, "rate", "%.2f", 1.5);  // "rate": 1.5
```

## Boolean and Null Values

### Booleans

```c
/* CORRECT - produces true/false (lowercase) */
print_bool(PRINT_ANY, "enabled", "enabled", 1);     // "enabled": true
print_bool(PRINT_ANY, "disabled", "disabled", 0);   // "disabled": false

/* WRONG - don't use strings for booleans */
print_string(PRINT_ANY, "enabled", "%s", "true");   // "enabled": "true" (string, not boolean)
```

### Null Values

```c
/* CORRECT - produces null (lowercase) */
print_null(PRINT_ANY, "gateway", "via %s", NULL);  // "gateway": null
```

## Comma Handling

### No Trailing Commas

The library handles commas automatically. Do not add manual commas in keys:

```c
/* CORRECT - library adds commas */
print_uint(PRINT_ANY, "mtu", "mtu %u", mtu);
print_uint(PRINT_ANY, "qlen", "qlen %u", qlen);
/* Produces: "mtu": 1500, "qlen": 1000 */

/* WRONG - don't add commas to keys */
print_uint(PRINT_ANY, "mtu,", "mtu %u", mtu);  // BAD: "mtu,": 1500
```

## Initializing JSON Context

```c
#include "json_print.h"

/* At the start of output */
new_json_obj(json);      /* json is a global flag set by -json option */

/* At the end of output */
delete_json_obj();
```

## Correct Usage Pattern

**Use `PRINT_ANY` to handle both JSON and text output in one call:**

```c
/* GOOD - single call handles both modes */
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
print_string(PRINT_ANY, "name", "%s ", name);

/* BAD - do not special-case JSON and text separately */
if (is_json_context()) {
    print_uint(PRINT_JSON, "foo", NULL, bar);
} else {
    print_uint(PRINT_FP, NULL, "foo %u", bar);
}
```

### When Separate Paths Are Acceptable

Only use separate JSON/text paths when truly necessary:

```c
/* ACCEPTABLE - fundamentally different representations */
if (is_json_context()) {
    print_uint(PRINT_JSON, "operstate_index", NULL, state);
} else {
    print_string(PRINT_FP, NULL, "state %s", oper_state_name(state));
}
```

## Output Type Enum

```c
enum output_type {
    PRINT_FP = 1,    /* Text output only */
    PRINT_JSON = 2,  /* JSON output only */
    PRINT_ANY = 4,   /* Both text and JSON (preferred) */
};
```

## Available Print Functions

### Basic Types

```c
print_string(PRINT_ANY, "name", "%s ", name);
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
print_int(PRINT_ANY, "value", "%d", value);
print_u64(PRINT_ANY, "bytes", "%llu", bytes);
print_s64(PRINT_ANY, "offset", "%lld", offset);
print_bool(PRINT_ANY, "up", "%s", is_up);
print_on_off(PRINT_ANY, "enabled", "%s ", enabled);
print_null(PRINT_ANY, "field", NULL, NULL);
```

### Numeric Formatting

```c
print_hex(PRINT_ANY, "mask", "0x%x", mask);
print_0xhex(PRINT_FP, NULL, "state %#llx", state);
print_luint(PRINT_ANY, "count", "%lu", count);
print_lluint(PRINT_ANY, "total", "%llu", total);
print_hu(PRINT_ANY, "port", "%hu", port);
print_hhu(PRINT_ANY, "flags", "%hhu", flags);
print_float(PRINT_ANY, "value", "%.2f", value);
```

### Time and Rate

```c
print_rate(PRINT_ANY, "rate", "%s", rate);
print_tv(PRINT_ANY, "time", "%s", &timeval);
```

### Newlines

```c
print_nl();  /* Prints newline in text mode, nothing in JSON mode */
```

## Color Support

```c
print_color_string(PRINT_ANY, COLOR_IFNAME, "ifname", "%s", ifname);
print_color_string(PRINT_ANY, COLOR_MAC, "address", "%s ", mac_addr);
print_color_uint(PRINT_ANY, COLOR_NONE, "mtu", "mtu %u ", mtu);
```

Colors: `COLOR_NONE`, `COLOR_IFNAME`, `COLOR_MAC`, `COLOR_INET`, `COLOR_INET6`

## Human-Readable vs Raw Values

**Critical**: JSON should contain raw values, text should be human-readable.

```c
/* CORRECT - print_rate() handles both */
print_rate(PRINT_ANY, "target", "target %s", rate);
/* Text: "target 5ms", JSON: "target": 4999 (microseconds) */

/* CORRECT - print_tv() handles both */
print_tv(PRINT_ANY, "time", "%s", &tv);
/* Text: "2.5s", JSON: "time": 2500000 (microseconds) */
```

## Complete Example with Validation

```c
static int print_link(struct nlmsghdr *n, void *arg)
{
    FILE *fp = arg;
    struct ifinfomsg *ifi = NLMSG_DATA(n);
    struct rtattr *tb[IFLA_MAX + 1];
    int len = n->nlmsg_len;
    const char *name;

    len -= NLMSG_LENGTH(sizeof(*ifi));
    if (len < 0)
        return -1;

    parse_rtattr(tb, IFLA_MAX, IFLA_RTA(ifi), len);

    if (!tb[IFLA_IFNAME])
        return -1;

    name = rta_getattr_str(tb[IFLA_IFNAME]);

    /* Open object - must close */
    open_json_object(NULL);

    /* Basic fields with unique keys */
    print_int(PRINT_ANY, "ifindex", "%d: ", ifi->ifi_index);
    print_color_string(PRINT_ANY, COLOR_IFNAME, "ifname", "%s", name);

    /* Nested object */
    if (tb[IFLA_STATS64]) {
        struct rtnl_link_stats64 *stats = RTA_DATA(tb[IFLA_STATS64]);

        open_json_object("stats64");
        print_u64(PRINT_ANY, "rx_bytes", " RX: %llu", stats->rx_bytes);
        print_u64(PRINT_ANY, "tx_bytes", " TX: %llu", stats->tx_bytes);
        close_json_object();  /* Close nested object */
    }

    /* Array with unique values */
    if (ifi->ifi_flags) {
        open_json_array(PRINT_ANY, "flags");
        if (ifi->ifi_flags & IFF_UP)
            print_string(PRINT_ANY, NULL, "%s", "UP");
        if (ifi->ifi_flags & IFF_BROADCAST)
            print_string(PRINT_ANY, NULL, "%s", "BROADCAST");
        close_json_array(PRINT_ANY, "");  /* Close array */
    }

    print_nl();
    close_json_object();  /* Close main object */

    return 0;
}
```

### Validate This Output

```bash
# Test the output
$ ip -json link show | jq . > /dev/null && echo "Valid JSON ✓"

# Or with Python
$ ip -json link show | python3 -c "import json,sys; json.load(sys.stdin); print('Valid JSON ✓')"
```

## Common JSON Bugs

### Missing close_json_object()

```c
/* WRONG - unbalanced */
open_json_object("link");
print_string(PRINT_ANY, "name", "%s", name);
/* Missing: close_json_object(); */
```

**Symptom**: `jq` reports "parse error: Expected separator"

### Missing close_json_array()

```c
/* WRONG - unbalanced */
open_json_array(PRINT_ANY, "flags");
print_string(PRINT_ANY, NULL, "%s", "UP");
/* Missing: close_json_array(PRINT_ANY, ""); */
```

**Symptom**: `jq` reports "parse error: Expected separator" or "Unexpected EOF"

### Duplicate Keys

```c
/* WRONG - same key twice */
print_uint(PRINT_ANY, "mtu", "mtu %u", 1500);
print_uint(PRINT_ANY, "mtu", "mtu %u", 9000);
```

**Symptom**: Valid JSON, but second value overwrites first (lossy)

### Error Messages to stdout

```c
/* WRONG - corrupts JSON output */
printf("Error: invalid argument\n");

/* CORRECT */
fprintf(stderr, "Error: invalid argument\n");
```

**Symptom**: `jq` reports "Invalid numeric literal" or similar

### Using fprintf for Display

```c
/* WRONG */
fprintf(fp, "mtu %u ", mtu);

/* CORRECT */
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
```

**Symptom**: Text appears in JSON output, breaking structure

## Testing Checklist

Always test both output modes:

```bash
# Text output
ip link show

# JSON output - validate with jq
ip -json link show | jq .

# Pretty JSON output - validate with Python
ip -json -pretty link show | python3 -m json.tool

# Save and validate
ip -json link show > output.json
jq empty output.json && echo "Valid ✓" || echo "Invalid ✗"
```

Verify:
- [ ] No errors to stdout in either mode
- [ ] JSON is valid (jq/python validate successfully)
- [ ] All objects/arrays properly closed
- [ ] No duplicate keys
- [ ] Raw values in JSON, human-readable in text
- [ ] Boolean values are true/false, not strings
- [ ] Null values are null, not "null"
