C = gcc
CFLAGS = -g -Wall -Werror -std=c99
all: parse
bar: 
.PHONY: clean
	$(RM) parse *.o bar *.o 

