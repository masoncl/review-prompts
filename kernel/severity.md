# Linux Kernel Issue Severity Categorization

Categorize issues based on potential impact if the code reaches a production kernel.

## Critical
**Impact**: Catastrophic failure, memory corruption, data loss, or severe security breach.
**Criteria**:
- **Memory corruption**: Unbounded memory corruption, use-after-free and other memory safety violations.
- **Data Corruption**: Filesystem corruption, silent data loss, or hardware damage.
- **Security**: Remote Code Execution (RCE), direct root privilege escalation, or bypass of core security controls (SELinux/AppArmor).
- **System Crash**: Panic, OOPS, or hard lockup in common code paths.
- **ABI Breakage**: Changes that break existing userspace binaries (uABI violations).

## High
**Impact**: Major service disruption, resource exhaustion, or significant functional regression.
**Criteria**:
- **Availability**: Soft lockups, hangs, or deadlocks under specific loads.
- **Resources**: Potentially rapid memory leaks (OOM), descriptor leaks, or other resource leaks.
- **Functionality**: Complete failure of a specific driver, filesystem, or subsystem feature.
- **Security**: Local privilege escalation requiring specific conditions.

## Medium
**Impact**: Degraded performance, noise, or partial failures. Workarounds usually exist.
**Criteria**:
- **Stability**: Recoverable errors that trigger loud warnings (WARN_ON) and spam logs.
- **Performance**: Measurable regressions (>1%) or latency spikes.
- **Logic**: Edge-case failures in error handling or initialization.

## Minor
**Impact**: Cosmetic, process-oriented, or negligible runtime effect.
**Criteria**:
- **Style**: Coding style violations, indentation, or typo fixes in comments.
- **Process**: Updates to MAINTAINERS file, .gitignore, or internal docs.
- **Dead Code**: Removal of unused variables/functions (unless hiding a logic bug).
- **Refactoring**: Cleanups that strictly preserve existing behavior.

## Context Nuances
- **Documentation**: Usually Minor, but **Critical** if it instructs users to configure the system dangerously.
- **Self-Tests**: Breaking kselftests is **Medium/Minor** depending on the test's importance.
- **Commit log**: Usually Minor, but **/High/Medium** if misses description of important changes or misses Fixes: tag.
