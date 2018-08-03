import pyautogui
import time
import os
from shutil import copyfile

#inDir = 'c:\\users\\ricky\\appdata\\roaming\\.minecraft\\replay_recordings\\hold"'
inDir = 'c:/users/ricky/appdata/roaming/.minecraft/replay_recordings/hold'
workingDir = 'c:/users/ricky/appdata/roaming/.minecraft/replay_recordings'
videoDir = 'c:/users/ricky/appdata/roaming/.minecraft/replay_videos'
finishedFile = 'c:/users/ricky/appdata/roaming/.minecraft/finished.txt'




def launchMC():
    # Run the Mine Craft Launcher
    cmd = '"C:\Program Files (x86)\Minecraft\MinecraftLauncher.exe"'
    os.startfile(cmd)
    print ("Launched ",cmd)

    x = 2944
    y = 1794
    print ("Launching Minecraft")
    pyautogui.moveTo(x,y)

    time.sleep(15) # Give the launcher time to come up
    # Click on the launcher button that starts Minecraft
    pyautogui.click(x,y)
    time.sleep(30)


def launchReplayViewer():
    x = 1782
    y = 1172
    pyautogui.moveTo(x,y)
    time.sleep(10)

    print ("\tLaunching ReplayViewer")
    pyautogui.click(x,y) # Then click the button that launches replayMod



# My replaySender pauses playback after 5 seconds of video has played this allows us to do what we need
def launchRendering():
    time.sleep(10);
    pyautogui.typewrite('t') # turn off mouse controls
    time.sleep(0.100)
    x = 1588
    y = 975
    pyautogui.moveTo(x,y)
    time.sleep(3)
    
    print ("\tLaunching render")
    pyautogui.click(x,y) # Then click the button that launches replayMod


# Just in case the finish file wasn't deleted before
if os.path.exists(finishedFile):
    print ("Deleting: ",finishedFile)
    os.remove(finishedFile)


counter = 0
launchMC()
for r, d, f in os.walk(inDir):
    for file in f: # For each .mcpr file - copy it to replay_recordings and then render it
        if ".mcpr" in file:
            print("Processing:",os.path.join(r, file))
            copyfile(os.path.join(r, file),os.path.join(workingDir,file)) # Don't touch the original files - just make a copy and then delete it
            launchReplayViewer() # Presses the ReplayViewer() button - this step can be automated in the code, but this is cleaner
            launchRendering() # Launch rendering inside the replaymod - this is the piece I have not been able to automate due to thread issues

            # RAH Modified version of ReplayMod writes a text file called finished.txt when it is done
            # Look for this file to determine when the system is done rendering and then exit replaymod, delete the working file and exit ReplayMod
            notFound = True
            while notFound:
                if os.path.exists(finishedFile):
                    print ("\tRendering is complete!!!!!")
                    os.remove(finishedFile)
                    notFound = False
                else:
                    time.sleep(10)
            time.sleep(5)
            try:
                os.remove(os.path.join(workingDir,file))
            except:
                # This should be a timeout and then retry - MC is not done closing the file yet
                pass

            # Need to rename the output file to match the input filename
            for vr,vd,vf in os.walk(videoDir):
                for videoFile in vf:
                    print ("Video file:",os.path.join(vr,videoFile))
                    #os.rename(os.path.join(vr,videoFile),"fubar.mp4")
            if counter > 5:
                exit (0)
            counter += 1
exit (0)
