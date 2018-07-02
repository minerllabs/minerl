/* Yinglan Chen, July 2018 */
/* Header comments go here: parse function */

#include <stdio.h>
#include <string.h>
// helper function: read entry, read len, read time_stamp, read data
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


/* HELPER FUNCTIONS */

/* convert string to int 
 * REQUIRES: 
 */

int string_to_int(char* buf)
{
    int result = 0;
    int curr;
    for (int i = 0; i < 4; i++)
    {
        curr = (int) buf[i];
        result = (result << 8) + curr;
    }
    return result;
}

// return entry
int get_entry(char* buf, FILE* stream)
{
    return string_to_int(buf);
}

// return time_stamp
int get_time_stamp(char* buf, FILE* stream)
{
    return string_to_int(buf);
}

// return time_stamp
int get_len(char* buf, FILE* stream)
{
    return string_to_int(buf);
}

// Exception CorruptedStream?
// curr step goal: read one [entry, time_stamp, len, data] and redirect output to a file
int main(int argc, char const *argv[])
{   

    char buf[256];
    int entry, time_stamp, len;
    FILE* input = fopen("test_foo_stream","r");
    FILE* output = fopen("output_test","w+");
    /*
        stream has the following format:
        [entry][len][json data]
    */
    
    // be careful: error handling, check return of fread value later 
    // temporary testing: read and print out first data 

    /* entry */
    fread(buf, sizeof(int), 1, input);
    entry = get_entry(buf, input);
    /* time_stamp */
    fread(buf, sizeof(int), 1, input);
    time_stamp = get_time_stamp(buf, input);
    /* len */
    fread(buf, sizeof(int), 1, input);
    len = get_len(buf, input);
    /* data */
    fread(buf, len, 1, input);
    fwrite(buf,len, 1, output);

    printf("entry = %d\n", entry);
    printf("time_stamp = %d\n", time_stamp);
    printf("len = %d\n", len);
    printf("please open output_test to check data, the expected output is 456\n");
    
    fclose(input);
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