import argparse
import os

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Suite2p parameters")
    parser.add_argument("--ops", default=[], type=str, help="options")
    parser.add_argument("--db", default=[], type=str, help="options")
    parser.add_argument("--tmp", default=[], type=str, help="options")
    parser.add_argument("--file", default=[], type=str, help="options")
    args = parser.parse_args()

    ops_path = args.ops
    db_path = args.db
    tmp_path = args.tmp
    file_name = args.file
    return ops_path, db_path, tmp_path, file_name


def update_paths(ops_path, db_path, tmp_path, file_name):
    if ops_path == []:
        from suite2p import run_s2p

        ops = run_s2p.default_ops()
    else:
        ops = np.load(ops_path, allow_pickle=True).item()

    if db_path == []:
        db = {}
    else:
        db = np.load(db_path, allow_pickle=True).item()

    # Modify the data path to the sciCORE job temp dir
    data_path = tmp_path
    fd_path = os.path.join(tmp_path, "fd/")
    # save_path = os.path.join(tmp_path, "suite2p/")
    print("data: %s \n fd: %s" % (data_path, fd_path))

    ops["batch_size"] = 4000
    ops["input_format"] = "h5"

    db["data_path"] = []
    db["h5py"] = os.path.join(tmp_path, file_name)
    db["h5py_key"] = "MSession_0/MUnit_0/Channel_0"
    # db['fast_disk'] = fd_path
    print(db)

    return ops, db


def main():
    ops_path, db_path, tmp_path, file_name = parse_args()
    ops, db = update_paths(ops_path, db_path, tmp_path, file_name)

    # save the files
    np.save("ops_job.npy", ops)
    np.save("db_tmp_job.npy", db)

    # import suite2p just before it is used so it is not required
    from suite2p import run_s2p

    # run the pipeline
    _ = run_s2p.run_s2p(ops=ops, db=db)
