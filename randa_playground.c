/* Yinglan Chen, July 2018 */
/* Header comments go here: parse function */

#include <stdio.h>
#include <string.h>

/*  library backup: fgetc and fread

size_t
     fwrite(const void *restrict ptr, size_t size, size_t nitems,
         FILE *restrict stream);
size_t
     fread(void *restrict ptr, size_t size, size_t nitems,
         FILE *restrict stream);

The function fread() reads nitems objects, each size bytes long, from the
     stream pointed to by stream, storing them at the location given by ptr.

The functions fread() and fwrite() advance the file position indicator for
     the stream by the number of bytes read or written.  They return the number
     of objects read or written.  If an error occurs, or the end-of-file is
     reached, the return value is a short object count (or zero).

     The function fread() does not distinguish between end-of-file and error;
     callers must use feof(3) and ferror(3) to determine which occurred.  The
     function fwrite() returns a value less than nitems only if a write error has
     occurred.
*/

// Exception CorruptedStream?
// curr step goal: read one [entry, timestamp, len, data] and redirect output to a file
int main(int argc, char const *argv[])
{   

    char tmp_buf[256];
    int entry;
    int time_stamp;
    int len;
    // char buf[256]; // warning: dont know how large one data chunk will be; 
    // char lenBuf[256];
    size_t dummy;
    FILE* mystream = fopen("test_foo_stream","r");
    FILE* output = fopen("output_test","w+");
    /*
        stream has the following format:
        [entry][len][json data]
    */
    // be careful: error handling 
    // temporary testing: read and print out first data 

    /* entry */
    dummy = fread(tmp_buf, sizeof(int), 1, mystream);

    sscanf(tmp_buf, "%d", &entry); // bug: always thought entry = 0
    // probably because 00 is the null terminator so c thought it is empty string
    /* timestamp */
    dummy = fread(tmp_buf, sizeof(int), 1, mystream);
    sscanf(tmp_buf, "%d", &time_stamp);
    /* len */
    dummy = fread(tmp_buf, sizeof(int), 1, mystream);
    sscanf(tmp_buf, "%d", &len);
    /* data */
    fread(tmp_buf, len, 1, mystream);// hardcoded here
    dummy = fwrite(tmp_buf, sizeof(int),1,output);
   
    printf("entry = %d, time_stamp = %d, len = %d\n", 
        entry, time_stamp, len);
    printf("please manually check the output_test file, the expected output is 4567abcdefgh\n");
    fclose(mystream);
    fclose(output);
    return 0;
}


/*
whlie not EOF

1. read 4 bytes => entries
2. read 4 bytes => len
3. read the next len bytes => write to a corresponding file

exit 

do i need: flush? 

change std out to a file? 

first write to some buffer??? then write to file??
*/