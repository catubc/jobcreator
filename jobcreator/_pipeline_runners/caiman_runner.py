#!/usr/bin/env python
import argparse
import glob
import os
from time import sleep

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser(description="Suite2p parameters")
    parser.add_argument("--file", default=[], type=str, help="options")
    parser.add_argument("--ncpus", default=1, type=int, help="options")
    args = parser.parse_args()

    file_path = args.file
    n_cpus = args.ncpus

    return file_path, n_cpus


def run(file_path, n_cpus):

    import caiman as cm
    from caiman.motion_correction import MotionCorrect
    from caiman.source_extraction.cnmf import params as params
    from caiman.source_extraction import cnmf

    # dataset dependent parameters
    frate = 20  # movie frame rate
    decay_time = 0.4  # length of a typical transient in seconds

    # motion correction parameters
    # flag for performing motion correction
    # motion_correct = True

    # flag for performing piecewise-rigid motion correction
    # (otherwise just rigid)
    pw_rigid = False

    # size of high pass spatial filtering, used in 1p data
    gSig_filt = (3, 3)

    # maximum allowed rigid shift
    max_shifts = (5, 5)
    strides = (
        48,
        48,
    )
    # start a new patch for pw-rigid motion correction every x pixels
    overlaps = (24, 24)

    # overlap between pathes (size of patch strides+overlaps)
    max_deviation_rigid = (
        3  # maximum deviation allowed for patch with respect to rigid shifts
    )
    border_nan = "copy"  # replicate values along the boundaries

    # fnames
    file_pattern = os.path.join(file_path, "*.tif")
    fnames = glob.glob(file_pattern)
    print(fnames)

    mc_dict = {
        "fnames": fnames,
        "fr": frate,
        "decay_time": decay_time,
        "pw_rigid": pw_rigid,
        "max_shifts": max_shifts,
        "gSig_filt": gSig_filt,
        "strides": strides,
        "overlaps": overlaps,
        "max_deviation_rigid": max_deviation_rigid,
        "border_nan": border_nan,
    }
    opts = params.CNMFParams(params_dict=mc_dict)

    print("starting server")
    # start the server

    # n_processes = n_cpus - 1
    c, dview, n_processes = cm.cluster.setup_cluster(
        backend="local", n_processes=None, single_thread=False
    )
    print(n_processes)
    sleep(30)

    print("motion corr")
    mc = MotionCorrect(fnames, dview=dview, **opts.get_group("motion"))
    mc.motion_correct(save_movie=True)
    fname_mc = mc.fname_tot_els if pw_rigid else mc.fname_tot_rig
    if pw_rigid:
        bord_px = np.ceil(
            np.maximum(
                np.max(np.abs(mc.x_shifts_els)), np.max(np.abs(mc.y_shifts_els))
            ).astype(np.int)
        )

    print("writing mmap")
    bord_px = 0
    fname_new = cm.save_memmap(
        fname_mc, base_name="memmap_", order="C", border_to_0=bord_px
    )

    # load mmap
    print("loading mmap")

    # load memory mappable file
    Yr, dims, T = cm.load_memmap(fname_new)
    images = Yr.T.reshape((T,) + dims, order="F")

    # parameters for source extraction and deconvolution
    p = 1  # order of the autoregressive system

    # upper bound on number of components per patch, in general None
    K = None

    # gaussian width of a 2D gaussian kernel, which approximates a neuron
    gSig = (3, 3)
    gSiz = (13, 13)  # average diameter of a neuron, in general 4*gSig+1
    Ain = None  # possibility to seed with predetermined binary masks
    merge_thr = 0.7  # merging threshold, max correlation allowed

    # half-size of the patches in pixels. e.g., if rf=40, patches are 80x80
    rf = 40
    # amount of overlap between the patches in pixels
    # (keep it at least large as gSiz, i.e 4 times the neuron size gSig)
    stride_cnmf = 20

    tsub = 2  # downsampling factor in time for initialization,
    #                     increase if you have memory problems
    ssub = 1  # downsampling factor in space for initialization,
    #                     increase if you have memory problems
    #                     you can pass them here as boolean vectors
    low_rank_background = None  # None leaves background of each patch intact,
    #                     True performs global low-rank approximation if gnb>0
    gnb = 0  # number of background components (rank) if positive,
    #                     else exact ring model with following settings
    #                         gnb= 0: Return background as b and W
    #                         gnb=-1: Return full rank background B
    #                         gnb<-1: Don't return background
    nb_patch = 0  # number of background components (rank) per patch if gnb>0,
    #                     else it is set automatically
    min_corr = 0.8  # min peak value from correlation image
    min_pnr = 10  # min peak to noise ration from PNR image
    ssub_B = 2  # additional downsampling factor in space for background
    ring_size_factor = 1.4  # radius of ring is gSiz*ring_size_factor

    opts.change_params(
        params_dict={
            "method_init": "corr_pnr",  # use this for 1 photon
            "K": K,
            "gSig": gSig,
            "gSiz": gSiz,
            "merge_thr": merge_thr,
            "p": p,
            "tsub": tsub,
            "ssub": ssub,
            "rf": rf,
            "stride": stride_cnmf,
            "only_init": True,  # set it to True to run CNMF-E
            "nb": gnb,
            "nb_patch": nb_patch,
            "method_deconvolution": "oasis",  # could use 'cvxpy' alternatively
            "low_rank_background": low_rank_background,
            "update_background_components": True,
            # sometimes setting to False improve the results
            "min_corr": min_corr,
            "min_pnr": min_pnr,
            "normalize_init": False,  # just leave as is
            "center_psf": True,  # leave as is for 1 photon
            "ssub_B": ssub_B,
            "ring_size_factor": ring_size_factor,
            "del_duplicates": True,
            "border_pix": bord_px,
        }
    )  # number of pixels to not consider in the borders)

    cnm = cnmf.CNMF(n_processes=n_processes, dview=dview, Ain=Ain, params=opts)
    cnm.fit(images)

    print("evaluate components")
    min_SNR = 2.5  # adaptive way to set threshold on the transient size
    # threshold on space consistency (if you lower more components
    # will be accepted, potentially with worst quality)
    r_values_min = 0.85

    cnm.params.set(
        "quality", {"min_SNR": min_SNR, "rval_thr": r_values_min, "use_cnn": False}
    )
    cnm.estimates.evaluate_components(images, cnm.params, dview=dview)

    cnm.save(cnm.mmap_file[:-4] + "hdf5")

    print("stopping server")
    cm.stop_server(dview=dview)


def main():
    file_path, n_cpus = parse_args()

    # run the pipeline
    run(file_path=file_path, n_cpus=n_cpus)
