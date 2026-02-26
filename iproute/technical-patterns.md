

### 2. Argument Parsing
- [ ] New code uses `strcmp()`, not `matches()` for argument comparison
- [ ] Proper use of `NEXT_ARG()`, `NEXT_ARG_OK()`, `PREV_ARG()`
- [ ] Error helpers used correctly: `invarg()`, `duparg()`, `missarg()`

### 3. JSON Output
- [ ] All output uses `print_XXX()` helpers, not raw `fprintf(fp, ...)`
- [ ] Error messages go to stderr, not stdout
- [ ] `open_json_object()` / `close_json_object()` properly paired
- [ ] `open_json_array()` / `close_json_array()` properly paired
- [ ] Uses `PRINT_ANY` where possible, not separate JSON/text paths
- [ ] Rates/times use proper helpers for human-readable vs raw JSON values

### 4. Memory Safety
- [ ] All allocations checked for NULL
- [ ] No buffer overflows
- [ ] Memory freed on all error paths
- [ ] Use goto for centralized cleanup when appropriate

### 5. Netlink Handling
- [ ] Proper request structure initialization with designated initializers
- [ ] Correct use of `addattr_l()`, `addattr32()`, `addattr_nest()`
- [ ] Nested attributes properly closed with `addattr_nest_end()`
- [ ] Error return values checked

### 6. Kernel Compatibility
- [ ] uapi header updates in separate patch from functionality
- [ ] uapi changes reference upstream kernel commit
- [ ] Code handles older kernels gracefully
- [ ] Runtime feature detection where appropriate
- [ ] no #ifdef KERNEL_VERSION

