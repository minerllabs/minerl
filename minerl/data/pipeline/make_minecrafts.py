# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton

import os
import shutil
import stat
import urllib.request
import zipfile

from os.path import join as J, exists as E

from minerl.data.util.constants import RENDERERS_DIR as BASE_DIR
from minerl.data.util.constants import NUM_MINECRAFTS

MINECRAFT_TEMPLATE = os.path.abspath(J(os.path.dirname(__file__), '..', 'assets', 'template_minecraft'))
DOTMINECRAFT = os.path.abspath(J(BASE_DIR, '.minecraft'))
LAUNCH_SH_TEMPLATE_PATH = os.path.abspath(J(os.path.dirname(__file__), 'launch.sh.template'))

import io


def download(url, file_name):
    out_file = open(file_name, 'wb+')
    with urllib.request.urlopen(url) as response:
        length = response.getheader('content-length')
        if length:
            length = int(length)
            blocksize = max(4096, length // 100)
        else:
            blocksize = 1000000  # just made something up

        print(length, blocksize)

        size = 0
        while True:
            buf1 = response.read(blocksize)
            out_file.write(buf1)
            if not buf1:
                break
            size += len(buf1)
            if length:
                print('{:.2f}\r done'.format(size / length), end='')
    out_file.close()


def get_minecraft_dir(i) -> str:
    return os.path.abspath(J(BASE_DIR, 'minecraft_{}'.format(i)))


def check_installed(n_minecrafts=NUM_MINECRAFTS):
    if n_minecrafts > NUM_MINECRAFTS:
        raise NotImplementedError(
            f"Cannot use n_minecrafts > {NUM_MINECRAFTS} because "
            "several constants in constants.py depend on NUM_MINECRAFT."
        )
    for i in range(n_minecrafts):
        if not os.path.exists(get_minecraft_dir(i)):
            return False
    return True


def main(n_minecrafts=NUM_MINECRAFTS):
    with open(LAUNCH_SH_TEMPLATE_PATH, "r") as f:
        launch_sh_template = f.read()

    print("Downloading minecraft assets and binaries.")
    cracked_libs = J(BASE_DIR, 'cracked_libs')
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(DOTMINECRAFT):
        mzip = J(BASE_DIR, 'mine.zip')
        if os.path.exists(mzip):
            os.remove(mzip)

        download('https://minerl.s3.amazonaws.com/assets/minecraft.zip', mzip)
        with zipfile.ZipFile(mzip, 'r') as zip_ref:
            zip_ref.extractall(BASE_DIR)

        os.makedirs(J(BASE_DIR, 'cracked_libs'), exist_ok=True)
        libs_zip = J(cracked_libs, 'libs.zip')
        download('https://minerl.s3.amazonaws.com/assets/libs.zip', libs_zip)
        with zipfile.ZipFile(libs_zip, 'r') as zip_ref:
            zip_ref.extractall(cracked_libs)

    for i in range(n_minecrafts):
        target_mc_name = get_minecraft_dir(i)
        if os.path.exists(target_mc_name):
            shutil.rmtree(target_mc_name)
        shutil.copytree(MINECRAFT_TEMPLATE, target_mc_name)
        xauth = os.path.join(target_mc_name, 'xauth')
        launch_sh_content = launch_sh_template.format(
            dotminecraft=DOTMINECRAFT,
            cracked_libs=cracked_libs,
            target_mc_name=target_mc_name,
            index=(i + 20),
            xauth=xauth,
        )
        with open(os.path.join(target_mc_name, 'launch.sh'), 'w') as f:
            f.write(launch_sh_content)

        file = (os.path.join(target_mc_name, 'launch.sh'))
        st = os.stat(file)
        os.chmod(file, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    main()
