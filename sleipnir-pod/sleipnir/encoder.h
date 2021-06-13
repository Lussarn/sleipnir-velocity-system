#ifndef ENCODER_H_
#define ENCODER_H_

#include <semaphore.h>

#include "interface/mmal/mmal.h"
#include "interface/mmal/mmal_buffer.h"

#include "velocity_state.h"

#define ENCODER_MAX_THREADS 8


typedef struct _encoder_data_t {
   int thread_id;
   int frame_number;
   int64_t timestamp;
   u_char *yuv_buffer;
   VELOCITY_STATE *state;
} encoder_data_t;
encoder_data_t encoder_data[ENCODER_MAX_THREADS];

pthread_mutex_t encoder_data_lock[ENCODER_MAX_THREADS];

void encoder_init(VELOCITY_STATE *velocity_state);
int32_t encoder_get_free_thread_id();

void encoder_data_set(VELOCITY_STATE *state, int32_t encoder_thread_id, MMAL_BUFFER_HEADER_T *buffer, int64_t timestamp);

#endif