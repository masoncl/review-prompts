# NFSD-012: Stateid and delegation/lock state

**Risk**: State confusion, unauthorized access, resource leak

## Check

- Stateid generation properly incremented to prevent reuse
- Stateid seqid updates follow RFC 8881 section 9.1.4
- Delegation state changes hold appropriate locks
- Lock state transitions maintain consistency
- Proper handling of stateid revocation
- State cleanup releases all associated resources

## Review focus

- Verify stateid generation avoids collisions and reuse
- Check delegation callbacks are properly sequenced
- Ensure lock state changes are atomic where required
- Validate proper use of state_lock and client_lock
- Review revocation handling doesn't leave stale state
- Check for memory leaks in state destruction paths

## Example vulnerability

Stateid reuse allowing unauthorized file access or
delegation recall race causing file corruption
