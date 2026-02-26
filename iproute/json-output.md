# JSON Output Support

**All commands must support JSON output.** Use the helper functions from
`json_print.h` to ensure consistent output in both regular and JSON modes.

## Key Principles

1. **Avoid special-casing JSON** - Let the library handle the differences
2. **Use print_XXX helpers** - Do not use `fprintf(fp, ...)` directly for display output
3. **Error messages to stderr** - Use `fprintf(stderr, ...)` for errors to avoid corrupting JSON
4. **Pair open/close calls** - Every `open_json_object()` needs `close_json_object()`,
   every `open_json_array()` needs `close_json_array()`

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
print_uint(PRINT_JSON, "foo", NULL, bar);
print_uint(PRINT_FP, NULL, "foo %u", bar);
```

The correct pattern uses `PRINT_ANY` with both a JSON key and a format string,
letting the library handle which output mode is active.

## Color Support

Use color variants for these value types to improve readability:

- **Interface names** (e.g., "eth0", "enp0s3")
- **MAC addresses** (e.g., "1a:0e:d4:cd:70:81")
- **IPv4 addresses**
- **IPv6 addresses**
- **Operational state values**

```c
print_color_string(PRINT_ANY, COLOR_IFNAME, "ifname", "%s", ifname);
print_color_string(PRINT_ANY, COLOR_MAC, "address", "%s ", mac_addr);
print_color_string(PRINT_ANY, oper_state_color(state), "operstate", "%s ", state_str);
```

## Output Functions

Use `PRINT_ANY` for output that works in both JSON and text modes:

```c
/* Simple values */
print_string(PRINT_ANY, "name", "%s ", name);
print_uint(PRINT_ANY, "mtu", "mtu %u ", mtu);
print_u64(PRINT_ANY, "bytes", "%llu", bytes);
print_bool(PRINT_ANY, "up", "%s", is_up);
print_on_off(PRINT_ANY, "enabled", "%s ", enabled);
```

## JSON Objects and Arrays

Objects and arrays must be properly paired:

```c
/* Objects - MUST pair open/close */
open_json_object("linkinfo");
print_string(PRINT_ANY, "kind", "    %s ", kind);
close_json_object();  /* Required! */

/* Arrays - MUST pair open/close */
open_json_array(PRINT_ANY, is_json_context() ? "flags" : "<");
print_string(PRINT_ANY, NULL, flags ? "%s," : "%s", "UP");
close_json_array(PRINT_ANY, "> ");  /* Required! */
```

## Conditional Output

For output that must differ between JSON and text modes (use sparingly):

```c
if (is_json_context()) {
	print_uint(PRINT_JSON, "operstate_index", NULL, state);
} else {
	print_0xhex(PRINT_FP, NULL, "state %#llx", state);
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

From `json_print.h`:
- `print_string()`, `print_uint()`, `print_int()`, `print_u64()`, `print_s64()`
- `print_bool()`, `print_on_off()`, `print_null()`
- `print_hex()`, `print_0xhex()`
- `print_float()`, `print_rate()`, `print_tv()` (timeval)
- `print_hu()` (unsigned short), `print_hhu()` (unsigned char)
- `print_luint()` (unsigned long), `print_lluint()` (unsigned long long)
- `print_nl()` - prints newline in non-JSON context only
- Color variants: `print_color_string()`, `print_color_uint()`, etc.

## Non-JSON Output Format

The non-JSON (text) output format should be aligned with the command-line
arguments. The output field names should match or closely correspond to
the argument names users provide:

```
$ ip link show dev eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP
    link/ether 00:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
```

## Human-Readable vs Raw Values

Commands that output rates, times, or byte counts should:

- **Plaintext output**: Use existing helpers to format into human-readable terms
- **JSON output**: Print raw numeric values (for script consumption)

JSON output is intended for scripts and programmatic parsing, so raw values
are more useful than formatted strings.

Example:
```
$ tc qdisc show dev enp7s0
qdisc fq_codel 0: parent :4 limit 10240p flows 1024 quantum 1514 target 5ms

$ tc -j -p qdisc show dev enp7s0
[ {
        "kind": "fq_codel",
        "handle": "0:",
        "parent": ":4",
        "options": {
            "limit": 10240,
            "flows": 1024,
            "quantum": 1514,
            "target": 4999,
            "interval": 99999,
            "memory_limit": 33554432,
            "ecn": true,
            "drop_batch": 64
        }
    } ]
```

Note how `target` shows as `5ms` in plaintext but `4999` (microseconds) in JSON.

Use helpers like `print_rate()` which automatically handle this distinction.
