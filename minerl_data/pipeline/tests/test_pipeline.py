"""
Integration test for data pipeline.
"""
import tempfile
import shutil
import os
import subprocess
import minerl
import zipfile

from minerl_data.pipeline.make_minecrafts import download

TESTS_DATA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests_data'))

def test_pipeline(copy_test_data_out=False, upload_test_data=''):
    # 0. Download and unzip a sample stream.
    sample_stream =  os.path.join(TESTS_DATA, 'sample_stream.zip')
    if not os.path.exists(sample_stream):
        download('https://minerl.s3.amazonaws.com/assets/sample_stream.zip', 
            os.path.join(TESTS_DATA, 'sample_stream.zip'))

    # 1. Make a temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        new_output_root = os.path.join(tmpdir, 'output')
        rendered_root = os.path.join(new_output_root, 'rendered')
        data_root = os.path.join(new_output_root, 'data')

        # Unzip the sample stream to output/rendered/player_stream_sample_stream
        # use zipfile/
        zipfile.ZipFile(sample_stream).extractall(rendered_root)
        sample_stream_root = os.path.join(rendered_root, 'player_stream_colorless_mung_bean_dragon-19')

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

            
def test_dataloader():
    os.path.join(TESTS_DATA, 


if __name__ == '__main__':
    test_pipeline(copy_test_data_out=True)