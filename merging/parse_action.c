/* Yinglan Chen, July 2018 */

/* this parse function takes in an action.tmcpr file and parses it
 * a list of malmo commands. 
 *
 * action.tmcpr has the following format:
 --
 |        [timestamp]     # 4 bytes (int)
 |        [len]           # 4 byets (int)
 |  --    
 |  |     [package id]    # 1 byte  (temporary fixed value 0x18)
 |  |     [len2]          # 1 byte
 |  |  -- 
 | len |  
 |   len2 [channel name]  # char*
 |  |  |                  # recorded_actions || recorded_camera_actions || tick
 |  |  -- 
 |  |     [data]          # can be computed with len & len2 
 |  --    
 --       
 * 
 * The output is written to a file and has the following format:
 *  [move1, jump, tick, ...]
 * 
 */
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

struct stat st = {0};

#ifdef __linux__ 

#elif _WIN32
    #include <windows.h>
    #define mkdir(dir, mode) _mkdir(dir)
#endif


#define OVERWRITE 0
#define APPEND 1

const int FILE_NUM = 15;
const int EOF_ENTRY = 13;
const int BUF_LEN = 500000;

const char* FILES[] =  {
    "./result/null",                        /* 0 */
    "./result/metaData.json", 
    "./result/recording.tmcpr",             /* 2 */        
    "./result/resource_pack.zip",         
    "./result/resource_pack_index.json" ,   /* 4 */ 
    "./result/thumb.json",                 
    "./result/visibility",                  /* 6 */ 
    "./result/visibility.json" ,           
    "./result/markers.json",                /* 8 */             
    "./result/asset.zip",  
    "./result/pattern_assets.zip",          /* 10 */               
    "./result/mods.json",
    "./result/experiment_metadata.json",    /* 12 */   
    "./result/end_of_stream.txt",  
    "./result/actions.tmcpr"                /* 14 */           
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
    OVERWRITE,                  /* 12 */    
    APPEND,
    APPEND                      /* 14 */    
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


    
    unsigned int entry, time_stamp, len;
    unsigned int sequence_number=0, prev_sequence_number=0;
    unsigned int prev_entry = 0, prev_len = 0;
    int checked_seq_num = 0;
    bool miss_seq_num = false;
    bool has_EOF = false;
    
    // open all "a" output
    for (int i = 1; i < FILE_NUM; i++)
    {
        if (WRITE_METHODS[i] == APPEND)
        {
            outputs[i] = fopen(FILES[i],"w+");
            if (outputs[i] == NULL)
            {
                printf("    error opening file %s. Abort\n", FILES[i]);
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
        if (has_EOF)
        {
            printf("    detect entry after EOF entry. Abort\n");
            exit(-1);
        }

        dbg_printf("[%d]\n",counter);
        /* entry: first fread in while loop condition */
        entry = get_entry(buf, input);
        
        /* sequence_number */
        fread(buf, 4, 1, input);
        prev_sequence_number = sequence_number; // store old sequence_number
        sequence_number = get_sequence_number(buf, input);
        if (sequence_number < prev_sequence_number)
        {
            printf("WARNING: detect decreasing sequence_number at [%d]entry=%u\n",counter,entry);
            printf("         prev_sequence_number = %u, sequence_number= %u\n",
                     prev_sequence_number, sequence_number);
        }

        /* check miss_seq_num */
        /*  
        if (checked_seq_num == 0 && counter != sequence_number)
        {
            miss_seq_num = true;
            checked_seq_num = true;
            printf("WARNING: missing sequence_number at entry %u: counter=%d,sequence_number=%d\n"
                ,entry,counter,sequence_number);
            printf("Previous: entry=%u,seq_num=%d,len=%u;",
                prev_entry,counter-1,prev_len);
            if (prev_len <= BUF_LEN) printf("data = %s\n",buf);
            else if (backup_buf != NULL) printf("data = %s\n", backup_buf);
            printf("Abort\n");
            exit(1);
        }
        */

        /* check miss_seq_num */ 
        if (counter != sequence_number)
        {
            miss_seq_num = true;
            (void)checked_seq_num;
            printf("WARNING: missing sequence_number at entry %u: counter=%d,sequence_number=%d\n"
                ,entry,counter,sequence_number);
            printf("Previous: entry=%u,seq_num=%d,len=%u;",
                prev_entry,counter-1,prev_len);
            if (prev_len <= BUF_LEN) printf("data = %s\n",buf);
            else if (backup_buf != NULL) printf("data = %s\n", backup_buf);
            counter = sequence_number;
        }

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
                printf("    failed to allocate new buffer, abort\n");
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
        if (0 < entry && entry < FILE_NUM)
        { 
            // case 1: append, directly write
            if (WRITE_METHODS[entry] == APPEND)
            {
                if ((err_check = fwrite(buf, len, 1, outputs[entry])) != 1)
                {
                    printf("    trouble writing to output file[%d] %s\n",
                       entry,FILES[entry] );
                    exit(-1);
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
                    printf("    failed to open the output file %d\n", entry);
                    exit(-1);
                }
                // write and close
                if (fwrite(buf, len, 1, output) != 1)
                {
                    printf("    trouble writing to output\n" );
                    exit(-1);
                }
                fclose(output);
            } 
        }

        else // invalid entry
        {
            printf("corrupted data with entry = %u. Program Abort.\n", entry);
            exit(-1);
        }

        /* check has_EOF */ /* question: no entries afterwards? */
        if (entry == EOF_ENTRY)
        {
            has_EOF = true;
        }

        dbg_printf("file position: %ld\n\n", ftell(input));
        counter++;
        prev_len = len;
        prev_entry = entry;
    }

    printf("SUMMARY: end of parsing.total sequence_number = %u\n",sequence_number);

    // close all "a" output
    for (int i = 1; i < FILE_NUM; i++)
    {
        if (WRITE_METHODS[i]== APPEND)
        {
            err_check = fclose(outputs[i]);
            if (err_check != 0)
            {
                printf("    error closing file %s. Abort\n", FILES[i]);
                exit(-1);
            }
            else
            {
                dbg_printf("successfully close file [%d] %s\n", i, FILES[i]);
            }
        }
    }

    // create stream_meta_data
    meta = fopen("./result/stream_meta_data.json", "w+");
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
    // const char* src_stream = default_src_stream;
    const char* src_stream = NULL;

    // get src_stream
    while ((opt = getopt(argc, argv, "f:")) != -1){
        switch (opt) {
            case 'f':
                src_stream = optarg;
                break;
        }
    }

    if (src_stream == NULL)
    {
        printf("    No src_stream fount. Program abort. Please run ./parse -f <filename>\n");
        exit(-1);
    }
    // display info
    printf("running %s...\n", src_stream);

    // open input file
    input = fopen(src_stream,"r");
    if (input == NULL)
    {
        printf("    Error opening the source stream. Abort.\n");
        exit(-1);
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
