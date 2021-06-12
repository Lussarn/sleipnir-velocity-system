#include <stdlib.h>
#include <pthread.h>
#include <stdbool.h>
#include <turbojpeg.h>
#include <log4c.h>

#include "jpegs.h"

static jpegs_t jpegs[MAX_JPEGS];
static pthread_mutex_t jpegs_lock_mutex;
static log4c_category_t* cat;

void jpegs_lock() {
    pthread_mutex_lock(&jpegs_lock_mutex);
}

void jpegs_unlock() {
    pthread_mutex_unlock(&jpegs_lock_mutex);
}

int jpegs_init() {
    int ret;
    cat = log4c_category_get("sleipnir.jpegs");
    log4c_category_debug(cat, "Creating mutex for jpegs lock");
    ret = pthread_mutex_init(&jpegs_lock_mutex, NULL);
    if (ret != 0)
        log4c_category_fatal(cat, "Unable to create mutex for jpegs lock");
    return ret;
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
    jpegs[position].data_size = 0;
    jpegs_unlock();
}

bool jpegs_have_data(int32_t position) {
    jpegs_lock();
    bool ret = jpegs[position].timestamp != 0;
    jpegs_unlock();
    return ret;
}

void jpegs_reset() {
   log4c_category_debug(cat, "Reset jpegs data structure");
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

void jpegs_store(int position, u_char *data, int32_t width, int32_t height, int64_t timestamp) {
   long unsigned int size = 0;
   unsigned char     *jpeg_data = NULL;

   tjhandle jpeg_compressor = tjInitCompress();
   tjCompress2(
      jpeg_compressor,
      data,
      width,
      0,
      height,
      TJPF_GRAY,
      &jpeg_data,
      &size,
      TJSAMP_GRAY,
      80,
      TJFLAG_FASTDCT
   );
   tjDestroy(jpeg_compressor);

   jpegs_set_data(position, timestamp, jpeg_data, size);
}