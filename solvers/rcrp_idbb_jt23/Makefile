#
# Vendored from https://github.com/jinboszu/rcrp-idbb (main branch, official
# version, GPL-3.0). Upstream builds with CMake; this Makefile mirrors
# main/CMakeLists.txt so the repo build script works without CMake installed.
#
.PHONY: all clean

TARGET     = main-solve
OBJS       = solve.o instance.o state.o lower_bound.o upper_bound.o move.o \
             algorithm.o report.o timer.o
SRCS       := $(OBJS:.o=.c)

CC         ?= gcc
CFLAGS     ?= -O2 -std=c99 -Wall -Wextra

override DEFS += -I.

all:: $(TARGET)

.c.o:
	$(CC) $(CFLAGS) $(DEFS) -c $<

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(DEFS) -o $@ $(OBJS)

clean:
	rm -f $(TARGET) $(OBJS) *~
