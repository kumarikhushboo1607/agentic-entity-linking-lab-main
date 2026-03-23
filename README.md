# Entity Linking Lab

Welcome to the entity linking lab! Over the course of a few hours, we hope to demonstrate: 
- what wikidata is, and the basics of the SPARQL query language
- a very simple entity linking pipeline backed by a small Knowledge Base derived from Wikidata 
- patterns for extending our entity linking pipeline with
  - vector-based disambiguation
  - context aware linking using an AI agent 

## Quickstart 


Open the main notebook here:

[`notebooks/01_wikidata_bootstrap_entity_linking.ipynb`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/notebooks/01_wikidata_bootstrap_entity_linking.ipynb)

## What You Will Build

You will build an entity linker backed by Wikidata:

1. Run one SPARQL query against Wikidata.
2. Turn the returned rows into a tiny local knowledge base.
3. Build a surface-form index from that local KB.
4. Annotate text with matching surface forms and Wikidata URIs.

The default domain is:

`living people currently holding a political office in Ireland`

You do not need an LLM or extra Python packages for the baseline.

## Before The Lab

Install these on your laptop before you arrive:

1. `git`
2. `uv`
3. Claude Code, if you want to try the local agentic disambiguator

Check that they work:

```bash
git --version
uv --version
claude --help
```

If `claude --help` does not work, you can still do the baseline and vector parts of the lab.

## Clone The Repo

```bash
git clone <repo-url>
cd agentic-entity-linking-lab
```

## Create A uv Environment

We recommend `uv` for all optional setup in this repo.

Install Python 3.11 and create the environment:

```bash
uv python install 3.11
uv sync --extra notebook
```

That gives you:

1. a Python 3.11 environment for the repo
2. Jupyter for the notebook
3. the local package installed from `src/`

## Start Jupyter

From the repository root, run:

```bash
uv run jupyter notebook
```

or:

```bash
uv run jupyter lab
```

Then open:

[`notebooks/01_wikidata_bootstrap_entity_linking.ipynb`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/notebooks/01_wikidata_bootstrap_entity_linking.ipynb)

## What To Do In The Notebook

Work through the notebook in order.

You should:

1. Print the default SPARQL query.
2. Run it against Wikidata.
3. Inspect the raw rows that come back.
4. Inspect the grouped local KB.
5. Build the surface-form index.
6. Run the baseline string matcher on sample text.
7. Start changing the KB or extending the linker.

## Run The Default Pipeline On A Real Example Document

There is an example document here:

[`data/example_current_irish_office_holders.txt`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/data/example_current_irish_office_holders.txt)

You can annotate it with the default KB like this:

```bash
uv run python scripts/run_default_annotation_pipeline.py \
  --input-file data/example_current_irish_office_holders.txt
```

That command:

1. loads the default `.sparql` query
2. fetches the current default KB from Wikidata
3. builds the surface-form index
4. prints JSON annotations for the input text

The notebook also shows the same pattern directly in Python by reading the example file and passing its contents to `annotate_text(...)`.

## Where To Change The Knowledge Base

If you want to change the local KB, start with the SPARQL query.

The default query file is here:

[`queries/current_living_irish_office_holders.sparql`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/queries/current_living_irish_office_holders.sparql)

This is the main file to edit if you want a different bootstrap KB.

The Python code that loads and executes that query is here:

[`src/wikidata_lab/wikidata.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/wikidata.py)

That is the pattern to copy for your own experiments:

1. Put the SPARQL in a clearly named `.sparql` file.
2. Load the file from Python.
3. Execute it.
4. Build your local KB from the returned rows.

## What The Default Query Means

The default query asks for people who are:

1. Human
2. Irish citizens
3. Politicians
4. Currently holding an office
5. Still alive
6. Holding an office tied to Ireland

The returned rows include:

1. `person`
2. `personLabel`
3. `office`
4. `officeLabel`

The notebook then groups those rows by person and uses `personLabel` as the initial surface form.

## How To Change The Domain

If you want a different KB, edit the query and rerun the notebook.

Examples:

1. Change Irish politicians to Irish musicians
2. Change Ireland to another country
3. Remove the office filter for a broader list
4. Add more properties such as party, birthplace, or aliases
5. Query a completely different kind of entity

The important point is:

`your local KB is just the result of a query plus a little Python`

## What Files You Should Look At

Start with these files:

- [`notebooks/01_wikidata_bootstrap_entity_linking.ipynb`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/notebooks/01_wikidata_bootstrap_entity_linking.ipynb): the main lab notebook
- [`data/example_current_irish_office_holders.txt`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/data/example_current_irish_office_holders.txt): sample text that annotates with the default KB
- [`queries/current_living_irish_office_holders.sparql`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/queries/current_living_irish_office_holders.sparql): default SPARQL bootstrap query
- [`src/wikidata_lab/wikidata.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/wikidata.py): query loading, query execution, KB construction, surface-form index, baseline annotator
- [`src/wikidata_lab/candidate_retrieval.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/candidate_retrieval.py): vector retrieval template
- [`src/wikidata_lab/sentence_transformer_embeddings.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/sentence_transformer_embeddings.py): sentence-transformers embedding provider
- [`src/wikidata_lab/agentic_linking.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/agentic_linking.py): context-driven agentic linker template
- [`src/wikidata_lab/agentic_disambiguator.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/agentic_disambiguator.py): agentic disambiguation helper

## Baseline First

Do the baseline before you add extensions.

The baseline is:

1. Query Wikidata
2. Build a small local KB
3. Build a string-matching spotter/linker
4. Inspect successes and failures

That gives you something simple and working before you add complexity.

## Extension Routes

After the baseline works, pick one direction:

1. Better spotting
2. More surface forms and aliases
3. Better disambiguation rules
4. Vector retrieval for candidate generation
5. Agentic context-aware linking
6. Evaluation

## Vector Retrieval Extension

If you want a vector-based candidate retrieval stage, start here:

[`src/wikidata_lab/candidate_retrieval.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/candidate_retrieval.py)

This file contains:

1. `EntityCandidate`
2. `EmbeddingProvider`
3. `SimpleVectorStoreTemplate`

What you need to do:

1. Plug in an embedding model or API
2. Index the entities from your local KB
3. Retrieve top-k candidates for a mention
4. Compare retrieval results against the baseline string matcher

### Tested sentence-transformers setup

Install the extra dependencies:

```bash
uv sync --extra notebook --extra vectors
```

Download the tested model:

```bash
uv run python scripts/download_sentence_transformer_model.py
```

This downloads:

`sentence-transformers/all-MiniLM-L6-v2`

Run the tested retrieval example:

```bash
uv run python scripts/run_sentence_transformer_candidate_retrieval.py \
  --mention "Simon Harris"
```

That script:

1. loads the default KB from Wikidata
2. loads the sentence-transformers model
3. indexes the KB labels
4. prints top retrieval candidates as JSON

## Agentic Linking Extension

If you want a context-aware agentic linker, start here:

[`src/wikidata_lab/agentic_linking.py`](/Users/christopherhokamp/projects/agentic-entity-linking-lab/src/wikidata_lab/agentic_linking.py)

This file contains:

1. `extract_context_window`
2. `AgenticLinkerTemplate`

What you need to do:

1. Build or retrieve a candidate set first
2. Pass the text, mention span, and candidates into the template
3. Connect `llm_call` to your chosen API or local model
4. Inspect whether context changes the chosen URI

The intended pattern is:

`retrieve candidates first, reason over them second`

### Tested Claude Code SDK setup

This repo includes a local agentic disambiguator that follows the same basic SDK pattern we use in `/Users/christopherhokamp/projects/everything-app/relevant-codebases/agentic-curator`:

1. build a prompt
2. create `ClaudeAgentOptions`
3. run `query(...)`
4. collect the text response

Install the extra dependencies:

```bash
uv sync --extra notebook --extra agentic
```

If Claude Code is installed locally and authenticated, run:

```bash
uv run python scripts/run_agentic_disambiguator.py \
  --mention "Martin" \
  --text "Martin said the government would bring the bill to the Dail next week." \
  --start 0
```

That script:

1. loads the default KB from Wikidata
2. builds a small lexical candidate shortlist
3. sends the mention, context, and candidates to Claude Code via the SDK
4. prints JSON with the chosen URI

If `claude --help` works on your machine, this is the setup path to try first.

## Suggested Student Tasks

If you want a clear first task, do one of these:

1. Change the SPARQL query to a different domain
2. Add aliases manually and rerun the string matcher
3. Add a second query to fetch aliases from Wikidata
4. Improve normalization for accents and punctuation
5. Build a tiny hand-labeled evaluation set
6. Add a vector retriever
7. Add an agentic disambiguation step

## Run The Tests

From the repository root:

Run offline tests:

```bash
uv run python -m unittest discover -s tests -v
```

Run the live Wikidata integration test:

```bash
LIVE_WIKIDATA_TESTS=1 uv run python -m unittest tests.test_live_wikidata -v
```

The live test hits the real Wikidata Query Service and checks that the default query still returns valid rows.

## If Something Fails

If `jupyter` does not run:

1. Make sure Jupyter is installed in the Python environment you are using
2. Try `python3 -m notebook`
3. Ask a lab monitor for help

If the live query fails:

1. Check your internet connection
2. Rerun the cell after a short wait
3. Make sure the Wikidata Query Service is reachable from your network

If imports fail in the notebook:

1. Make sure you opened Jupyter from the repository root
2. Make sure the `src/` directory exists in the repo
3. Restart the kernel and rerun from the top

## Session Flow

The plan for the session is:

1. Short intro
2. Baseline notebook
3. Break into groups and extend the system in whichever direction you want

If you are already set up, grab your group, go straight to the quickstart notebook, then start building!
