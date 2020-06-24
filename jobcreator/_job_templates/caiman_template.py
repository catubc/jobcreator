import os


def caiman_job_file(
    data_path: str,
    job_name: str,
    email: str,
    ops_path: str = None,
    db_path: str = None,
    n_cpu: int = 8,
    mem_per_cpu: int = 25,
    tmp_size: int = 50,
    job_time: str = "01:00:00",
    qos: str = "6hours",
    log_file: str = "myrun.o",
    error_file: str = "myrun.e",
):
    mem_per_cpu = str(mem_per_cpu) + "G"
    tmp_size = str(tmp_size) + "G"

    # get the name of the file and make the path to the temp dir
    file_name = os.path.basename(data_path)
    temp_data_path = os.path.join("$TMPDIR", file_name)

    if ops_path is None:
        ops_path = "[]"

    if db_path is None:
        db_path = "[]"

    job_file = f"""#!/bin/bash

#SBATCH --job-name={job_name}                   #This is the name of your job
#SBATCH --cpus-per-task={n_cpu}                  #This is the number of cores reserved
#SBATCH --mem-per-cpu={mem_per_cpu}              #This is the memory reserved per core.
#SBATCH --tmp={tmp_size}

#SBATCH --time={job_time}        #This is the time that your task will run
#SBATCH --qos={qos}           #You will run in this queue

# Paths to STDOUT or STDERR files should be absolute or relative to current working directory
#SBATCH --output={log_file}%j     #These are the STDOUT and STDERR files
#SBATCH --error={error_file}%j
#SBATCH --mail-type=END,FAIL,TIME_LIMIT
#SBATCH --mail-user={email}        #You will be notified via email when your task ends or fails


#Remember:
#The variable $TMPDIR points to the local hard disks in the computing nodes.
#The variable $HOME points to your home directory.
#The variable $SLURM_JOBID stores the ID number of your job.


#load your required modules below
#################################
module purge
module load Anaconda3

#add your command lines below
#############################
mkdir $TMPDIR/fd
cp {data_path} {temp_data_path}
val=$(ls $TMPDIR)
echo $val
echo $TMPDIR

source activate caiman_37
conda env export > job_%j_env.yml
xvfb-run --server-args='-screen 0 1024x768x24' -a python -W ignore caiman_runner
suite2p_runner --tmp $TMPDIR --ops {ops_path} --db {db_path}
"""

    return job_file
