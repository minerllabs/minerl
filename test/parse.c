/* Yinglan Chen, July 2018 */
/* Header comments go here: parse function */
/*
    stream has the following format:
    [entry][len][json data]
*/
#include <stdio.h>
#include <assert.h>
#include <string.h>

const char* src_stream = "almost_perfect.bin";
// const char* Files[] =  {
//     "null",                         /* 0 */
//     "metaData.json",
//     "recording.tmcpr",          
//     "resource_pack.zip",         
//     "resource_pack_index.json" ,  
//     "thumb.json",                 
//     "visibility",        
//     "visibility.json" ,           
//     "markers.json",               
//     "asset.zip",                 
//     "mods.json",      
//     "end_of_stream.json",              
//     "stream_meta_data.json" 
           
// };

const char* Files[] =  {
    "output0",                         /* 0 */
    "output1.json",
    "output2.tmcpr",          
    "output3.zip",         
    "output4.json" ,  
    "output5.json",                 
    "output6",        
    "output7.json" ,           
    "output8.json",               
    "output9.zip",                 
    "output10.json",      
    "output11.json",              
    "output12.json" 
           
};

const int FILE_NUM = 13;
#define BUF_LEN 50000

/* HELPER FUNCTIONS: read entry, read len, read time_stamp, read data */

/* convert string to int REQUIRES: */
unsigned int string_to_unsigned_int(char* buf)
{
    unsigned int result = 0;
    unsigned int curr;
    for (int i = 0; i < 4; i++)
    {
        curr = (unsigned int)(unsigned char) buf[i];
        // printf("curr: %u\n", curr );
        result = (result << 8) + curr;
    }
    return result;
}

// return entry
unsigned int get_entry(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return time_stamp
unsigned int get_time_stamp(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return time_stamp
unsigned int get_len(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return sequence_number
unsigned int get_sequence_number(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

/* MAIN */
// Exception CorruptedStream?
// curr: different output file?
// next: overwrite or append? 
// future: output a meta data json for my streaming. {error: false, eof: true, esg:...}
int main(int argc, char const *argv[])
{   
    char buf[BUF_LEN];
    unsigned int entry, time_stamp, len, sequence_number;
    int counter = 0;
    size_t dummy;
    FILE* input;
    FILE* output;

    // init input
    input = fopen(src_stream,"r");

    // be careful: error handling, check return of fread value later 
    // temporary testing: read and print out first data 
    
    // to-do: distinguish EOF and error
    while ((dummy = fread(buf, 4, 1, input)) == 1)
    {
        // printf("[%d]fread(entry) returns  %zu\n",counter,dummy);
        printf("[%d]\n",counter);
        /* entry: first fread in while loop condition */
        entry = get_entry(buf, input);
        printf("entry = %u\n", entry);

        /* time_stamp */
        fread(buf, 4, 1, input);
        time_stamp = get_time_stamp(buf, input);
        printf("time_stamp = %u\n", time_stamp);

        /* sequence_number */
        fread(buf, 4, 1, input);
        sequence_number = get_sequence_number(buf, input);
        printf("sequence_number = %u\n", sequence_number);

        /* len */
        fread(buf, 4, 1, input);
        len = get_len(buf, input);
        printf("len = %u\n", len);

        /* data */
        assert(len < BUF_LEN);
        fread(buf, len, 1, input);
        printf("data = %s\n", buf);
        // open output
        // if entry == blah, blah, or blah, open with "a", else (delete? and) "w+"
        output = fopen(Files[entry], "w+"); // w+ or "a"
        if (output == NULL) printf("failed to open output file %d\n", entry);
        if (fwrite(buf,len, 1, output)!= 1)
            {printf("trouble writing to output\n" );}
        fclose(output);
        printf("file position: %ld\n\n", ftell(input));
        counter++;
    }
    
    fclose(input);

    return 0;
}
