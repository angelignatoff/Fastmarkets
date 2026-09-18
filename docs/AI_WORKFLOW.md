# AI workflow

## Tools and context

I used Codex for repository review, Python and SQL generation, test development and troubleshooting. The context included the assignment, existing project files and the source CSV. Official Snowflake and dbt documentation provided references for platform behaviour.

I ran the setup and pipeline commands locally and in Snowflake, then brought connection, configuration and permission errors back into the conversation to resolve them. This included key registration, a dbt version mismatch and reviewer-role access checks.

## Actual prompt excerpts

Initial review request:

> I will give you the task and let me know what is missing from my files, what needs fixing, what can be improved, what is yet to handle and etc:

This was followed by the complete assignment.

Implementation request:

> Okay, so please modify the files to how they should be, clean up the comments as they are insane and please give me step by step what should I do next, from how and where to load the data and files in Snowflake to how to build what I am missing

Source clarification:

> I have it saved in the project, should be the same as the original

The workflow used a direct conversation with project-file access. Snowflake commands were run separately through the local terminal and SQL worksheets.

## What AI accelerated

- Comparing the supplied files against the submission requirements.
- Writing the dbt configuration, source/model documentation and initial tests.
- Finding and correcting Snowflake-specific SQL problems.
- Producing a reproducible local reference profile and setup guide.

The README records the resulting design choices and trade-offs: full snapshots, order/array-index line grain, latest observed customer attributes, Monday weeks, revenue-based ranking and tie-aware flags.

## Corrections and limits

The earlier README claimed B1/Gadget won all 144 weeks. An independent Python calculation found B1 won 139 weeks, C1 four, and A1 one. For 2024-05-27, revenues are A1=500, B1=450, C1=400. A statement labelled as verified was wrong.

The initial files also contained an incomplete DATEADD call and PostgreSQL-style regex syntax. The review identified these issues alongside missing dbt models and tests. The implementation and documentation were updated together.

The first dependency choice in this revision was dbt 1.10. Its runtime reported that it was deprecated, so the project moved to the supported 1.11 line before final checks.

The local tests include mocked Snowflake failure paths. They show that the loader does not attempt publication after those simulated failures; they do not prove actual Snowflake COPY or transaction behaviour.

## Validation approach

- Recompute source totals and weekly rankings with Python Decimal, independently of model SQL.
- Test malformed headers/JSON, empty input and incomplete load results.
- Parse the dbt project to validate configuration, references and test definitions.
- Use synthetic ties and a year boundary in a dbt unit test.
- Execute the real load, dbt build and independent SQL checks in the trial before submission.

Local parsing, mocked failure tests and live warehouse execution provide different kinds of evidence. Their results and any outstanding checks are tracked in evidence/VALIDATION.md. A successful parse alone does not establish that the models execute correctly in Snowflake.
