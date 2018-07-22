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
import subprocess
import json

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
ACTION_FILE = "actions.tmcpr"
END_OF_STREAM_TEXT = 'This is the end.'
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'

METADATA_FILES = [
	'metaData.json',
	'markers.json',
	'mods.json',
	'stream_meta_data.json']

def touch(path):
    with open(path, 'w'):
        pass

def remove(path):
    if E(path):
    	os.remove(path)

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
			render_path = J(RENDER_DIR, recording_name)

			if not E(render_path):
				os.makedirs(render_path)

			render_dirs.append((recording_name, render_path))

	return render_dirs

# 2. render metadata from the files.
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
				# If it has been computed see if it is valid
				# or not.
				if E(J(render_path, GOOD_MARKER_NAME)):
					good_renders.append((recording_name, render_path))
				else:
					bad_renders.append((recording_name, render_path))
			else:
				try: 
					recording = get_recording_archive(recording_name)
					extract = lambda fname: recording.extract(fname, render_path)

					# Test end of stream validity.
					with open(extract(END_OF_STREAM), 'r') as eos:
						assert len(eos.read()) > 0
					
					# If everything is good extfct the metadata.
					for mfile in METADATA_FILES:
						assert str(mfile) in [str(x) for x in recording.namelist()]
						extract(mfile)

					# check that tream_meta_data is good
					with open(J(render_path, 'stream_meta_data.json'), 'r') as f:
						jbos = json.load(f)
						assert jbos["has_EOF"]
						assert not jbos["miss_seq_num"]

					touch(J(render_path, GOOD_MARKER_NAME))
					good_renders.append((recording_name, render_path))
				except AssertionError as e:
					# Mark that this is a bad file.
					touch(J(render_path, BAD_MARKER_NAME))
					remove(J(render_path, GOOD_MARKER_NAME))
					bad_renders.append((recording_name, render_path))

	return good_renders, bad_renders

# 2.Renders the actions.
def render_actions(renders: list):
	"""
	For every render directory, we render the actions
	"""
	good_renders = []
	bad_renders = []

	for recording_name, render_path in tqdm.tqdm(renders):
		if E(J(render_path, 'network.npy')):
			if E(J(render_path, GOOD_MARKER_NAME)):
					good_renders.append((recording_name, render_path))
			else:
				bad_renders.append((recording_name, render_path))
		else:
			try:
				recording = get_recording_archive(recording_name)
				extract = lambda fname: recording.extract(fname, render_path)

				# Extract actions
				assert str(ACTION_FILE) in [str(x) for x in recording.namelist()]
				# Extract it if it doesnt exist
				action_mcbr = extract(ACTION_FILE)
				# Check that it's not-empty.
				assert not os.stat(action_mcbr).st_size == 0

				# Run the actual parse action and make sure that its actually of length 0.
				p = subprocess.Popen(["python3", "parse_action.py",os.path.abspath(action_mcbr)], cwd='action_rendering')
				returncode = (p.wait())
				assert returncode == 0

				good_renders.append((recording_name, render_path))
			except AssertionError as e:
				touch(J(render_path, BAD_MARKER_NAME))
				remove(J(render_path, GOOD_MARKER_NAME))
				bad_renders.append((recording_name, render_path))

	return good_renders, bad_renders

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

	print("Constructing render directories.")
	renders = construct_render_dirs(blacklist)

	print("Rendering metadata from files:")
	valid_renders, invalid_renders = render_metadata(renders)
	print(len(valid_renders))
	print("Rendering actions: ")
	valid_renders, invalid_renders = render_actions(valid_renders)
	print("... found {} valid recordings and {} invalid recordings"
	  " out of {} total files".format(
	  	len(valid_renders), len(invalid_renders), len(os.listdir(MERGED_DIR)))
	)
	print("Rendering videos: ")
	render_videos(valid_renders)




	from IPython import embed; embed()

if __name__ == "__main__":
	main()