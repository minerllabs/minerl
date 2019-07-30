import os
import shutil
import minerl

MINERL_ROOT = os.environ.get('MINERL_DATA_ROOT')

if os.path.exists(MINERL_ROOT):
    shutil.rmtree(MINERL_ROOT)

minerl.data.download(minimal=True)
