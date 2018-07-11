#!/bin/bash
# This script 
# 1) takes in a folder of streams
# 2) concatenated streams with the same prefix and version number 
#   by alphabetical order (thus by time order)
# 3) parse them one by one
# 4) zip the result if exit status is 0 (i.e. success)
# 5) mv all results into oneo folder

home=$(pwd)
mkdir streams # during testing, manually remove streams/

# input folder 
path=$1
cd $path

# create a list of files to merge, contains duplicates
for file in player*
do
  who=$(echo ${file} |cut -d "-" -f1)
  version=$(echo ${file} |cut -d "-" -f2)
  echo "$who-$version" >> list_all.txt
done

# remove duplicates
sort -u list_all.txt > unique.txt
rm list_all.txt

# concatenate
while read p; do
  # ensure alphabtical order
  cat $p* > $home/streams/$p.bin
done <unique.txt
rm unique.txt

# parse and zip
cd $home
mkdir results
for file in ./streams/*
do
  # reminder: add "make" if necessary
  mkdir result
  ./parse -f $file
  # only zip if successfully parse with exit status 0
  if [ $? -eq 0 ] 
    then
      fileName=$(echo ${file} |cut -d "/" -f3)
      fileName=$(echo ${fileName} |cut -d "." -f1)
      cd result
      zip -r $fileName.mcpr ./*
      cp $fileName.mcpr ../
      cd ..
  fi
  rm -r result
done
mv ./player* ./results/

rm -r streams
echo DONE






