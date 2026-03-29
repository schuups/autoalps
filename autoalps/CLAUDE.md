# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is an autonomous LLM-driven research project to iteratively improve a CIFAR-10 image classifier. Code runs on the **clariden** HPC cluster (ALPS) via the **Firecreset MCP server** — there are no GPUs locally and training cannot run locally.

## File roles

| File | Editable | Purpose |
|------|----------|---------|
| `train.py` | **Yes** | Model architecture, optimizer, training loop — the only file you modify |
| `evaluate.py` | No | Evaluation logic, incl. test dataloader |
| `settings.py` | Yes | Configurations. Here you can only adapt the batch size |
| `prepare.py` | No | One-time CIFAR-10 dataset download |
| `train.sbatch` | Yes | SLURM job submission (2 nodes × 4 GPUs, 10 min max) |
| `environment.toml` | Yes | NGC PyTorch container definition for SLURM |

## Remote paths

- Local working directory: `autoalps/` (inside the repo)
- Remote working directory: `/iopsstor/scratch/cscs/stefschu/autoalps`
- Dataset cache: `_cache/` (relative, resolved by `settings.cache_path`)

## Experiment workflow

1. Edit `train.py` with an experimental idea
2. Upload changed files to clariden via Firecreset MCP
3. Submit `train.sbatch` to SLURM — **at most one job in queue at a time**
4. Wait for completion; read the SLURM log file for metrics
5. Record results in `results.tsv` (tab-separated, 6 columns: `datetime_utc`, `common_hash`, `experiment_description`, `accuracy`, `execution_secs`, `status`)
6. Commit changes on the `autoalps` branch — commit after every run, whether success or crash

## Output format expected from training runs

```
---
accuracy:         0.997900
execution_secs:   300.1
```

If these lines are absent from the SLURM log, the job crashed.

## Constraints

- You must ignore everything outside the project folder.
- Only `train.py`, `train.sbatch` and `environment.toml` may be modified (and `pyproject.toml` / `uv.lock` if adding dependencies)
- Do not change the number of nodes/GPUs or the 10-minute time limit in `train.sbatch`
- The first run must always be the baseline (unmodified `train.py`)
- Simplicity criterion: prefer simpler code; a marginal accuracy gain that adds complexity is not worth keeping
- Always assume the files on the remote folder are old and need to be overwritten with the latest versions changed locally.
- After the setup is done, you cannot ask for inputs from the human and must instead loop through the experiments you decide to persue.
- You cannot change the number of epochs.

## Distributed training details

- Uses PyTorch DDP with NCCL backend, 8 total processes (2 nodes × 4 GPUs)
- Environment variables from SLURM: `SLURM_NTASKS`, `SLURM_PROCID`, `SLURM_LOCALID`, `MASTER_ADDR`, `MASTER_PORT`
- Only rank 0 evaluates and prints results
- `settings.py` exports `settings` (with `cache_path`, `epochs` and `batch_size`)
- `evaluate.py` exports `evaluate(net_ddp)`

## Crash handling

- An experiment it supposed to run for about 60 seconds before producing outputs.
- Typo or missing import: fix and re-run
- Fundamentally broken idea: log `crash` as status in `results.tsv`, move on
- After a few failed fix attempts on the same idea, abandon and try something else
