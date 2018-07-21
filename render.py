"""
render.py  
# This script renders the merged experiments into 
# actions and videos by doing the following
# 1) Unzipping various mcprs and building render directories 
#    containing meta data.
# 2) Running the action_rendering scripts
# 3) Running the video_rendering scripts
"""
import os
import numpy as np
import tqdm
import zipfile

######################3
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
WORKING_DIR = "output"
MERGED_DIR = J(WORKING_DIR, "merged")
RENDER_DIR = J(WORKING_DIR, "rendered")
BLACKLIST_PATH =J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
END_OF_STREAM_TEXT = 'This is the end.'
BAD_MARKER_NAME = 'INVALID'

METADATA_FILES = [
	'metaData.json',
	'markers.json',
	'mods.json',
	'stream_meta_data.json']

def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def get_recording_archive(recording_name):
	"""
	Gets the zipfile object of a mcpr recording.
	"""
	mcpr_path = J(MERGED_DIR, (recording_name + ".mcpr"))
	assert E(mcpr_path)

	return zipfile.ZipFile(mcpr_path)

##################
### PIPELINE
#################

# 1. Construct render working dirs.
def construct_render_dirs(blacklist):
	"""
	Constructs the render directories omitting
	elements on a blacklist.
	"""
	if not E(RENDER_DIR):
		os.makedirs(RENDER_DIR)
	# We only care about unrendered directories.
	render_dirs = []

	for filename in tqdm.tqdm(os.listdir(MERGED_DIR)):
		if filename.endswith(".mcpr") and filename not in blacklist:
			recording_name = filename.split(".mcpr")[0]
			render_path = J(MERGED_DIR, filename)

			if not E(render_path):
				os.makedirs(render_path)

			render_dirs.append((filename, render_path))

	return render_dirs


def render_metadata(renders: list) -> list:
	"""
	Unpacks the metadata of a recording and checks its validity.
	"""
	good_renders = []
	bad_renders = []

	for recording_name, render_path in tqdm.tqdm(renders):
		if E(render_path):
			# Check if metadata has already been extracted.
			if E(J(render_path, END_OF_STREAM)):
				good_renders.append((recording_name, render_path))
			else:
				try: 
					recording = get_recording_archive(recording_name)
					extract = lamda fname: recording.extract(fname, J(render_path, fname))

					# Test end of stream validity.
					with open(extract(END_OF_STREAM), 'r') as eos:
						assert END_OF_STREAM_TEXT not in eos.read()
					
					# If everything is good extract the metadata.
					for mfile in METADATA_FILES:
						assert mfile in recording.namelist()
						extract(mfile)

					good_renders.append((recording_name, render_path))
				except AssertionError:
					# Mark that this is a bad file.
					touch(J(render_path, BAD_MARKER_NAME))
					bad_renders.append((recording_name, render_path))

	return good_renders, bad_renders


def render_actions(renders: list):
	"""
	For every render directory, we render the actions
	"""

	return

def render_videos(renders: list):
	"""
	For every render directory, we render the videos.
	"""

def main():
	"""
	The main render script.
	"""
	# 1. Load the blacklist.
	blacklist = set(np.loadtxt(BLACKLIST_PATH, dtype=np.str).tolist())

	renders = construct_render_dirs(blacklist)
	valid_renders, invalid_renders = render_metadata(render)
	render_actions(renders)
	render_videos(renders)




	from IPython import embed; embed()

if __name__ == "__main__":
	main()