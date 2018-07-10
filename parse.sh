#!/bin/bash
rm -r streams
mkdir streams

cd 'deepmine-alpha-data'
rm list_all.txt
rm unique.txt

# create a list of files to merge, contains duplicates
for file in player*
do
  who=$(echo ${file} |cut -d "-" -f1)
  version=$(echo ${file} |cut -d "-" -f2)
  echo "$who-$version" >> list_all.txt
done

# remove duplicates and store to a new file
sort -u list_all.txt > unique.txt

# merge files from the same user with the same stream version
while read p; do
  # ensure alphabtical order
  cat $p* > ../streams/merge_$p.bin
done <unique.txt

cd ..

# for file in ./streams/recording*
for file in ./streams/merge*
do
	mkdir result # a temporary folder
	./parse -f $file
  fileName=$(echo ${file} |cut -d "/" -f3)
  fileName=$(echo ${fileName} |cut -d "." -f1)
  cd result
	zip -r $fileName.mcpr ./*
  cp $fileName.mcpr ../
  cd ..
	rm -r result
done

echo DONE






