import os
import shutil
import stat
import urllib.request

from os.path import join as J, exists as E


from minerl.data.util.constants import RENDERERS_DIR as BASE_DIR
from minerl.data.util.constants import NUM_MINECRAFTS


MINECRAFT_TEMPLATE= os.path.abspath(J(os.path.dirname(__file__), '..', 'assets', 'template_minecraft'))
DOTMINECRAFT = os.path.abspath(J(BASE_DIR, '.minecraft'))
LAUNCH_STR = (
  '''
#!/bin/bash \\
  xvfb-run -f {4} -n {3}  java \\
  -Xms4G \\
  -Xmx8G  \\
  -XX:+UseG1GC  \\
  -XX:+UnlockExperimentalVMOptions \\
  -XX:MaxGCPauseMillis=100 \\
  -XX:+DisableExplicitGC \\
  -XX:TargetSurvivorRatio=90 \\
  -XX:G1NewSizePercent=35  \\
  -XX:G1MaxNewSizePercent=60  \\
  -XX:InitiatingHeapOccupancyPercent=15 \\
  -XX:G1MixedGCLiveThresholdPercent=50 \\
  -XX:+AggressiveOpts \\
  -XX:+AlwaysPreTouch \\
  -XX:+UseLargePagesInMetaspace \\
  -Xmx10G \\
  -XX:+UnlockExperimentalVMOptions \\
  -XX:+UseG1GC -XX:G1NewSizePercent=20 \\
  -XX:G1ReservePercent=20 \\
  -XX:MaxGCPauseMillis=50 \\
  -XX:G1HeapRegionSize=32M  \\
  -Djava.library.path={1} \\
  -Dminecraft.launcher.brand=minecraft-launcher \\
  -Dminecraft.launcher.version=2.1.1349 \\
  -Dminecraft.client.jar={0}/versions/1.12.2/1.12.2.jar \\
  -cp \\
{0}/libraries/net/minecraftforge/forge/1.12.2-14.23.4.2745/forge-1.12.2-14.23.4.2745.jar\\
:{0}/libraries/net/minecraft/launchwrapper/1.12/launchwrapper-1.12.jar\\
:{0}/libraries/org/ow2/asm/asm-all/5.2/asm-all-5.2.jar\\
:{0}/libraries/org/jline/jline/3.5.1/jline-3.5.1.jar\\
:{0}/libraries/net/java/dev/jna/jna/4.4.0/jna-4.4.0.jar\\
:{0}/libraries/com/typesafe/akka/akka-actor_2.11/2.3.3/akka-actor_2.11-2.3.3.jar\\
:{0}/libraries/com/typesafe/config/1.2.1/config-1.2.1.jar\\
:{0}/libraries/org/scala-lang/scala-actors-migration_2.11/1.1.0/scala-actors-migration_2.11-1.1.0.jar\\
:{0}/libraries/org/scala-lang/scala-compiler/2.11.1/scala-compiler-2.11.1.jar\\
:{0}/libraries/org/scala-lang/plugins/scala-continuations-library_2.11/1.0.2/scala-continuations-library_2.11-1.0.2.jar\\
:{0}/libraries/org/scala-lang/plugins/scala-continuations-plugin_2.11.1/1.0.2/scala-continuations-plugin_2.11.1-1.0.2.jar\\
:{0}/libraries/org/scala-lang/scala-library/2.11.1/scala-library-2.11.1.jar\\
:{0}/libraries/org/scala-lang/scala-parser-combinators_2.11/1.0.1/scala-parser-combinators_2.11-1.0.1.jar\\
:{0}/libraries/org/scala-lang/scala-reflect/2.11.1/scala-reflect-2.11.1.jar\\
:{0}/libraries/org/scala-lang/scala-swing_2.11/1.0.1/scala-swing_2.11-1.0.1.jar\\
:{0}/libraries/org/scala-lang/scala-xml_2.11/1.0.2/scala-xml_2.11-1.0.2.jar\\
:{0}/libraries/lzma/lzma/0.0.1/lzma-0.0.1.jar\\
:{0}/libraries/net/sf/jopt-simple/jopt-simple/5.0.3/jopt-simple-5.0.3.jar\\
:{0}/libraries/java3d/vecmath/1.5.2/vecmath-1.5.2.jar\\
:{0}/libraries/net/sf/trove4j/trove4j/3.0.3/trove4j-3.0.3.jar\\
:{0}/libraries/org/apache/maven/maven-artifact/3.5.3/maven-artifact-3.5.3.jar\\
:{0}/libraries/com/mojang/patchy/1.1/patchy-1.1.jar\\
:{0}/libraries/oshi-project/oshi-core/1.1/oshi-core-1.1.jar\\
:{0}/libraries/net/java/dev/jna/jna/4.4.0/jna-4.4.0.jar\\
:{0}/libraries/net/java/dev/jna/platform/3.4.0/platform-3.4.0.jar\\
:{0}/libraries/com/ibm/icu/icu4j-core-mojang/51.2/icu4j-core-mojang-51.2.jar\\
:{0}/libraries/net/sf/jopt-simple/jopt-simple/5.0.3/jopt-simple-5.0.3.jar\\
:{0}/libraries/com/paulscode/codecjorbis/20101023/codecjorbis-20101023.jar\\
:{0}/libraries/com/paulscode/codecwav/20101023/codecwav-20101023.jar\\
:{0}/libraries/com/paulscode/libraryjavasound/20101123/libraryjavasound-20101123.jar\\
:{0}/libraries/com/paulscode/librarylwjglopenal/20100824/librarylwjglopenal-20100824.jar\\
:{0}/libraries/com/paulscode/soundsystem/20120107/soundsystem-20120107.jar\\
:{0}/libraries/io/netty/netty-all/4.1.9.Final/netty-all-4.1.9.Final.jar\\
:{0}/libraries/com/google/guava/guava/21.0/guava-21.0.jar\\
:{0}/libraries/org/apache/commons/commons-lang3/3.5/commons-lang3-3.5.jar\\
:{0}/libraries/commons-io/commons-io/2.5/commons-io-2.5.jar\\
:{0}/libraries/commons-codec/commons-codec/1.10/commons-codec-1.10.jar\\
:{0}/libraries/net/java/jinput/jinput/2.0.5/jinput-2.0.5.jar\\
:{0}/libraries/net/java/jutils/jutils/1.0.0/jutils-1.0.0.jar\\
:{0}/libraries/com/google/code/gson/gson/2.8.0/gson-2.8.0.jar\\
:{0}/libraries/com/mojang/authlib/1.5.25/authlib-1.5.25.jar\\
:{0}/libraries/com/mojang/realms/1.10.22/realms-1.10.22.jar\\
:{0}/libraries/org/apache/commons/commons-compress/1.8.1/commons-compress-1.8.1.jar\\
:{0}/libraries/org/apache/httpcomponents/httpclient/4.3.3/httpclient-4.3.3.jar\\
:{0}/libraries/commons-logging/commons-logging/1.1.3/commons-logging-1.1.3.jar\\
:{0}/libraries/org/apache/httpcomponents/httpcore/4.3.2/httpcore-4.3.2.jar\\
:{0}/libraries/it/unimi/dsi/fastutil/7.1.0/fastutil-7.1.0.jar\\
:{0}/libraries/org/apache/logging/log4j/log4j-api/2.8.1/log4j-api-2.8.1.jar\\
:{0}/libraries/org/apache/logging/log4j/log4j-core/2.8.1/log4j-core-2.8.1.jar\\
:{0}/libraries/org/lwjgl/lwjgl/lwjgl/2.9.4-nightly-20150209/lwjgl-2.9.4-nightly-20150209.jar\\
:{0}/libraries/org/lwjgl/lwjgl/lwjgl_util/2.9.4-nightly-20150209/lwjgl_util-2.9.4-nightly-20150209.jar\\
:{0}/libraries/com/mojang/text2speech/1.10.3/text2speech-1.10.3.jar\\
:{0}/versions/1.12.2/1.12.2.jar\\
    net.minecraft.launchwrapper.Launch \\
        --username imushroom1 \\
        --version 1.12.2-forge1.12.2-14.23.4.2745 \\
        --gameDir {2} \\
        --assetsDir {0}/assets \\
        --assetIndex 1.12 \\
        --uuid ce7c20e4445443eea7c184eb6dad13c1 \\
        --accessToken ca36dda91089440fb5a8e5f0f2185c25 \\
        --userType mojang \\
        --tweakClass net.minecraftforge.fml.common.launcher.FMLTweaker \\
        --versionType Forge &> {2}/logs/debug.log &
PID=$!
XAUTHORITY={4} x11vnc -rfbport 50{3} -display :{3}.0 -forever  &> {2}/logs/xvnc.log
wait $PID \\''')

import io
def download(url, file_name):
  out_file =  open(file_name, 'wb+')
  with urllib.request.urlopen(url) as response:
      length = response.getheader('content-length')
      if length:
          length = int(length)
          blocksize = max(4096, length//100)
      else:
          blocksize = 1000000 # just made something up

      print(length, blocksize)

      size = 0
      while True:
          buf1 = response.read(blocksize)
          out_file.write(buf1)
          if not buf1:
              break
          size += len(buf1)
          if length:
              print('{:.2f}\r done'.format(size/length), end='')
  out_file.close()
      
  

import zipfile

if __name__ == "__main__":
  print("Downloading mincraft assets and binaries.")
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
    libs_zip =J(cracked_libs,'libs.zip')
    download('https://minerl.s3.amazonaws.com/assets/libs.zip', libs_zip)
    with zipfile.ZipFile(libs_zip, 'r') as zip_ref:
      zip_ref.extractall(cracked_libs)


  for i, mc in enumerate(range(NUM_MINECRAFTS)):
    print("hi")
    target_mc_name = os.path.abspath(J(BASE_DIR, 'minecraft_{}'.format(mc)))
    if os.path.exists(target_mc_name):
      shutil.rmtree(target_mc_name)
    shutil.copytree(MINECRAFT_TEMPLATE, target_mc_name)
    xauth = os.path.join(target_mc_name, 'xauth')
    with open(os.path.join(target_mc_name, 'launch.sh'), 'w') as f:
        f.write(LAUNCH_STR.format(DOTMINECRAFT, cracked_libs, target_mc_name, i +20, xauth))

    file = (os.path.join(target_mc_name, 'launch.sh'))
    st = os.stat(file)
    os.chmod(file, st.st_mode | stat.S_IEXEC)
