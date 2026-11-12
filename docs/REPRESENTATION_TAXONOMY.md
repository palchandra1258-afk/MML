# Representation Taxonomy v1

`src/mcp_ri/representation/representation_taxonomy.py` exposes taxonomy version `1.0` and these machine-readable categories:

| ID | Examples | Configuration when a provider is available |
|---|---|---|
| `textual` | Simplified explanation, definition, alternative wording, summary | Explanation complexity and content references |
| `worked_example` | Step-by-step solution, solved problem, example plus similar practice | Example count, difficulty and content references |
| `visual` | Concept diagram, flow diagram, graph, annotated illustration, comparison | Visual detail and content references |
| `symbolic` | Equation, formula decomposition, symbol manipulation, algebraic steps | Explanation complexity and content references |
| `interactive` | Interactive graph, parameter adjustment, manipulation, exploration | Provider-defined interaction type and content references |
| `simulation` | Parameter simulation, dynamic visualization, what-if exploration | Provider-defined interaction type and content references |
| `diagnostic` | Diagnostic question, conceptual assessment, reasoning prompt, intermediate step | Difficulty and item reference |
| `alternative_explanation` | Continue current explanation, simpler language, different strategy or example | Explanation complexity and example count |

These names categorize potential downstream content. They do not assert that all forms exist in this repository or are appropriate for a particular learner. The availability registry controls whether a category can be selected for delivery.
