# AI workflow

## Tools and context

This revision used Codex to inspect the project, implement the missing dbt layer, and run local checks. It was given the assignment, the existing files and the actual CSV. Official Snowflake and dbt documentation was consulted for platform behaviour.

The earlier README attributed work to Claude. No original Claude transcript was available in this review, so that history is not asserted here. Add earlier tools and interactions only if they reflect your actual experience.

## Actual prompt excerpts

Initial review request:

> I will give you the task and let me know what is missing from my files, what needs fixing, what can be improved, what is yet to handle and etc:

This was followed by the complete assignment.

Implementation request:

> Okay, so please modify the files to how they should be, clean up the comments as they are insane and please give me step by step what should I do next, from how and where to load the data and files in Snowflake to how to build what I am missing

Source clarification:

> I have it saved in the project, should be the same as the original

These are actual prompts from this task, not invented examples. No custom agents, MCP access to a Snowflake account, or prior production deployment is claimed.

## What AI accelerated

- Comparing the supplied files against the submission requirements.
- Writing the dbt configuration, source/model documentation and initial tests.
- Finding and correcting Snowflake-specific SQL problems.
- Producing a reproducible local reference profile and setup guide.

The design choices in the resulting project are explicit: full snapshots, order/array-index line grain, latest observed customer attributes, Monday weeks, revenue-based ranking and tie-aware flags. The candidate still needs to understand and defend these choices.

## Corrections and limits

The earlier README claimed B1/Gadget won all 144 weeks. An independent Python calculation found B1 won 139 weeks, C1 four, and A1 one. For 2024-05-27, revenues are A1=500, B1=450, C1=400. A statement labelled as verified was wrong.

The earlier files also used an incomplete DATEADD call and PostgreSQL-style regex syntax, and described dbt files that were absent. These were corrected rather than preserving a polished but unsupported narrative.

The first dependency choice in this revision was dbt 1.10. Its runtime reported that it was deprecated, so the project moved to the supported 1.11 line before final checks.

The local tests include mocked Snowflake failure paths. They show that the loader does not attempt publication after those simulated failures; they do not prove actual Snowflake COPY or transaction behaviour.

## Validation approach

- Recompute source totals and weekly rankings with Python Decimal, independently of model SQL.
- Test malformed headers/JSON, empty input and incomplete load results.
- Parse the dbt project to validate configuration, references and test definitions.
- Use synthetic ties and a year boundary in a dbt unit test.
- Execute the real load, dbt build and independent SQL checks in the trial before submission.

The live checks are still the candidate's next step. Record their actual outcomes in evidence/VALIDATION.md. Do not describe dbt parse as a successful Snowflake build or claim manual verification that has not happened.
