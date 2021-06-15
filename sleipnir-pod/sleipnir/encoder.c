#define _GNU_SOURCE
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <stdbool.h>
#include <log4c.h>

#include "interface/mmal/mmal.h"
#include "interface/mmal/mmal_buffer.h"

#include "velocity_state.h"
#include "encoder.h"
#include "jpegs.h"
#include "fit_image.h"

static pthread_t encoder_threads[ENCODER_MAX_THREADS];
static u_char *yuv_image_buffers[ENCODER_MAX_THREADS];
static log4c_category_t* cat;

/*
 * Encoder threads
 */
void *encoder_thread_func(void *arg) {
    char *buffer;
    char *new_buffer;

    encoder_data_t *data = (encoder_data_t *)arg;
    while(data->state->running) {
        pthread_mutex_lock(&encoder_data_lock[data->thread_id]);
        if (data->frame_number != 0) {
            pthread_mutex_unlock(&encoder_data_lock[data->thread_id]);

            buffer = data->yuv_buffer;

            new_buffer = fit_image(
                        buffer,
                        camera_version(data->state->camera_version).capture_width,
                        camera_version(data->state->camera_version).capture_height,
                        camera_version(data->state->camera_version).roi_left,
                        camera_version(data->state->camera_version).roi_top,
                        camera_version(data->state->camera_version).roi_width,
                        camera_version(data->state->camera_version).roi_height,
                        camera_version(data->state->camera_version).rotate,
                        camera_version(data->state->camera_version).final_width,
                        camera_version(data->state->camera_version).final_height
                        );

            jpegs_store(data->frame_number,
                        new_buffer, 
                        camera_version(data->state->camera_version).final_width, 
                        camera_version(data->state->camera_version).final_height,  
                        data->timestamp);

            // If a new buffer is allocated by fit_image we need to free it
            if (buffer != new_buffer) free(new_buffer);

            // Lock while writing frame_number since this is the one we check
            pthread_mutex_lock(&encoder_data_lock[data->thread_id]);
            data->frame_number = 0;
        }
        pthread_mutex_unlock(&encoder_data_lock[data->thread_id]);
        usleep(1000);
    }
    pthread_exit(NULL);
}

void encoder_init(VELOCITY_STATE *state) {
    int i;
    pthread_attr_t tattr;

    cat = log4c_category_get("sleipnir.encoder");
    log4c_category_debug(cat, "Creating %d threads and mutexes for encoders locks", ENCODER_MAX_THREADS);

    for (i = 0; i < ENCODER_MAX_THREADS; i++) {
        pthread_mutex_init(&encoder_data_lock[i], NULL);

        /* v1 = 230400 && v2 = 1382400 */
        /* Allocate enough for v2, ugly fix later */
        yuv_image_buffers[i] = malloc(1382400);

        encoder_threads[i] = 0;
        encoder_data[i].thread_id = i;
        encoder_data[i].frame_number = 0;
        encoder_data[i].yuv_buffer = NULL;
        encoder_data[i].state = state;

        pthread_attr_init(&tattr);
        pthread_attr_setschedpolicy(&tattr, SCHED_BATCH);
        pthread_attr_setinheritsched(&tattr, PTHREAD_EXPLICIT_SCHED);
        pthread_create(&encoder_threads[i], &tattr, encoder_thread_func, &encoder_data[i]);
        pthread_attr_destroy(&tattr);
    }
}

int32_t encoder_get_free_thread_id() {
    int i;
    static int thread_id = 0;

    /* Round robin the threads for minimal locking */
    for (i = 0; i < ENCODER_MAX_THREADS; i++) {
        if (++thread_id >= ENCODER_MAX_THREADS) thread_id = 0;
        pthread_mutex_lock(&encoder_data_lock[thread_id]);
        if (encoder_data[thread_id].frame_number == 0) {
            pthread_mutex_unlock(&encoder_data_lock[thread_id]);
            return thread_id;
        }
        pthread_mutex_unlock(&encoder_data_lock[thread_id]);
    }
    return -1;
}

void encoder_copy_mmal_buffer_to_image_buffer(int32_t encoder_thread_id, MMAL_BUFFER_HEADER_T *buffer) {
    mmal_buffer_header_mem_lock(buffer);
    memcpy(yuv_image_buffers[encoder_thread_id], buffer->data, buffer->length);
    mmal_buffer_header_mem_unlock(buffer);
}

void encoder_data_set(VELOCITY_STATE *state, int32_t encoder_thread_id, MMAL_BUFFER_HEADER_T *buffer, int64_t timestamp) {
    encoder_copy_mmal_buffer_to_image_buffer(encoder_thread_id, buffer);

    pthread_mutex_lock(&encoder_data_lock[encoder_thread_id]);
    encoder_data[encoder_thread_id].timestamp = timestamp;
    encoder_data[encoder_thread_id].yuv_buffer = yuv_image_buffers[encoder_thread_id];
    encoder_data[encoder_thread_id].frame_number = state->camera_position;
    encoder_data[encoder_thread_id].state = state;
    pthread_mutex_unlock(&encoder_data_lock[encoder_thread_id]);    
}
