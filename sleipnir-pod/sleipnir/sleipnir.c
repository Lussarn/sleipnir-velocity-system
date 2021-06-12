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

// Standard port setting for the camera component
#define MMAL_CAMERA_VIDEO_PORT 1

/// Video render needs at least 2 buffers.
#define VIDEO_OUTPUT_BUFFERS_NUM 2

int mmal_status_to_int(MMAL_STATUS_T status);
static void signal_handler(int signal_number);

static VELOCITY_STATE state;
log4c_category_t* cat;

/**
 *  buffer header callback function for camera control
 *
 *  Callback will dump buffer data to the specific file
 *
 * @param port Pointer to port from which callback originated
 * @param buffer mmal buffer header pointer
 */
static void camera_control_callback(MMAL_PORT_T *port, MMAL_BUFFER_HEADER_T *buffer) {
   if (buffer->cmd == MMAL_EVENT_PARAMETER_CHANGED) {
      MMAL_EVENT_PARAMETER_CHANGED_T *param = (MMAL_EVENT_PARAMETER_CHANGED_T *)buffer->data;
      switch (param->hdr.id) {
         case MMAL_PARAMETER_CAMERA_SETTINGS:
         {
            MMAL_PARAMETER_CAMERA_SETTINGS_T *settings = (MMAL_PARAMETER_CAMERA_SETTINGS_T*)param;
            vcos_log_error("Exposure now %u, analog gain %u/%u, digital gain %u/%u",
			settings->exposure,
                        settings->analog_gain.num, settings->analog_gain.den,
                        settings->digital_gain.num, settings->digital_gain.den);
            vcos_log_error("AWB R=%u/%u, B=%u/%u",
                        settings->awb_red_gain.num, settings->awb_red_gain.den,
                        settings->awb_blue_gain.num, settings->awb_blue_gain.den
                        );
         }
         break;
      }
   }
   else if (buffer->cmd == MMAL_EVENT_ERROR) {
      vcos_log_error("No data received from sensor. Check all connections, including the Sunny one on the camera board");
   }
   else {
      vcos_log_error("Received unexpected camera control callback event, 0x%08x", buffer->cmd);
   }
   mmal_buffer_header_release(buffer);
}

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
static void camera_buffer_callback(MMAL_PORT_T *port, MMAL_BUFFER_HEADER_T *buffer)
{
   MMAL_BUFFER_HEADER_T *new_buffer;
   int i;
   int64_t now_nano;
   int32_t encoder_thread_id;

   struct timespec spec;
   clock_gettime(CLOCK_REALTIME, &spec);

   // Save current timestamp as nanosecond
   now_nano = ((int64_t)spec.tv_sec) * 1000000000 + ((int64_t)spec.tv_nsec);

   // Get the state from port userdata
   VELOCITY_STATE *state = (VELOCITY_STATE *) port->userdata;

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

   // release buffer back to the pool
   mmal_buffer_header_release(buffer);

   // and send one back to the port (if still open)
   if (port->is_enabled) {
      MMAL_STATUS_T status;
      new_buffer = mmal_queue_get(state->camera_pool->queue);

      if (new_buffer) status = mmal_port_send_buffer(port, new_buffer);
      
      if (!new_buffer || status != MMAL_SUCCESS) {
         vcos_log_error("Unable to return a buffer to the camera port");
      }
   }
}


/**
 * Create the camera component, set up its ports
 *
 * @param state Pointer to state control struct
 *
 * @return MMAL_SUCCESS if all OK, something else otherwise
 *
 */
static MMAL_STATUS_T create_camera_component(VELOCITY_STATE *state)
{
   MMAL_COMPONENT_T *camera = 0;
   MMAL_ES_FORMAT_T *format;
   MMAL_PORT_T *video_port = NULL;
   MMAL_STATUS_T status;
   MMAL_POOL_T *pool;

   /* Create the component */
   status = mmal_component_create(MMAL_COMPONENT_DEFAULT_CAMERA, &camera);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("Failed to create camera component");
      goto error;
   }

   /* Select Camera */
   MMAL_PARAMETER_INT32_T camera_num =
      {{MMAL_PARAMETER_CAMERA_NUM, sizeof(camera_num)}, 0};
   status = mmal_port_parameter_set(camera->control, &camera_num.hdr);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("Could not select camera : error %d", status);
      goto error;
   }
   if (!camera->output_num) {
      status = MMAL_ENOSYS;
      vcos_log_error("Camera doesn't have output ports");
      goto error;
   }

   /* Set sensor mode */
   status = mmal_port_parameter_set_uint32(camera->control, MMAL_PARAMETER_CAMERA_CUSTOM_SENSOR_CONFIG, camera_version(state->camera_version).sensor_mode);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("Could not set sensor mode : error %d", status);
      goto error;
   }

   video_port = camera->output[MMAL_CAMERA_VIDEO_PORT];

   // Enable the camera, and tell it its control callback function
   status = mmal_port_enable(camera->control, camera_control_callback);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("Unable to enable control port : error %d", status);
      goto error;
   }

   //  set up the camera configuration
   {
      MMAL_PARAMETER_CAMERA_CONFIG_T cam_config =
      {
         { MMAL_PARAMETER_CAMERA_CONFIG, sizeof(cam_config) },
         .max_stills_w = camera_version(state->camera_version).capture_width,
         .max_stills_h = camera_version(state->camera_version).capture_height,
         .stills_yuv422 = 0,
         .one_shot_stills = 0,
         .max_preview_video_w = camera_version(state->camera_version).capture_width,
         .max_preview_video_h = camera_version(state->camera_version).capture_height,
         .num_preview_video_frames = 3,
         .stills_capture_circular_buffer_height = 0,
         .fast_preview_resume = 0,
         .use_stc_timestamp = MMAL_PARAM_TIMESTAMP_MODE_RAW_STC
      };
      mmal_port_parameter_set(camera->control, &cam_config.hdr);
   }

   // Now set up the port formats
   // Set the encode format on the video  port
   format = video_port->format;
   format->encoding_variant = MMAL_ENCODING_I420;

   if(state->camera_parameters.shutter_speed > 6000000) {
        MMAL_PARAMETER_FPS_RANGE_T fps_range = {{MMAL_PARAMETER_FPS_RANGE, sizeof(fps_range)},
                                                     { 50, 1000 }, {166, 1000}};
        mmal_port_parameter_set(video_port, &fps_range.hdr);
   }
   else if(state->camera_parameters.shutter_speed > 1000000) {
        MMAL_PARAMETER_FPS_RANGE_T fps_range = {{MMAL_PARAMETER_FPS_RANGE, sizeof(fps_range)},
                                                     { 167, 1000 }, {999, 1000}};
        mmal_port_parameter_set(video_port, &fps_range.hdr);
   }

   format->encoding = MMAL_ENCODING_I420;
   format->encoding_variant = MMAL_ENCODING_I420;

   format->es->video.width = VCOS_ALIGN_UP(camera_version(state->camera_version).capture_width, 32);
   format->es->video.height = VCOS_ALIGN_UP(camera_version(state->camera_version).capture_height, 16);
   format->es->video.crop.x = 0;
   format->es->video.crop.y = 0;
   format->es->video.crop.width = camera_version(state->camera_version).capture_width;
   format->es->video.crop.height = camera_version(state->camera_version).capture_height;
   format->es->video.frame_rate.num = camera_version(state->camera_version).framerate;
   format->es->video.frame_rate.den = 1;

   status = mmal_port_format_commit(video_port);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("camera video format couldn't be set");
      goto error;
   }

   // Ensure there are enough buffers to avoid dropping frames
   if (video_port->buffer_num < VIDEO_OUTPUT_BUFFERS_NUM)
      video_port->buffer_num = VIDEO_OUTPUT_BUFFERS_NUM;

   /* Enable component */
   status = mmal_component_enable(camera);
   if (status != MMAL_SUCCESS) {
      vcos_log_error("camera component couldn't be enabled");
      goto error;
   }

   raspicamcontrol_set_all_parameters(camera, &state->camera_parameters);
   mmal_port_parameter_set_boolean(video_port, MMAL_PARAMETER_ZERO_COPY, MMAL_TRUE);

   /* Create pool of buffer headers for the output port to consume */
   pool = mmal_port_pool_create(video_port, video_port->buffer_num, video_port->buffer_size);
   if (!pool) {
      vcos_log_error("Failed to create buffer header pool for camera video port %s", video_port->name);
   }

   state->camera_pool = pool;
   state->camera_component = camera;

   if (state->verbose) {
      fprintf(stderr, "Camera component done\n");
   }

   return status;

error:
   if (camera) mmal_component_destroy(camera);
   return status;
}

/**
 * Destroy the camera component
 *
 * @param state Pointer to state control struct
 *
 */
static void destroy_camera_component(VELOCITY_STATE *state) {
   if (state->camera_component) {
      mmal_component_destroy(state->camera_component);
      state->camera_component = NULL;
   }
}

/**
 * Checks if specified port is valid and enabled, then disables it
 *
 * @param port  Pointer the port
 *
 */
static void check_disable_port(MMAL_PORT_T *port)
{
   if (port && port->is_enabled)
      mmal_port_disable(port);
}

/**
 * Handler for sigint signals
 *
 * @param signal_number ID of incoming signal.
 *
 */
static void signal_handler_interrupt(int signal_number)
{
   state.running = false;
   log4c_category_info(cat, "Exiting program");
}

/**
 * main
 */
int main(int argc, const char **argv) {
   pthread_attr_t tattr;
   static int rc;
   static int ret;

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

   velocity_state_default(&state);

   // Do we have any parameters
   if (argc == 1) {
      fprintf(stdout, "Sleipnir %s\n\n", VERSION_STRING);
      exit(EX_USAGE);
   }

   // Parse the command line and put options in to our status structure
   if (velocity_state_parse_cmdline(argc, argv, &state)) {
      status = -1;
      exit(EX_USAGE);
   }

   // Initialize encoder
   encoder_init(&state);

   // Initialize http IO
   http_io_init(&state);


   if ((status = create_camera_component(&state)) != MMAL_SUCCESS) {
      vcos_log_error("%s: Failed to create camera component", __func__);
      exit_code = EX_SOFTWARE;
   } else {
      camera_video_port   = state.camera_component->output[MMAL_CAMERA_VIDEO_PORT];

      camera_video_port->userdata = (struct MMAL_PORT_USERDATA_T *)&state;
      // Enable the camera video port and tell it its callback function
      status = mmal_port_enable(camera_video_port, camera_buffer_callback);

      if (status != MMAL_SUCCESS) {
         vcos_log_error("Failed to setup camera output");
         goto error;
      }

      // Send all the buffers to the camera video port
      {
         int num = mmal_queue_length(state.camera_pool->queue);
         int q;
         for (q=0;q<num;q++) {
            MMAL_BUFFER_HEADER_T *buffer = mmal_queue_get(state.camera_pool->queue);

            if (!buffer) {
               vcos_log_error("Unable to get a required buffer %d from pool queue", q);
            }

            if (mmal_port_send_buffer(camera_video_port, buffer)!= MMAL_SUCCESS) {
               vcos_log_error("Unable to send a buffer to camera video port (%d)", q);
            }
         }
      }

      mmal_port_parameter_set_boolean(camera_video_port, MMAL_PARAMETER_CAPTURE, true);
      while (state.running) {
         usleep(10000);
      }

error:
      mmal_status_to_int(status);


      log4c_category_info(cat, "Closing down");
      destroy_camera_component(&state);
      log4c_category_info(cat, "Close down completed, all components disconnected, disabled and destroyed");
   }

   if (status != MMAL_SUCCESS) {
      raspicamcontrol_check_configuration(128);
   }

   return exit_code;
}
