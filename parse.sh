#!/bin/bash
cd deepmine-alpha-data
rm foo.txt
rm combine.txt

for file in `ls`
do
  echo ${file} |cut -d "_" -f3 >> foo.txt
  foo=$(echo ${file} |cut -d "_" -f3)
  echo ${foo}
  cat player_stream_$foo* > combine_$foo.txt
done


# rem merget files
# cat *.txt >> all.txt?
# echo *.txt | xargs cat > all.txt

#  For Bash, IIRC, that's alphabetical order. 
#  If the order is important, you should either name the files appropriately 
#  (01file.txt, 02file.txt, etc...) or specify each file in the order you want it concatenated.

# $ cat file1 file2 file3 file4 file5 file6 > out.txt
# cat >> ...

# nested for loop?
# 	first one: fix one stream, find "username"
# 	next: loop through, append to it, cat >>, and delete that file???

# player_stream_262CPI_06_29_20_16_04-1-2018-07-05-19-39-56-8b5dd8a6-0ece-48f1-ba26-f1326dc5b374
# player_stream_*_06_29_20_16_04-1-2018-07-05-19-39-56-8b5dd8a6-0ece-48f1-ba26-f1326dc5b374

# Any filenames that match the glob are gathered up and sorted
# rem parse and zip them one by one

# git clone to download the parse executable?
# for each src_stream to parse:
# rem for file in *; do rm "$file"; done


# $ filename="somefile.jpg"
# $ if [[ $filename = *.jpg ]]; then
# > echo "$filename is a jpeg"
# > fi
# somefile.jpg is a jpeg



# for file in `ls`|cut -d"-" -f1
# do
#   cat ${file}-* > ${file}
# done


# 	mkdir result
# 	./parse -f <src_stream>

# 	zip -r my-folder.zip my-folder -x "*.DS_Store"
# 	rm -r result

# shopt -s extglob
#  echo !(*jpg|*bmp)



