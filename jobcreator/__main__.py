#!/usr/bin/python

import argparse
import json
import os
import subprocess

from ._job_templates import suite2p_job_file, caiman_job_file

JOB_FILE_GENERATORS = {"suite2p": suite2p_job_file, "caiman": caiman_job_file}


def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline parameters")
    parser.add_argument("--pipeline", default=[], type=str, help="options")
    parser.add_argument("--settings", default=[], type=str, help="options")
    parser.add_argument("--output", default=".", type=str, help="options")

    args = parser.parse_args()

    pipeline_name = args.pipeline
    settings_path = args.settings
    output_path = args.output

    return pipeline_name, settings_path, output_path


def main():
    pipeline_name, settings_path, output_path = parse_args()

    job_file_path = os.path.join(output_path, "job_file.sh")

    with open(settings_path, "r") as read_file:
        job_settings = json.load(read_file)

    # get the file text
    job_file_gen = JOB_FILE_GENERATORS[pipeline_name]
    job_file_text = job_file_gen(**job_settings)

    # make the file job file
    with open(job_file_path, "w") as text_file:
        text_file.write(job_file_text)

    # run the job
    subprocess.run(["srun", job_file_path])
