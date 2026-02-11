# Tracing Subsystem Details

## Tracepoint Requirements
- No side effects in TP_fast_assign()
- Strings need __string/__assign_str handling
- Conditional tracing with TP_CONDITION
- RCU protection for tracepoint probes

## Performance Considerations
- Tracepoints have near-zero overhead when disabled
- Use TRACE_EVENT_CONDITION for conditional events
- Avoid expensive operations in trace arguments

## String Handling
- Use __string for dynamic strings
- __assign_str copies the string
- Fixed arrays can use __array

## Quick Checks
- No blocking operations in trace context
- Proper string termination for string fields
- Tracepoint names follow subsystem conventions
- Include files properly generated with CREATE_TRACE_POINTS
