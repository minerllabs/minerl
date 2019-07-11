import os
import shutil
import tqdm
import glob

J = os.path.join
E = os.path.exists
def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


WORKING_DIR = os.path.abspath('./output')
MERGED_DIR = J(WORKING_DIR, 'merged_new')
DOWNLOADED_DIR = J(WORKING_DIR, 'downloaded_new')

BLACKLIST_TXT = J(WORKING_DIR, 'blacklist.txt')

if not E(BLACKLIST_TXT):
    touch(BLACKLIST_TXT)
    blacklist = []
else:
    with open(BLACKLIST_TXT, 'r') as f:
        blacklist = f.readlines()

def get_files_to_merge():

    files_to_merge = []
    downloaded_streams = glob.glob(J(DOWNLOADED_DIR, "player*"))
    for f in downloaded_streams:
        try:
            assert os.path.isfile(f), "{} was not a file. Your download dir could be wrong."
            name = os.path.basename(f)
            delimited_name = name.split("-")
            who, version = delimited_name[0], delimited_name[1]
            stream_name = "{}-{}".format(who, version)
            if not (
                E(J(MERGED_DIR, "{}.mcpr".format(stream_name))) 
                and not stream_name in blacklist):
                files_to_merge.append(stream_name)

        except AssertionError as e:
            print(e)

    return list(set(files_to_merge))

print(get_files_to_merge())