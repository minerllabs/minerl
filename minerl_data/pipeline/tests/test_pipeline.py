"""
Integration test for data pipeline.
"""
import tempfile
import shutil
import os
import subprocess
import minerl
import zipfile

from os.path import join as J

from minerl_data.pipeline.make_minecrafts import download
from minerl_data.pipeline.tests import old_data_pipeline
from herobraine.hero.test_spaces import assert_equal_recursive

TESTS_DATA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests_data'))

def _test_pipeline(copy_test_data_out=False, upload_test_data=''):
    # 0. Download and unzip a sample stream.
    sample_stream =  os.path.join(TESTS_DATA, 'sample_stream.zip')
    if not os.path.exists(sample_stream):
        download('https://storage.googleapis.com/wguss-rcall/public/sweet_potato_full.zip', 
           sample_stream)

    # 1. Make a temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        new_output_root = os.path.join(tmpdir, 'output')
        rendered_root = os.path.join(new_output_root, 'rendered')
        data_root = os.path.join(new_output_root, 'data')

        # Unzip the sample stream to output/rendered/player_stream_sample_stream
        # use zipfile/
        zipfile.ZipFile(sample_stream).extractall(rendered_root)
        sample_stream_root = os.path.join(rendered_root, 'player_stream_ccool_sweet_potato_nymph-13')

        # Tocuh a blacklist
        open(os.path.join(new_output_root, 'blacklist.txt'), 'w').close()

        # Set the environment root.
        os.environ.update(dict(MINERL_OUTPUT_ROOT=tmpdir))


        # Now we run the generate script.
        subprocess.check_call('python3 -m minerl_data.pipeline.generate'.split(' '))
        
        # Now make the version.
        with open(os.path.join(data_root, minerl.data.VERSION_FILE_NAME), 'w') as f:
            f.write(str(minerl.data.DATA_VERSION))

        # Now we run the publish script.
        subprocess.check_call('python3 -m minerl_data.pipeline.publish'.split(' '))

        # Assert that the resulting files are the same as the reference.
        test_name = 'test_pipeline'
        if copy_test_data_out:
            test_data_out = os.path.join(TESTS_DATA, 'out', test_name)
            os.makedirs(os.path.join(TESTS_DATA, 'out'))
            shutil.copytree(tmpdir, test_data_out)
        if upload_test_data:
            # Zip it and upload it.
            with tempfile.TemporaryDirectory as zipdir:
                zip_result_dir = os.path.join(zipdir, f'{test_name}_result.zip')
                shutil.make_archive(zip_result_dir, 'zip', data_root) 

                # Upload the result.
                subprocess.check_call(f'gsutil cp {zip_result_dir} {upload_test_data}'.split(' '))

            
def test_dataloader_regression():
    sample_data_dir = os.path.join(TESTS_DATA, 'out', 'test_pipeline', 'output', 'data')
    sweet_potato_path = os.path.join(TESTS_DATA, 'sweet_potato.zip')
    old_data_root = J(TESTS_DATA, 'old_data', 'MineRLTreechop-v0')
    if not os.path.exists(old_data_root):
        download('https://storage.googleapis.com/wguss-rcall/public/sweet_potato.zip', sweet_potato_path)
        os.makedirs(old_data_root, exist_ok=True)
        zipfile.ZipFile(sweet_potato_path).extractall(
            old_data_root
        )
    
    trajname=  'v2_cool_sweet_potato_nymph-13_724-5408'
    old_trajname = 'v1_cool_sweet_potato_nymph-13_724-5408'
    os.environ.update(dict(
        MINERL_DATA_ROOT=sample_data_dir
    ))
    treechop = minerl.data.make('MineRLTreechop-v0')
    treechop_obf = minerl.data.make('MineRLTreechopVectorObf-v0')
    assert treechop_obf.get_trajectory_names() == [
        'v2_cool_sweet_potato_nymph-13_5564-6194',  # TODO THIS SHOULDN'T BE HERE
        'v2_cool_sweet_potato_nymph-13_724-5408'
    ] 
    assert treechop.get_trajectory_names() == [
        'v2_cool_sweet_potato_nymph-13_724-5408'
    ]

    # Todo: Up the version numbers

    # import matplotlib
    # matplotlib.use('MACOSX')
    new_data = list(treechop.load_data(trajname, include_metadata=True))
    # Todo make some tests

    treechop_old = old_data_pipeline.DataPipeline(old_data_root,
        'MineRLTreechop-v0', 1, 32,32)

    old_data = list(treechop_old.load_data(old_trajname, include_metadata=True))

    for i, x in enumerate(old_data):
        # print("new frame")
        # import matplotlib.pyplot as plt
        # print("new data")
        # plt.imshow(new_data[i][0]['pov'])
        # # New data is smooth
        # # Old data is not
        # plt.show()
        # print("old data")
        # plt.imshow(old_data[i][0]['pov'])
        # plt.show()
        # for j, y in enumerate(x): 
        # TODO: Rerender data, AO if off
        assert_equal_recursive(x[1], new_data[i][1])



def test_ao_on_or_off():
    assert False, "AO has not been fixed."

    



if __name__ == '__main__':
    # test_pipeline(copy_test_data_out=True)
    test_dataloader_regression()