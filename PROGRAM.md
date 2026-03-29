# Autoalps

This is an experiment to have a LLM do research to improve a classifier for the CIFAR10 dataset. The present computer does not have GPUs, so the code cannot be executed locally. Training execution must happen on the clariden system, through the firecreset MCP server.

## Setup

To set up a new experiment, work with the user to:

1. **Retrieve files**: Checkout the `autoalps` branch.
2. **Set the working context**: Locally, the working directory is `autoalps` (it is part of the branch just checked out). On the clariden system the working directory is `/iopsstor/scratch/cscs/stefschu/autoalps`.
3. **Read the in-scope files**: Read these files for your context:
    - `prepare.py` - One time logic such as dataset preparation. Do not modify.
    - `commons.py` - Logic about results evaluation. Do not modify.
    - `train.py` - The file you modify. Model architecture, optimizer, training loop. This outputs the achieved accuary scope, and the training runtime in seconds.
    - `environment.toml` - The Environment Definition File for the SLURM execution.
    - `train.sbatch` - The SLURM script to be submitted to execute train.py.
4. **Verify dataset exists**: On the clariden system, check that the CIFAR10 dataset is already cached under the `_cache` folder. If not, tell the human to run `uv run prepare.py`.
5. **Verify uv environment**: On the clariden system, check that the uv virtual environment already exists. This is stored under `.venv`.
5. **Initialize results.tsv**: If not existing, create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment must run on 2 Alps nodes (4 GPUs each), as already set in the training script `train.sbatch`. Do not change the number of GPUs involved, nor the max runtime of 10 minutes. You run the training by uploading the newly edited files to the clariden system and by submitting the `train.sbatch` script to SLURM. 

**What you CAN do:**
- Modify `train.py` — this is the only file you edit. Everything is fair game: model architecture, optimizer, hyperparameters, training loop, batch size, model size, etc.
- Adapt the virtual environement dependencies as needed.

**What you CANNOT do:**
- You cannot modify `prepare.py` and `commons.py`. They are read-only.

**The goal is simple: improve the classification accurary.** Everything is fair game: change the architecture, the optimizer, the hyperparameters, the batch size, the model size. The only constraint is that the code runs without crashing and finishes within the time budget.

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the improvement magnitude. A 0.01 accuracy improvement that adds 20 lines of hacky code? Probably not worth it. A 0.001 accuracy improvement from deleting code? Definitely keep. An improvement of ~0 but much simpler code? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the training script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
accuracy:         0.997900
execution_secs:   300.1
```

You can extract these key metrics from the slurm job log file.

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 5 columns:

```
common_hash experiment_description  accuracy    execution_secs
```

## The experiment loop

The experiments run on the `autoalps` branch. Improvements must be committed.


LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Tune `train.py` with an experimental idea by directly hacking the code.
3. Run the experiment on SLURM, and wait for its completion to read the SLURM job output. Do not ever submit a new job if I already have something running in the queue. This means I want to have at most one job running at a time.
4. Once the job has completed, read the log file to obtain the metrics of interest.
5. If the metics are not present, it means it crashed. Try to fix it. If you can't get things to work after more than a few attempts, give up.
6. If the run was successful, record the results in the tsv.
7. You commit the results after every test.

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Crashes**: If a run crashes (OOM, or a bug, or etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read papers referenced in the code, re-read the in-scope files for new angles, try combining previous near-misses, try more radical architectural changes. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you up to 10 minutes then you can run approx 6/hour, for a total of about 50 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!