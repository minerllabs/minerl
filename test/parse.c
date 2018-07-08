/* Yinglan Chen, July 2018 */

/* a parse function that takes in a player_stream file and parse it to 
 * FILE_NUM output files.
 * player_stream has the following format:
    [entry][sequence_number][time_stamp][len][json data]
 * implementation:
 *  keep append files open, open and close write files
 */
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include "zlib.h"


const int EOF_ENTRY = 12;
const int OVERWRITE = 0;
const int APPEND = 1;
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
};

const int WRITE_METHODS[] =  {
    APPEND,                     /* 0 */
    OVERWRITE, 
    APPEND,                     /* 2 */
    OVERWRITE,         
    OVERWRITE ,                 /* 4 */ 
    OVERWRITE,                 
    OVERWRITE,                  /* 6 */ 
    OVERWRITE ,           
    OVERWRITE,                  /* 8 */           
    APPEND,   
    APPEND,                     /* 10 */ 
    OVERWRITE,      
    APPEND,                     /* 12 */ 
};

const char* JSON[]= 
{
    "{\"has_EOF\":true,\"miss_seq_num\":true}",
    "{\"has_EOF\":true,\"miss_seq_num\":false}",
    "{\"has_EOF\":false,\"miss_seq_num\":true}",
    "{\"has_EOF\":false,\"miss_seq_num\":false}",
};

/*
 * If DEBUG is defined, enable printing on dbg_printf.
 */
#ifdef DEBUG
/* When debugging is enabled, these form aliases to useful functions */
#define dbg_printf(...) printf(__VA_ARGS__)
#define dbg_assert(...) assert(__VA_ARGS__)
#else
/* When debugging is disabled, no code gets generated */
#define dbg_printf(...)
#define dbg_assert(...) 
#endif

/* function prototypes */
unsigned int string_to_unsigned_int(char* buf);
unsigned int get_entry(char* buf, FILE* stream);
unsigned int get_sequence_number(char* buf, FILE* stream);
unsigned int get_time_stamp(char* buf, FILE* stream);
unsigned int get_len(char* buf, FILE* stream);
void parse(FILE* input);


/* implementation */

void parse(FILE* input)
{ 
    // TODO: error handling, check return of fread value 
    FILE* output; // for overwrite files
    FILE* outputs[FILE_NUM]; // for append files
    FILE* meta;
    int meta_len = 0;
    int counter = 0, err_check;
    char buf[BUF_LEN];
    char* backup_buf = NULL;
    int backup_buf_len = 0;
    
    unsigned int entry, time_stamp, len, sequence_number;
    int checked_seq_num = 0;
    bool miss_seq_num = false;
    bool has_EOF = false;
    
    // open all "a" output
    for (int i = 0; i < FILE_NUM; i++)
    {
        if (WRITE_METHODS[i] == APPEND)
        {
            outputs[i] = fopen(FILES[i],"w+");
            if (outputs[i] == NULL)
            {
                printf("error opening file %s. Abort\n", FILES[i]);
                exit(-1);
            }
            else
            {
                dbg_printf("successfully open file [%d] %s\n", i, FILES[i]);
            }
        }
    }

    // to-do: distinguish EOF and error
    while ((err_check= fread(buf, 4, 1, input)) == 1)
    {
        dbg_printf("[%d]\n",counter);
        /* entry: first fread in while loop condition */
        entry = get_entry(buf, input);
        
        /* sequence_number */
        fread(buf, 4, 1, input);
        sequence_number = get_sequence_number(buf, input);

        /* time_stamp */
        fread(buf, 4, 1, input);
        time_stamp = get_time_stamp(buf, input);

        /* len */
        fread(buf, 4, 1, input);
        len = get_len(buf, input);
        
        /* data */ 
        if (len > BUF_LEN) // handle exception first
        {
            printf("detect data with %u bytes\n", len );
            
            // reuse back_up buf if possible; if not, alloc new one
            if (len > backup_buf_len)
            {
                if (backup_buf != NULL) free(backup_buf);

                backup_buf = malloc(sizeof(len)); 
                if (backup_buf == NULL)
                {
                printf("failed to allocate new buffer, abort\n");
                // no file leaks since close rightaway
                exit(-1);
                }
                backup_buf_len = len;
            }
            fread(backup_buf , len, 1, input);
            dbg_printf("data too long, omit printing\n");
        }
        else
        {
            fread(buf, len, 1, input);
            dbg_printf("data = %s\n", buf);
        }
        
        
        /* open and write output */
        if (entry < FILE_NUM)
        { 
            // case 1: append, directly write
            if (WRITE_METHODS[entry] == APPEND)
            {
                if ((err_check = fwrite(buf, len, 1, outputs[entry])) != 1)
                {
                    printf("trouble writing to output file[%d] %s\n",
                       entry,FILES[entry] );
                }
            }
            // case 2: overwrite
            else
            {
                dbg_assert(WRITE_METHODS[entry] == OVERWRITE);
                output = fopen(FILES[entry], "w+");
                // error checking
                if (output == NULL) 
                {
                    printf("failed to open the output file %d\n", entry);
                }
                // write and close
                if (fwrite(buf, len, 1, output) != 1)
                {
                    printf("trouble writing to output\n" );
                }
                fclose(output);
            } 
        }

        else // invalid entry
        {
            printf("corrupted data? with entry = %u\n", entry);
        }

        /* check has_EOF */ /* question: no entries afterwards? */
        if (entry == EOF_ENTRY)
        {
            has_EOF = true;
        }

        /* check miss_seq_num */ 
        if (checked_seq_num == 0 && counter != sequence_number)
        {
            miss_seq_num = true;
            checked_seq_num = true;
        }
        dbg_printf("file position: %ld\n\n", ftell(input));
        counter++;
    }

    // close all "a" output
    for (int i = 0; i < FILE_NUM; i++)
    {
        if (WRITE_METHODS[i]== APPEND)
        {
            err_check = fclose(outputs[i]);
            if (err_check != 0)
            {
                printf("error closing file %s. Abort\n", FILES[i]);
            }
            else
            {
                dbg_printf("successfully close file [%d] %s\n", i, FILES[i]);
            }
        }
    }

    // create stream_meta_data
    meta = fopen("stream_meta_data.json", "w+");
    if (meta == NULL) printf("error creating stream_meta_data.json\n");
    // four cases 
    if (has_EOF && miss_seq_num)
    {
        strncpy(buf, JSON[0], strlen(JSON[0]));
        meta_len = strlen(JSON[0]);
    }
    else if (has_EOF && !miss_seq_num)
    {
        strncpy(buf, JSON[1], strlen(JSON[1]));
        meta_len = strlen(JSON[1]);
    }
    else if (!has_EOF && miss_seq_num)
    {
        strncpy(buf, JSON[2], strlen(JSON[2]));
        meta_len = strlen(JSON[2]);
    }
    else 
    {
        strncpy(buf, JSON[3], strlen(JSON[3]));
        meta_len = strlen(JSON[3]);
    }
    fwrite(buf, meta_len, 1, meta);
    fclose(meta);
}


/* MAIN */
int main(int argc, char **argv)
{   
    int opt;
    size_t err_check;
    FILE* input;
    const char* src_stream = default_src_stream;

    // get src_stream
    while ((opt = getopt(argc, argv, "f:")) != -1){
        switch (opt) {
            case 'f':
                src_stream = optarg;
                break;
        }
    }
    // display info
    printf("running %s...\n", src_stream);

    // open input file
    input = fopen(src_stream,"r");
    if (input == NULL)
    {
        printf("Error opening the source stream. Abort.\n");
    }

    // the main parse function
    parse(input);
    
    // close input file
    err_check = fclose(input);
    if (err_check != 0)
    {
        printf("error closing the source stream. \n");
    }
    // finish and return
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
    unsigned int entry = string_to_unsigned_int(buf);
    dbg_printf("entry = %u\n", entry);
    return entry;
}

// return time_stamp, assume already copied to buf
unsigned int get_time_stamp(char* buf, FILE* stream)
{
    unsigned int time_stamp = string_to_unsigned_int(buf);
    dbg_printf("time_stamp = %u\n", time_stamp);
    return time_stamp;
}

// return time_stamp, assume already copied to buf
unsigned int get_len(char* buf, FILE* stream)
{
    unsigned int len = string_to_unsigned_int(buf);
    dbg_printf("len = %u\n", len);
    return len;
}

// return sequence_number, assume already copied to buf
unsigned int get_sequence_number(char* buf, FILE* stream)
{
    unsigned int sequence_number = string_to_unsigned_int(buf);
    dbg_printf("sequence_number = %u\n", sequence_number);
    return sequence_number;
}