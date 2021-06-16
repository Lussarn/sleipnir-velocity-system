#define _GNU_SOURCE
#define VERSION_STRING "v0.3"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <memory.h>
#include <sysexits.h>
#include <curl/curl.h>
#include <stdbool.h>
#include <semaphore.h>

#include <log4c.h>
#include <popt.h>

#include "bcm_host.h"
#include "interface/vcos/vcos.h"

#include "interface/mmal/mmal.h"
#include "interface/mmal/mmal_logging.h"
#include "interface/mmal/mmal_buffer.h"
#include "interface/mmal/util/mmal_util.h"
#include "interface/mmal/util/mmal_util_params.h"
#include "interface/mmal/util/mmal_default_components.h"
#include "interface/mmal/util/mmal_connection.h"

#include "velocity_state.h"
#include "RaspiCamControl.h"
#include "RaspiCLI.h"
#include "jpegs.h"
#include "encoder.h"
#include "http_io.h"
#include "camera.h"

int mmal_status_to_int(MMAL_STATUS_T status);
static void signal_handler(int signal_number);
static void parse_cmdline(int argc, const char **argv, VELOCITY_STATE *state);

static VELOCITY_STATE state;
log4c_category_t* cat;

#define TIMESTAMPS_BUFFER_SIZE 200
int64_t circularTimestamp[TIMESTAMPS_BUFFER_SIZE];
int64_t last_timestamp_nano = 0;
int64_t lastPts = 0;
int32_t numDrops = 0;

/**
 *  buffer header callback function for camera
 *
 *  Callback will dump buffer data to internal buffer
 *
 * @param port Pointer to port from which callback originated
 * @param buffer mmal buffer header pointer
 */
static void picture_callback(VELOCITY_STATE *state, MMAL_BUFFER_HEADER_T *buffer)
{
   int i;
   int64_t now_nano;
   int32_t encoder_thread_id;

   struct timespec spec;
   clock_gettime(CLOCK_REALTIME, &spec);

   // Save current timestamp as nanosecond
   now_nano = ((int64_t)spec.tv_sec) * 1000000000 + ((int64_t)spec.tv_nsec);

   if (state) {
      if (buffer->length) {

         // Update the circular buffer with frame timestamps
         for (i = TIMESTAMPS_BUFFER_SIZE - 2; i >= 0; i--) {
            circularTimestamp[i + 1] = circularTimestamp[i];
         }
         circularTimestamp[0] = now_nano;

         // Average the frametimes to get the true framerate
         int64_t averageFrameDuration = 0;
         for (i = 0; i < TIMESTAMPS_BUFFER_SIZE - 1; i++) {
            if (circularTimestamp[i + 1] == 0) goto out;
            averageFrameDuration += circularTimestamp[i] - circularTimestamp[i + 1];
         }
         averageFrameDuration /= (TIMESTAMPS_BUFFER_SIZE - 1);

         if (last_timestamp_nano == 0) last_timestamp_nano = now_nano;

         int64_t timestamp_nano;
         // Draw timestamp closer to now a bit (smoothing)
         if (now_nano - last_timestamp_nano > averageFrameDuration) {
            timestamp_nano = last_timestamp_nano + averageFrameDuration + (averageFrameDuration / 15);
         } else {
            timestamp_nano = last_timestamp_nano + averageFrameDuration - (averageFrameDuration / 15);
         }

         // JITTER DEBUG
         if (false)
            printf("timestamp: %" PRId64 " pts: %" PRIu64 " diff: %" PRId64 " frametime: %" PRId64 "\n",
                     timestamp_nano / 1000000,
                     buffer->pts / 1000,
                     (timestamp_nano / 1000 - buffer->pts) / 1000,
                     (buffer->pts - lastPts) / 1000);

         if ((buffer->pts - lastPts) > (averageFrameDuration + (averageFrameDuration / 2)) / 1000) {
            char timeBuf[256];
            struct tm t;
            localtime_r(&(spec.tv_sec), &t);
            strftime(timeBuf, 256, "%F %T", &t);
            numDrops++;
            log4c_category_warn(cat, "Frame drop number %d", numDrops);
            timestamp_nano += averageFrameDuration;
         }
         last_timestamp_nano = timestamp_nano;

         if (state->post_frames) {
            encoder_thread_id = encoder_get_free_thread_id();

            if (encoder_thread_id == -1) {
                  log4c_category_warn(cat, "Running out of encoder threads");
                  goto out;
            }

            encoder_data_set(
               state,
               encoder_thread_id,
               buffer,
               timestamp_nano / 1000000
            );

            state->camera_position++;
         }
      }
   }
   else
   {
      vcos_log_error("Received a camera buffer callback with no state");
   }
out:
   lastPts = buffer->pts;
}

static void signal_handler_interrupt(int signal_number) {
   state.running = false;
   log4c_category_info(cat, "Exiting program");
}

int main(int argc, const char **argv) {
   pthread_attr_t tattr;
   static int rc;
   static int ret;

   // Parse the command line and put options in to our status structure
   velocity_state_default(&state);
   parse_cmdline(argc, argv, &state);

   state.running = true;

   // Initializing logging system
   log4c_init();
   cat = log4c_category_get("sleipnir.pod"); 

   log4c_category_info(cat, "Sleipnir pod starting up...");

   // Initialize jpegs structure
   if (jpegs_init() != 0) {
      log4c_category_error(cat, "Error initializing jpegs...");
      return EX_SOFTWARE;
   }

   // Capture CTRL-C
   signal(SIGINT, signal_handler_interrupt);

   int exit_code = EX_OK;

   MMAL_STATUS_T status = MMAL_SUCCESS;
   MMAL_PORT_T *camera_video_port = NULL;

   bcm_host_init();
   vcos_log_register("Sleipnir", VCOS_LOG_CATEGORY);


   // Initialize encoder
   encoder_init(&state);

   // Initialize http IO
   http_io_init(&state);


   if ((status = camera_create_component(&state, picture_callback)) != MMAL_SUCCESS) {
      vcos_log_error("%s: Failed to create camera component", __func__);
      exit_code = EX_SOFTWARE;
   } else {
      while (state.running) {
         usleep(10000);
      }

error:
      mmal_status_to_int(status);


      log4c_category_info(cat, "Closing down");
      camera_destroy_component(&state);
      log4c_category_info(cat, "Close down completed, all components disconnected, disabled and destroyed");
   }

   if (status != MMAL_SUCCESS) {
      raspicamcontrol_check_configuration(128);
   }

   return exit_code;
}

static void parse_cmdline(int argc, const char **argv, VELOCITY_STATE *state) {
   int c;
   poptContext optCon;

   struct poptOption optionsTable[] = {
        { "url", 'u', POPT_ARG_STRING, &state->url, 'u',
        "URL to base station including port" },

        { "cam", 'c', POPT_ARG_STRING, &state->identifier, 'c',
        "Camera pod left (cam1) or right (cam2)" },

        { "camversion", 'r', POPT_ARG_INT, &state->camera_version, 'r',
        "Camera version (13, 21)" },

        POPT_AUTOHELP
        POPT_TABLEEND
   };

   optCon =  poptGetContext(NULL, argc, argv, optionsTable, 0);

   while ((c = poptGetNextOpt(optCon)) > 0) ;

   if (c == POPT_ERROR_BADOPT) {
      printf("%s %s\n", poptStrerror(c), poptBadOption(optCon, 0));
      exit(1);
   } else if (c < -1) {
      printf("%s\n", poptStrerror(c));
      exit(1);
   }

   // Sanity check url
   if (state->url == NULL) {
      printf("need url\n");
      exit(1);
   }

   // Sanity check cam
   if (state->identifier == NULL || (strcmp(state->identifier, "cam1") != 0 && strcmp(state->identifier, "cam2") != 0)) {
      printf("bad cammera supplied\n");
      exit(1);
   }

   // Sanity check camera version
   if (state->camera_version == 13)
      state->camera_version = CAMERA_VERSION_13;
   else if (state->camera_version == 21)
      state->camera_version = CAMERA_VERSION_21;
   else {
      printf("bad camera version\n");
      exit(1);
   }
}