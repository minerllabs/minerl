#!/bin/bash
# This script 
# 1) takes in a folder of streams
# 2) concatenated streams with the same prefix and version number 
#   by alphabetical order (thus by time order)
# 3) parse them one by one
# 4) zip the result if exit status is 0 (i.e. success)
# 5) mv all results into oneo folder


home=$(pwd)
working_dir=$home/output
results_dir=$working_dir/merged


# input folder 
path=$working_dir/downloaded
echo "Loading streams from $path"
if [ ! -d $path ]; then
  echo "Could not find parsed files. Did you not download from s3?"
  exit
fi

cd $path

# Create a blacklist
if [ ! -f $working_dir/blacklist.txt ]; then
  touch $working_dir/blacklist.txt
fi

# create a list of files to merge, contains duplicates
echo "Creating a list of files to merge mod the blacklist"
for file in player*
do
  who=$(echo ${file} |cut -d "-" -f1)
  version=$(echo ${file} |cut -d "-" -f2)
  fileName=$(echo "$who-$version" | cut -d "/" -f3)
  fileName=$(echo ${fileName} |cut -d "." -f1)
  if [ ! -f $results_dir/$fileName.mcpr ] &&  ! grep -qF "$fileName.mcpr" "$working_dir/blacklist.txt";
  then
    echo "making $results_dir/$fileName.mcpr"
    # Use this if you want to blacklist all files which haven't been converted
    # This is dangerous.
    # echo "$fileName.mcpr" >> $home/blacklist.txt

    echo "$who-$version" >> $path/list_all.txt
  fi
done


# Make temp directory for zipping streams :)
if [ ! -d $working_dir/streams ]; then
  mkdir $working_dir/streams # during testing, manually remove streams/
fi

# remove duplicates
if [ -f $path/list_all.txt ]; then
  echo "Removing duplicates"
  sort -u $path/list_all.txt > $path/unique.txt
  rm $path/list_all.txt

  # concatenate
  while read p; do
    # ensure alphabtical order
    cat $p* > $working_dir/streams/$p.bin
  done <unique.txt
  rm unique.txt
fi 

# parse and zip
cd $working_dir
if [ ! -d $results_dir ]; then
  mkdir $results_dir
fi 

for file in ./streams/*
do
  # reminder: add "make" if necessary
  mkdir $working_dir/result
  $home/merging/parse -f $file
  # only zip if successfully parse with exit status 0
  if [ $? -eq 0 ] 
    then
      echo "$file"
      fileName=$(echo ${file} |cut -d "/" -f3)
      fileName=$(echo ${fileName} |cut -d "." -f1)
      echo "$fileName"
      cd result
      zip -r $fileName.mcpr ./*
      cp $fileName.mcpr $results_dir/
      cd $working_dir
  else
    echo "BLACKLISTING $fileName.mcpr"
    echo "Blacklisting is currently disabled."
    # echo "$fileName.mcpr" >> $home/blacklist.txt
  fi
  rm -r $working_dir/result
done

rm -r $working_dir/streams
echo DONE






