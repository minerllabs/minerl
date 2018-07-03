/* Yinglan Chen, July 2018 */
/* Header comments go here: parse function */
/*
    stream has the following format:
    [entry][len][json data]
*/
#include <stdio.h>
#include <string.h>

const char* src_stream = "muffins.bin";
const char* Files[] =  {
    "meta_data.json",             
    "entity_positions.json",      
    "resource_pack.json",         
    "resource_pack_index.json" ,  
    "thumb.json",                 
    "visibility_old.json",        
    "visibility.json" ,           
    "markers.json",               
    "asset.json",                 
    "mods.json",                  
    "end_of_stream.json",              
    "stream_meta_data.json"            
};

const int FILE_NUM = 12;
const int BUF_LEN = 5000;

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

/* MAIN */
// Exception CorruptedStream?
// curr: different output file?
// next: overwrite or append? 
// future: output a meta data json for my streaming. {error: false, eof: true, esg:...}
int main(int argc, char const *argv[])
{   
    char buf[BUF_LEN];
    unsigned int entry, time_stamp, len;
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
        printf("[%d]fread(entry) returns  %zu\n",counter,dummy);
        /* entry: first fread in while loop condition */
        entry = get_entry(buf, input);
        printf("entry = %u\n", entry);

        /* time_stamp */
        fread(buf, 4, 1, input);
        time_stamp = get_time_stamp(buf, input);
        printf("time_stamp = %u\n", time_stamp);

        /* len */
        fread(buf, 4, 1, input);
        len = get_len(buf, input);
        printf("len = %u\n", len);

        /* data */
        fread(buf, len, 1, input);
        printf("data = %s, now try to write to output file\n", buf);
        // open output
        output = fopen(Files[entry], "w+");
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
