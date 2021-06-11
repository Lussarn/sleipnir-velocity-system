#ifndef JPEGS_H_
#define JPEGS_H_

#include <stdbool.h>
#include <semaphore.h>

#define MAX_JPEGS 10000000

typedef struct _jpegs_t {
   unsigned char *data;
   int32_t data_size;
   int64_t timestamp;
} jpegs_t;

int jpegs_init();
void jpegs_set_data(int32_t position, int64_t timestamp, u_char *data, int32_t data_size);
void jpegs_free_data(int32_t position);
bool jpegs_have_data(int32_t position);
void jpegs_reset();
jpegs_t jpegs_get_by_position(int32_t position);


#endif