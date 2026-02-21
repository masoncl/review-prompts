# Syscall Subsystem Guide

## ABI Compatibility

- Adding additional arguments to a syscall does not break ABI as long as the
existing arguments are not changed

## Syscall Parameter Trust Boundaries

Syscall parameters come from user-controlled registers or stack slots. Parameters that are only meaningful when a specific flag is set may contain arbitrary garbage when that flag is absent — userspace is not required to zero-fill unused arguments. When syscall args are copied into a kernel struct, each field inherits the trust boundary of its source argument and remains garbage outside the flag gate even though it looks initialized in C. When refactoring moves a check across a flag gate, verify that every variable the check uses is valid in the broader scope.

**REPORT as bugs**: Any validation, arithmetic, or comparison that uses a flag-gated syscall parameter outside the scope of its flag gate.
