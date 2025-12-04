# NULL Pointer Dereference Guide

**What's a NULL pointer dereference?**

You often get this wrong.

## Dereference Types

```
- val = *foo dereferences foo
  - if (foo) val = *foo is safe
- val = foo[var] dereferences foo but only reads var without dereference
  - if (foo) val = foo[var] is safe
- val = foo->ptr dereferences foo but only reads ptr without dereference
  - if (foo) val = foo->ptr is safe
- val = *foo->ptr dereferences foo and ptr.
  - if (foo && foo->ptr) val = *foo->ptr is safe
- val = (*foo)->ptr dereferences foo, then dereferences what foo points to, then
         reads ptr without dereference
  - if (foo && *foo) val = (*foo)->ptr is safe
- val = foo->ptr->something dereferences foo and ptr but only reads something
  - if (foo && foo->ptr) val = foo->ptr->something is safe
```

## Key Points

1. **Reading a pointer field is not the same as dereferencing it**
   - `ptr = foo->bar` dereferences `foo`, reads `bar`, but does NOT dereference `bar`
   - The dereference happens when you later USE `ptr`

2. **Check where the pointer is actually used**
   - If `ptr = foo->bar` and `bar` can be NULL, the problem occurs when `ptr` is dereferenced
   - Example: `ptr->field` or `*ptr` or passing `ptr` to a function that dereferences it

3. **NULL checks protect the pointer being checked**
   - `if (foo)` protects dereferencing `foo`
   - `if (foo && foo->bar)` protects dereferencing both `foo` and `foo->bar`
