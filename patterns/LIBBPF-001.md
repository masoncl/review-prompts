# LIBBPF-001: Error return errno handling in public APIs

**Risk**: Public libbpf API functions returning errors without setting errno, breaking userspace error handling conventions

**When to check**: Mandatory for all error return paths in public libbpf API functions (declared in libbpf.h or bpf.h)

Place each step defined below into TodoWrite.

**Mandatory error return validation:**
- step 1: Place into TodoWrite all public API functions that are new or modified in this patch
  - Public APIs are functions declared in tools/lib/bpf/libbpf.h or tools/lib/bpf/bpf.h
  - Look for functions with LIBBPF_API macro or listed in libbpf.map
  - Internal/static functions are NOT subject to this pattern
- step 2: for each public API function, identify its return type:
  - Integer returns (int, __s32, etc.) that can return negative error codes
  - Pointer returns (struct bpf_*, void *, etc.) that can return NULL or ERR_PTR()
  - Skip functions that cannot fail (void return, always-success semantics)
- step 3: for each public API function, trace all error return paths and add to TodoWrite:
  - Direct error returns: `return -EINVAL;`, `return -ENOMEM;`, etc.
  - Propagated errors: `return err;` where err is negative
  - NULL returns: `return NULL;` on error paths
  - ERR_PTR returns: `return ERR_PTR(-EINVAL);`
- step 4: for each error return path, verify libbpf_err() wrapper is used:
  - Integer errors: must use `return libbpf_err(-ERRNO);`
  - Pointer errors from error codes: must use `return libbpf_err_ptr(-ERRNO);` (takes int, always returns NULL)
  - Pointer errors from internal ERR_PTR-returning functions: must use `return libbpf_ptr(internal_func());`
  - The wrapper MUST be on the return statement itself, not earlier in the function
- step 5: check error propagation paths:
  - When propagating integer errors from other functions: `return libbpf_err(other_func());`
  - When propagating pointer errors from internal ERR_PTR-returning functions: `return libbpf_ptr(internal_func());`
  - When returning stored error values: `return libbpf_err(err);` or `return libbpf_err_ptr(err);`
  - Verify errno is set on ALL paths that return to userspace

**After analysis:** Issues found: [none OR list]
