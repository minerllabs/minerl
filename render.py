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
import glob
import numpy as np
import tqdm
import zipfile
import subprocess
import json
import time
from shutil import copyfile

######################3
### UTILITIES
#######################
J = os.path.join
E = os.path.exists
WORKING_DIR = "output"
MERGED_DIR = J(WORKING_DIR, "merged")
RENDER_DIR = J(WORKING_DIR, "rendered")
MINECRAFT_DIR = "C:/Users/Brandon/minecraft_modded"
BLACKLIST_PATH =J(WORKING_DIR, "blacklist.txt")

END_OF_STREAM = 'end_of_stream.txt'
ACTION_FILE = "actions.tmcpr"
END_OF_STREAM_TEXT = 'This is the end.'
BAD_MARKER_NAME, GOOD_MARKER_NAME = 'INVALID', 'VALID'
SKIPPED_RENDER_FLAG = 'SKIPPED_RENDER'

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
	This works by:
	 1) Copying the file to the minecraft directory
	 2) Waiting for user input:
	 		User render the video using replay mod and hit enter once the video is rendered
	 3) Copying the produced mp4 to the rendered directory 

	"""

	for recording_name, render_path in tqdm.tqdm(renders):
		#Get mcpr file from merged
		print("Rendering:", recording_name, '...')

		# Skip if the folder has an recording already
		list_of_files = glob.glob(render_path + '/*.mp4') # * means all if need specific format then *.csv
		if len(list_of_files) > 0:
			print ("Skipping: replay folder contains", list_of_files[0])
			continue

		# Skip if the file has been skipped allready
		skip_path = J(render_path, SKIPPED_RENDER_FLAG)
		if E(skip_path):
			print ("Skipping: file was previously skipped")
			continue


		mcpr_path= J(MERGED_DIR, (recording_name + ".mcpr"))
		recording_path = MINECRAFT_DIR + '/replay_recordings/'
		rendered_video_path = MINECRAFT_DIR + '/replay_videos/'
		copyfile(mcpr_path, recording_path + (recording_name + ".mcpr"))
		copy_time = os.path.getmtime(recording_path + (recording_name + ".mcpr"))

		video_path = None
		while video_path is None:
			user_input = input("Hit enter (q to stop : s to skip)")
			if "q" in user_input:
				return
			if "s" in user_input:
				with open(skip_path, 'a'):
					try:                     
						os.utime(skip_path, None)  # => Set skip time to now
					except OSError:
						pass  # File deleted between open() and os.utime() calls
				break

			# copy the most recent file 
			list_of_files = glob.glob(rendered_video_path + '*.mp4') # * means all if need specific format then *.csv

			if len(list_of_files) > 0:
				#Check that this render was created after we copied 
				video_path = max(list_of_files, key=os.path.getmtime)
				if os.path.getmtime(video_path) < copy_time:
					print ("Error! Rendered file is older than replay!")
					user_input = input("Are you sure you want to copy this out of date render? (y/n)")
					if "y" in user_input:
						print("using out of date recording")
					else:
						print("skipping out of date rendering")
						video_path = None

			else:
				print ("No video file found!")
		if not video_path is None:
			print ("Copying file", video_path, 'to', render_path, 'created', os.path.getmtime(video_path))
			copyfile(video_path, render_path + '/recording.mp4')
			os.remove(video_path)

		# Remove mcpr file from dir
		os.remove(J(recording_path, (recording_name + ".mcpr")))

		


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




	#from IPython import embed; embed()

if __name__ == "__main__":
	main()