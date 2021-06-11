#include <stdlib.h>
#include <pthread.h>

#include "jpegs.h"
#include <stdbool.h>

jpegs_t jpegs[MAX_JPEGS];
pthread_mutex_t jpegs_lock_mutex;

void jpegs_lock() {
    pthread_mutex_lock(&jpegs_lock_mutex);
}

void jpegs_unlock() {
    pthread_mutex_unlock(&jpegs_lock_mutex);
}

int jpegs_init() {
   return pthread_mutex_init(&jpegs_lock_mutex, NULL);
}

void jpegs_set_data(int32_t position, int64_t timestamp, u_char *data, int32_t data_size) {
    jpegs_lock();
    jpegs[position].timestamp = timestamp;
    jpegs[position].data = data;
    jpegs[position].data_size = data_size;
    jpegs_unlock();
}

void jpegs_free_data(int32_t position) {
    jpegs_lock();
    free(jpegs[position].data);
    jpegs[position].data = NULL;
    jpegs[position].timestamp = 0;
    jpegs_unlock();
}

bool jpegs_have_data(int32_t position) {
    jpegs_lock();
    bool ret = jpegs[position].data != NULL;
    jpegs_unlock();
    return ret;
}

void jpegs_reset() {
   jpegs_lock();
   for (int i = 1; i < MAX_JPEGS; i++) {
      if (jpegs[i].data != NULL) free(jpegs[i].data);
      jpegs[i].data = NULL;
      jpegs[i].data_size = 0;
      jpegs[i].timestamp = 0;
   }   
   jpegs_unlock();
}

jpegs_t jpegs_get_by_position(int32_t position) {
    return jpegs[position];
}