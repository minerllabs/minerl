/* Yinglan Chen, July 2018 */
/* parse function that takes in a player_stream file and parse it to 
 * FILE_NUM output files.
 * player_stream has the following format:
    [entry][sequence_number][time_stamp][len][json data]
*/
#include <stdio.h>
#include <string.h>

#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>


const int FILE_NUM = 14;
const int BUF_LEN = 500000;
const char* default_src_stream = "new.bin";

const char* FILES[] =  {
    "null",                     /* 0 */
    "metaData.json", 
    "recording.tmcpr",         
    "resource_pack.zip",         
    "resource_pack_index.json" ,  
    "thumb.json",                 
    "visibility",        
    "visibility.json" ,           
    "markers.json",               
    "asset.zip",  
    "pattern_assets.zip",               
    "mods.json",      
    "end_of_stream.txt",              
    "stream_meta_data.json" 
};

const char* WRITE_METHODS[] =  {
    "a",                     /* 0 */
    "w+", 
    "a",         
    "w+",         
    "w+" ,  
    "w+",                 
    "w+",        
    "w+" ,           
    "w+",               
    "a",  
    "a",               
    "w+",      
    "a",              
    "w+" 
};

/* use this part for easier testing
const char* Files[] =  {
    "output0",                       
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
        // 4 on brandon's side and 5 here   
};
*/ 

/* function prototypes */
unsigned int string_to_unsigned_int(char* buf);
unsigned int get_entry(char* buf, FILE* stream);
unsigned int get_sequence_number(char* buf, FILE* stream);
unsigned int get_time_stamp(char* buf, FILE* stream);
unsigned int get_len(char* buf, FILE* stream);

/* MAIN */
// Exception CorruptedStream?
// next: overwrite or append? 
// future: output a meta data json for my streaming. 
//      {error: false, eof: true, esg:...}
int main(int argc, char **argv)
{   
    int opt;
    char buf[BUF_LEN];
    unsigned int entry, time_stamp, len, sequence_number;
    int counter = 0;
    size_t err_check;
    FILE* input;
    FILE* output;
    const char* src_stream = default_src_stream;

    while ((opt = getopt(argc, argv, "f:")) != -1){
        switch (opt) {
            case 'f':
            src_stream = optarg;
            break;
        }
    }
    printf("running %s...\n", src_stream);

    // open input file
    input = fopen(src_stream,"r");
    if (input == NULL)
    {
        printf("Error opening the source stream. Abort.\n");
    }
    
    // be careful: error handling, check return of fread value later 
    
    // to-do: distinguish EOF and error
    while ((err_check= fread(buf, 4, 1, input)) == 1)
    {
        printf("[%d]\n",counter);
        /* entry: first fread in while loop condition */
        entry = get_entry(buf, input);
        printf("entry = %u\n", entry);

        /* sequence_number */
        fread(buf, 4, 1, input);
        sequence_number = get_sequence_number(buf, input);
        printf("sequence_number = %u\n", sequence_number);

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
        printf("data = %s\n", buf);
        // open output

        if (entry < FILE_NUM){ 
            output = fopen(FILES[entry], WRITE_METHODS[entry]); // w+ or "a"
            if (output == NULL) 
            {
                printf("failed to open the output file %d\n", entry);
            }
            if (fwrite(buf, len, 1, output) != 1)
                {printf("trouble writing to output\n" );}
            fclose(output);
        }

        else
        {
            printf("corrupted data? with entry = %u\n", entry);
        }


        printf("file position: %ld\n\n", ftell(input));
        counter++;
    }
    

    err_check = fclose(input);
    if (err_check != 0)
    {
        printf("error closing the source stream. \n");
    }
    printf("finish parsing the source stream.\n");
    return 0;
}

/* HELPER FUNCTIONS */

/* convert string to unsigned int*/
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

// return entry, assume already copied to buf
unsigned int get_entry(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return time_stamp, assume already copied to buf
unsigned int get_time_stamp(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return time_stamp, assume already copied to buf
unsigned int get_len(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}

// return sequence_number, assume already copied to buf
unsigned int get_sequence_number(char* buf, FILE* stream)
{
    return string_to_unsigned_int(buf);
}