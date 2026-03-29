#!/bin/bash
#SBATCH --job-name=autoalps
#SBATCH --time=00:10:00
#SBATCH --account=csstaff
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4

export MASTER_ADDR=$(scontrol show hostname $SLURM_NODELIST | head -n1)
export MASTER_PORT=29500


srun --mpi=pmix --network=disable_rdzv_get --environment=$(pwd)/environment.toml --nodes=1 --ntasks=1 bash -c "source .venv/bin/activate && python prepare.py"

srun --mpi=pmix --network=disable_rdzv_get --environment=$(pwd)/environment.toml bash -c "source .venv/bin/activate && python train.py"
