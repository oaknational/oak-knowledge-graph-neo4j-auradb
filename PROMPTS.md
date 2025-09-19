# Prompts for Claude

> [!IMPORTANT]  
> There are plenty of placeholders throughout these prompts which need to be filled before use or if you direct Claude to this document you can indicate what those are. For instance, "Follow 'KICKOFF / REFRESH MEMORY' in `PROMPTS.md` - fill the `TASK_NUMBER `placeholder with `2`.

## Conception

The first step is to develop your own set of specifications, requirements and standards for this project. To do this you will converse as a team with Claude and produce 4 structured outputs:

1. **FUNCTIONAL.md** - Complete functional requirements
2. **ARCHITECTURE.md** - Detailed project architecture
3. **CLAUDE.md** - Compact standards and guidelines
4. **TO-DO.md** - Ordered tasks/features to complete the project collaboratively

These are the prompts you can use to do so:

---

### GENERATE SPECS

> [!NOTE]
> Resist the urge of being too ambitious here, remember you are aiming to finish building this and fully understand, be able to explain it by the end of the day.

```markdown
We're going to discuss the specification for a software project. The project details are contained in `BRIEF.md` and workshop details are in `README.md`.

Ask me one question at a time so we can develop thorough, step-by-step specs. Each question should build on my previous answers, and our end goal is to have a detailed specification I can hand off to a developer. This will be built in only a few hours so try and keep the conversation short, apply KISS principles and use logical inference based on previous answers when possible.

We should cover: language (ask this first), frameworks, libraries, package managers, styling choices, data structure options (SQL/NoSQL/Graph) BEFORE data storage, architecture, project structure, components, interfaces, design patterns, error handling, UI features, user experience, coding standards, naming conventions, agreed principles, version control, commit standards, testing and documentation requirements.

Do not wrap up until you have answers from me for each of these topics. There will be three outputs at the end: a functional spec, an architectural spec, and our code standards specification for `CLAUDE.md`, review the template for this file currently in the repo to understand what we must cover.

**Important**: When asking questions about technical choices, present 2-3 specific options with brief explanations rather than leaving it open-ended. This speeds up decision-making. When there are more viable options available, verbalise this and ask if I want to see more options. Only one question at a time, stay within scope, and don't generate anything until requested.
```

### SPEC WRAP-UP

```markdown
Now that we've wrapped up the brainstorming process, compile our findings into three comprehensive, developer-ready specifications:

1. **FUNCTIONAL.md** - Complete functional requirements
2. **ARCHITECTURE.md** - Detailed project architecture
3. **CLAUDE.md** - Compact standards and guidelines

For `CLAUDE.md`, follow the existing template but ensure each section includes specific, actionable directives that we can reference explicitly during development. Be very concise, this should be a compact standards document you will refer to each time you write any code.

Make each specification modular and cross-referenced so developers can quickly find relevant information when prompted to check these files. Do not repeat yourself.
```

### GENERATE TO-DO

```markdown
Review `CLAUDE.md` first to understand our standards. Then review `FUNCTIONAL.md` and `ARCHITECTURE.md` to understand what we're building.

Break the project down into manageable, atomic to-do tasks that:

- Build on each other logically
- Are small enough to complete in one session

Generate `TO-DO.md` with:

1. Clear dependencies between to-do tasks
2. Explicit prerequisites listed

Each to-do task should be numbered sequentially, and include:

- Brief description
- Specific deliverables
- Dependencies (if any)
- Definition of done

**Important**: Order to-do tasks by dependency, ensuring you can work efficiently and logically through them in order.
```

## Implementation

During implementation, there are a number of prompts you can use at the start of each task (KICKOFF / REFRESH MEMORY) or after each task (CONTEXT RESET). Included is also a DEPENDENCY CHECK prompt to be used if anything is unclear, remember to also check in with your teammate regularly to iron out anything that is unclear or overlapping.

### KICKOFF / REFRESH MEMORY

> [!IMPORTANT]  
> This prompt contains the placeholders `TASK_NUMBER` to be filled in. At the end of the below text, you should add your instructions to the LLM to complete the prompt (this can often be taken from the task you are working on). Remove the sentence asking to check `HISTORY.md` on first task as this will be the first code interaction.

> [!NOTE]
> Always clear context window before using this prompt.

```markdown
**First, review `CLAUDE.md` to understand our project standards and workflow.**

Then refresh your memory by checking `HISTORY.md`. Review the `ARCHITECTURE.md` and `FUNCTIONAL.md` to understand what we are building.

We are working through `TO-DO.md` and are on task 16.

**Before implementing anything:**

1. Confirm you understand the current task requirements
2. Ask if you should reference any specific standards from `CLAUDE.md`
3. Only implement what's specified in this task

As you implement, explain:

- How the code works and why it meets our `FUNCTIONAL.md` requirements
- How it aligns with our `ARCHITECTURE.md`
- Why it complies with our standards in `CLAUDE.md`

Now, here is the next task to complete:

Before we start Task 16, i want to properly test the application we have developed with real connections to my Hasura API and my Neo4j database. Lets call this Task 15A.
I want to step through the testing of the pipeline one stage at a time:
1. start with testing the extraction of data from the Hasura API. Show me where to enter the name of the MV(s) to test. Show me where to limit the number of records retreieved for each MV. Show me where the MV fields are specified. Show me where I can see the data exported from the MVs. Show me where these results are displayed (CLI and web UI). Then I want to be able to filter the data from the MV import by subject and year.
2. I will then want to use a schema that is VERY simple for testing. (:Subject)-[:HAS_UNIT]->(:Unit). Show me where to set this up. Show me where and how I 'MAP' the MV data fields extracted to the Neo4j schema (via the UI?).
3. Show me how to execute the import using the MV data I've exported and the schema mapping I've entered?
4. Tell me if there is any functionality lacking, or if there is any functionality that I haven't tested here.

IMPORTANT: I need to be able to validate the data being passed through the pipeline at every stage during the testing.

Please replay your understanding of my requirement to me before you start to execute this additional testing stage.

```

### DEPENDENCY CHECK

> [!IMPORTANT]  
> This prompt contains variable `TASK_NUMBER` to be filled in.

> [!NOTE]
> Use this prompt if task dependencies or scope is unclear or overlapping.

```markdown
Before starting this task [`TASK_NUMBER`], check `TO-DO.md` for dependencies. Then:

1. Verify all prerequisite tasks are complete
2. Confirm our implementation aligns with dependent tasks
3. Check if any shared interfaces or data structures need coordination with your teammate
4. Flag any potential conflicts with work in progress

Only proceed when dependencies are satisfied and coordination is clear.
```

### CONTEXT RESET

> [!NOTE]
> You should use this prompt after each task.

```markdown
Now we will reset the context window, before we do so:

1. Create/update a `HISTORY.md` file summarising our progress
2. List completed tasks with key implementation details
3. Note any important decisions or patterns established
4. Mention any deviations from original specs and why
5. Save current state of key variables/configurations
6. If applicable, update `CLAUDE.md` with any learned standards picked up from the review process
7. If there have been significant changes, update `FUNCTIONAL.md` or `ARCHITECTURE.md` as required
8. **IMPORTANT**: Be concise, don't repeat yourself, double check and remove duplication/reduce where possible

After creating/updating these files, I'll reset the context window and we'll continue with a fresh session.
```
