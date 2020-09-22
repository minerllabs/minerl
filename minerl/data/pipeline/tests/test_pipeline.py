"""
Integration test for data pipeline.
"""
import tempfile
import shutil
import os
import subprocess
import minerl
import zipfile
import numpy as np

from os.path import join as J

import minerl.herobraine.envs
from minerl.data.pipeline.make_minecrafts import download
from minerl.data.pipeline.tests import old_data_pipeline
from minerl.herobraine.hero.test_spaces import assert_equal_recursive
from collections import OrderedDict

TESTS_DATA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests_data'))


def _test_pipeline(copy_test_data_out=True, upload_test_data=''):
    # 0. Download and unzip a sample stream.
    sample_stream = os.path.join(TESTS_DATA, 'sample_stream.zip')
    # TODO get this from AWS one?
    if not os.path.exists(sample_stream):
        download('https://storage.googleapis.com/wguss-rcall/public/sweet_potato_full.zip',
                 sample_stream)

    # 1. Make a temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        new_output_root = os.path.join(tmpdir, 'output')
        rendered_root = os.path.join(new_output_root, 'rendered')
        data_root = os.path.join(new_output_root, 'data')
        _ = [os.makedirs(d, exist_ok=True) for d in [new_output_root, rendered_root, data_root]]

        # Unzip the sample stream to output/rendered/player_stream_sample_stream
        # use zipfile/
        zipfile.ZipFile(sample_stream).extractall(rendered_root)
        sample_stream_root = os.path.join(rendered_root, 'player_stream_colorless_mung_bean_dragon-19')

        # Touch a blacklist
        open(os.path.join(new_output_root, 'blacklist.txt'), 'w').close()

        # Set the environment root.
        os.environ.update(dict(MINERL_OUTPUT_ROOT=tmpdir))

        # Now we run the generate script.
        subprocess.check_call('python3 -m minerl.data.pipeline.generate'.split(' '))

        # Now make the version.
        with open(os.path.join(data_root, minerl.data.VERSION_FILE_NAME), 'w') as f:
            f.write(str(minerl.data.DATA_VERSION))

        # Now we run the publish script.
        subprocess.check_call('python3 -m minerl.data.pipeline.publish'.split(' '))

        # Assert that the resulting files are the same as the reference.
        test_name = 'test_pipeline'
        if copy_test_data_out:
            test_data_out = os.path.join(TESTS_DATA, 'out', test_name)
            os.makedirs(os.path.join(TESTS_DATA, 'out'), exist_ok=True)
            shutil.copytree(tmpdir, test_data_out)
        if upload_test_data:
            # Zip it and upload it.
            with tempfile.TemporaryDirectory as zipdir:
                zip_result_dir = os.path.join(zipdir, '{}_result.zip'.format(test_name))
                shutil.make_archive(zip_result_dir, 'zip', data_root)

                # Upload the result.
                subprocess.check_call('gsutil cp {} {}'.format(zip_result_dir, upload_test_data).split(' '))


def _test_obfuscated_data():
    _test_pipeline()
    # Need to reproduce data.
    sample_data_dir = os.path.join(TESTS_DATA, 'out', 'test_pipeline', 'output', 'data')
    os.environ.update(dict(
        MINERL_DATA_ROOT=sample_data_dir
    ))
    treechop = minerl.data.make('MineRLTreechop-v0')
    treechop_obf = minerl.data.make('MineRLTreechopVectorObf-v0')

    trajname = 'v2_cool_sweet_potato_nymph-13_724-5408'
    assert set(treechop_obf.get_trajectory_names()) == {
        'v2_cool_sweet_potato_nymph-13_724-5408',
        'v2_cool_sweet_potato_nymph-13_5564-6194'  # TODO THIS SHOULDN'T BE HERE
    }
    assert set(treechop.get_trajectory_names()) == {
        'v2_cool_sweet_potato_nymph-13_724-5408'
    }

    # We want to see that the obfuscated data can be unwrapped to yield the original data.
    obf_data = list(treechop_obf.load_data(trajname))
    data = list(treechop.load_data(trajname))

    # Take the data and obfuscate to compare to obf_data
    for i, (s, a, r, sp1, d) in enumerate(data):
        (so, ao, ro, sp1o, do) = obf_data[i]

        assert_equal_recursive(treechop_obf.spec.wrap_observation(s), so)
        assert_equal_recursive(treechop_obf.spec.wrap_observation(sp1), sp1o)

        # and now the dual
        assert_equal_recursive(s, treechop_obf.spec.unwrap_observation(so))
        assert_equal_recursive(sp1, treechop_obf.spec.unwrap_observation(sp1o))

        assert r == ro
        assert d == do


def _test_dataloader_regression():
    sample_data_dir = os.path.join(TESTS_DATA, 'out', 'test_pipeline', 'output', 'data')
    sweet_potato_path = os.path.join(TESTS_DATA, 'sweet_potato.zip')
    old_data_root = J(TESTS_DATA, 'old_data', 'MineRLTreechop-v0')
    if not os.path.exists(old_data_root):
        download('https://storage.googleapis.com/wguss-rcall/public/sweet_potato.zip', sweet_potato_path)
        os.makedirs(old_data_root, exist_ok=True)
        zipfile.ZipFile(sweet_potato_path).extractall(
            old_data_root
        )

    trajname = 'v4_cool_sweet_potato_nymph-13_724-5408'
    old_trajname = 'v1_cool_sweet_potato_nymph-13_724-5408'
    os.environ.update(dict(
        MINERL_DATA_ROOT=sample_data_dir
    ))
    treechop = minerl.data.make('MineRLTreechop-v0')
    assert treechop.get_trajectory_names() == [
        'v4_cool_sweet_potato_nymph-13_724-5408'
    ]

    # Todo: Up the version numbers

    new_data = list(treechop.load_data(trajname, include_metadata=True))
    # Todo make some tests

    treechop_old = old_data_pipeline.DataPipeline(old_data_root,
                                                  'MineRLTreechop-v0', 1, 32, 32)

    old_data = list(treechop_old.load_data(old_trajname, include_metadata=True))

    assert len(old_data) == len(new_data)
    for i in range(len(old_data)):
        ns, na, nr, nsp1, nd, nmeta = new_data[i]
        o_s, oa, o_r, osp1, od, ometa = old_data[i]

        # Assert actions are the same
        assert_equal_recursive(na, oa)

        # plt.imshow(ns['pov'])
        # plt.show()
        # plt.imshow(o_s['pov'])
        # plt.show()

        # Remove 'pov' from ns,nsp1,os,osp1
        del ns['pov']
        del nsp1['pov']
        del o_s['pov']
        del osp1['pov']

        # assert states are the same WITHOUT POV
        assert_equal_recursive(ns, o_s)
        assert_equal_recursive(nsp1, osp1)

        # assert meta is the same
        if 'stream_name' in ometa: del ometa['stream_name']
        if 'stream_name' in nmeta: del nmeta['stream_name']

        # New feature
        if 'true_video_frame_count' in nmeta:
            del nmeta['true_video_frame_count']

        assert_equal_recursive(OrderedDict(ometa), OrderedDict(nmeta))

        # asser the new done (nd) is equal to the old done
        assert np.allclose(nd, od)

        # assert the new reward (nr) is equal to the old reward (o_r)
        assert np.allclose(nr, o_r)

# def _test_ao_on_or_off():
# assert False, "AO has not been fixed."

# if __name__ == "__main__":
#     _test_dataloader_regression()
#     # test_pipeline( copy_test_data_out=True)
