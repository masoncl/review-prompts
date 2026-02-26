# /iproute-verify - iproute2 Patch Verification

Verify that an iproute2 patch is correct and complete.

## Instructions

1. Load `review-core.md` for the verification checklist
2. Check all items in the checklist
3. Verify the patch compiles cleanly
4. Check for obvious runtime issues
5. Report any problems found

## Verification Checklist

### Code Quality
- [ ] Follows coding style (tabs, line length, braces)
- [ ] No compiler warnings expected
- [ ] Memory properly managed

### Functionality
- [ ] JSON output works correctly
- [ ] Text output works correctly
- [ ] Error cases handled properly
- [ ] Works with expected kernel versions

### Commit Quality
- [ ] Subject line format correct
- [ ] Description adequate
- [ ] Signed-off-by present
- [ ] uapi changes (if any) in separate patch

## Output

Report verification results with:
- PASS/FAIL for each checklist item
- Details on any failures
- Suggestions for fixes if needed
