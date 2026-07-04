# Ailovanta Code repair loop

This is the first verified auto-repair loop.

## Goal

Ailovanta Code should not only chat about code. It should repair code and learn only from verified repairs.

Flow:

```text
failing tests -> repair prompt -> replacements -> apply patch -> run tests again -> record only if tests pass
```

## API

Endpoint:

```text
POST /code-repair/run
```

Body:

```json
{
  "project_dir": "/path/to/project",
  "test_command": "pytest",
  "replacements": [
    {
      "path": "calc.py",
      "old": "return a - b",
      "new": "return a + b"
    }
  ],
  "project_hint": "Fix the calculator add function."
}
```

If `replacements` is omitted, the endpoint runs the allowed test command and returns a repair prompt. That prompt is intended for Ailovanta-owned-code or another code model to produce replacements.

If `replacements` is provided, the endpoint applies the patch, runs tests again, and records the sample into AutoTruth only when the tests pass.

## Safety boundary

- Only allowlisted test commands are accepted: `pytest`, `python -m pytest`, `npm test`.
- Replacement paths must stay inside `project_dir`.
- Only common source/text suffixes are allowed.
- Successful repairs become training events.

## Why this matters

This is the data engine for Ailovanta-owned-code:

```text
verified bug fix -> training event -> AutoTrain -> stronger code model
```
