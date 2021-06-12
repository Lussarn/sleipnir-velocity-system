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

#include "RaspiCamControl.h"
#include "RaspiCLI.h"
#include "jpegs.h"
#include "encoder.h"


// Standard port setting for the camera component
#define MMAL_CAMERA_VIDEO_PORT 1

// Video format information
// 0 implies variable
#define VIDEO_FRAME_RATE_NUM 30
#define VIDEO_FRAME_RATE_DEN 1

/// Video render needs at least 2 buffers.
#define VIDEO_OUTPUT_BUFFERS_NUM 2

/// Interval at which we check for an failure abort during capture
const int ABORT_INTERVAL = 100; // ms

int mmal_status_to_int(MMAL_STATUS_T status);
static void signal_handler(int signal_number);

/** Structure containing all state information for the current run
 */
typedef struct VELOCITY_STATE_S
{
   bool running;                       /// still running
   int timeout;                        /// Time taken before frame is grabbed and app then shuts down. Units are milliseconds
   int width;                          /// Requested width of image
   int height;                         /// requested height of image
   int framerate;                      /// Requested frame rate (fps)
   char *identifier;                   /// identifier for this camera
   char *url;                          /// Url for posting data
   int verbose;                        /// !0 if want detailed run information

   RASPICAM_CAMERA_PARAMETERS camera_parameters; /// Camera setup parameters
   MMAL_COMPONENT_T *camera_component;    /// Pointer to the camera component
   MMAL_POOL_T *camera_pool;            /// Pointer to the pool of buffers used by camera video port

   int settings;                        /// Request settings from the camera
   int sensor_mode;                     /// Sensor mode. 0=auto. Check docs/forum for modes selected by other values.
} VELOCITY_STATE;
static VELOCITY_STATE state;

/// Command ID's and Structure defining our command line options
#define CommandWidth        1
#define CommandHeight       2
#define CommandFramerate    7
#define CommandSettings     13
#define CommandSensorMode   14
#define CommandIdentifier   15
#define CommandUrl          16

static COMMAND_LIST cmdline_commands[] =
{
   { CommandWidth,         "-width",      "w",  "Set image width <size>. Default 1920", 1 },
   { CommandHeight,        "-height",     "h",  "Set image height <size>. Default 1080", 1 },
   { CommandFramerate,     "-framerate",  "fps","Specify the frames per second to record", 1},
   { CommandSettings,      "-settings",   "set","Retrieve camera settings and write to stdout", 0},
   { CommandSensorMode,    "-mode",       "md", "Force sensor mode. 0=auto. See docs for other modes available", 1},
   { CommandIdentifier,    "-identifier", "id", "Command identifer for this camera", 1},
   { CommandUrl,           "-url",        "u",  "Url to post data to", 1},
};

static int cmdline_commands_size = sizeof(cmdline_commands) / sizeof(cmdline_commands[0]);
static int save_frames = 0;

static pthread_t io_thread;

static int camera_position = 0;

log4c_category_t* cat;

size_t curl_callback(void *ptr, size_t size, size_t nmemb, void *chunk){
   size_t realsize = size * nmemb;
   snprintf(chunk, 255, "%s", (char *)ptr);
   return realsize;
}

int http_post(CURL *curl, char *url, void *post_data, uint32_t post_size, void *answer) {
   CURLcode res = 0;
   char chunk[256];
   struct curl_slist *headerlist=NULL;
   static const char buf[] = "Expect:";

   headerlist = curl_slist_append(headerlist, buf);
   curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headerlist);
   curl_easy_setopt(curl, CURLOPT_URL, url);
   curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data);
   curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, &curl_callback);
   curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
   curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, post_size);
   res = curl_easy_perform(curl);
   if(res != CURLE_OK) {
       fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
   } else {
      if (strncmp(chunk, "OK", 2) == 0) {
         strncpy(answer, chunk + 3, 253);
      }
   }
   curl_slist_free_all (headerlist);
   return res;
}


/**
 * IO THREAD 
 * globals used: state, save_frames, camera_position,
 */
void *thread_io_func(void *arg) {
   static char post_data[300000];
   char answer[256];
   CURL *curl;
   CURLcode res;
   VELOCITY_STATE *state = (VELOCITY_STATE *) arg;
   char url[256];
   int cx;

   curl = curl_easy_init();

   while (state->running) {
      save_frames = 0;
      jpegs_reset();
      camera_position = 0;
      while(state->running) {
         cx = snprintf(url, 256, "%s?action=startcamera&cam=%s", state->url, state->identifier);
         if (cx < 0 || cx >= 256) {
            printf("Error snprintf in thread_io_func");
         }
         memset(answer,0,strlen(answer));  // Is this necesary?
         res = http_post(curl, url, "", 0, &answer);
         if (res != CURLE_OK) {
            usleep(100000);
            continue;
         }
         if (strcmp(answer, "START") == 0) break;
         usleep(100000);
      }

      save_frames = 1;
      int frame_number = 1;
      while(true) {
         if (!state->running) break;
         while (true) {
            if (jpegs_have_data(frame_number)) break;
            usleep(100);
         }

         cx = snprintf(url, 256, "%s?action=uploadframe&cam=%s&position=%d&timestamp=%d",
            state->url,
            state->identifier,
            frame_number,
            jpegs_get_by_position(frame_number).timestamp);
            if (cx < 0 || cx >= 256) {
               printf("Error snprintf in thread_io_func");
            }
         memset(answer,0,strlen(answer)); // Is this necesary?
         res = http_post(curl, url, jpegs_get_by_position(frame_number).data, jpegs_get_by_position(frame_number).data_size, &answer);
         if (res != CURLE_OK) {
            break;
         }

         if (strcmp(answer, "STOP") == 0) {
            save_frames = 0;
            if (frame_number > (camera_position - 50)) break;
         }

         jpegs_free_data(frame_number);

         frame_number++;
      }
      // Wait for encoder threads
      sleep(1);
   }

   curl_easy_cleanup(curl);
   pthread_exit(NULL);
}


/**
 * Assign a default set of parameters to the state passed in
 *
 * @param state Pointer to state structure to assign defaults to
 */
static void default_status(VELOCITY_STATE *state)
{
   if (!state)
   {
      vcos_assert(0);
      return;
   }

   // Default everything to zero
   memset(state, 0, sizeof(VELOCITY_STATE));

   // Now set anything non-zero
   state->running = true;
   state->timeout = 5000;     // 5s delay before take image
   state->width = 320;
   state->height = 480;
   state->framerate = VIDEO_FRAME_RATE_NUM;

//   state->bCapturing = 0;

   state->settings = 0;
   state->sensor_mode = 0;

   // Set up the camera_parameters to default
   raspicamcontrol_set_defaults(&state->camera_parameters);
}

/**
 * Parse the incoming command line and put resulting parameters in to the state
 *
 * @param argc Number of arguments in command line
 * @param argv Array of pointers to strings from command line
 * @param state Pointer to state structure to assign any discovered parameters to
 * @return Non-0 if failed for some reason, 0 otherwise
 */
static int parse_cmdline(int argc, const char **argv, VELOCITY_STATE *state)
{
   // Parse the command line arguments.
   // We are looking for --<something> or -<abreviation of something>

   int valid = 1;
   int i;

   for (i = 1; i < argc && valid; i++)
   {
      int command_id, num_parameters;

      if (!argv[i]) {
         continue;
      }

      if (argv[i][0] != '-')
      {
         valid = 0;
         continue;
      }

      // Assume parameter is valid until proven otherwise
      valid = 1;

      command_id = raspicli_get_command_id(cmdline_commands, cmdline_commands_size, &argv[i][1], &num_parameters);

      // If we found a command but are missing a parameter, continue (and we will drop out of the loop)
      if (command_id != -1 && num_parameters > 0 && (i + 1 >= argc)) {
         continue;
      }

      //  We are now dealing with a command line option
      switch (command_id) {

      case CommandWidth: // Width > 0
         if (sscanf(argv[i + 1], "%u", &state->width) != 1)
            valid = 0;
         else
            i++;
         break;

      case CommandHeight: // Height > 0
         if (sscanf(argv[i + 1], "%u", &state->height) != 1)
            valid = 0;
         else
            i++;
         break;

      case CommandIdentifier:  // cam1, cam2
      {
         int len = strlen(argv[i + 1]);
         if (len)
         {
            state->identifier = malloc(len + 1);
            if (state->identifier)
               strncpy(state->identifier, argv[i + 1], len+1);
            i++;
         }
         else
            valid = 0;
         break;
      }

      case CommandUrl:
      {
         int len = strlen(argv[i + 1]);
         if (len)
         {
            state->url = malloc(len + 1);
            if (state->url)
               strncpy(state->url, argv[i + 1], len+1);
            i++;
         }
         else
            valid = 0;
         break;
      }


      case CommandFramerate: // fps to record
      {
         if (sscanf(argv[i + 1], "%u", &state->framerate) == 1)
         {
            // TODO : What limits do we need for fps 1 - 30 - 120??
            i++;
         }
         else
            valid = 0;
         break;
      }

      case CommandSettings:
         state->settings = 1;
         break;

      case CommandSensorMode:
      {
         if (sscanf(argv[i + 1], "%u", &state->sensor_mode) == 1)
         {
            i++;
         }
         else
            valid = 0;
         break;
      }

      default:
      {
         // Try parsing for any image specific parameters
         // result indicates how many parameters were used up, 0,1,2
         // but we adjust by -1 as we have used one already
         const char *second_arg = (i + 1 < argc) ? argv[i + 1] : NULL;
         int parms_used = (raspicamcontrol_parse_cmdline(&state->camera_parameters, &argv[i][1], second_arg));

         // If no parms were used, this must be a bad parameters
         if (!parms_used)
            valid = 0;
         else
            i += parms_used - 1;

         break;
      }
      }
   }

   if (!valid)
   {
      fprintf(stderr, "Invalid command line option (%s)\n", argv[i-1]);
      return 1;
   }

   return 0;
}

/**
 *  buffer header callback function for camera control
 *
 *  Callback will dump buffer data to the specific file
 *
 * @param port Pointer to port from which callback originated
 * @param buffer mmal buffer header pointer
 */
static void camera_control_callback(MMAL_PORT_T *port, MMAL_BUFFER_HEADER_T *buffer)
{
   if (buffer->cmd == MMAL_EVENT_PARAMETER_CHANGED)
   {
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
   else if (buffer->cmd == MMAL_EVENT_ERROR)
   {
      vcos_log_error("No data received from sensor. Check all connections, including the Sunny one on the camera board");
   }
   else
   {
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

         if (save_frames == 1) {
            encoder_thread_id = encoder_get_free_thread_id();

            if (encoder_thread_id == -1) {
                  log4c_category_warn(cat, "Running out of encoder threads");
                  goto out;
            }

            encoder_data_set(
               encoder_thread_id,
               buffer,
               state->width,
               state->height,
               camera_position,
               timestamp_nano / 1000000
            );

            camera_position++;
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
   if (port->is_enabled)
   {
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

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("Failed to create camera component");
      goto error;
   }

   MMAL_PARAMETER_INT32_T camera_num =
      {{MMAL_PARAMETER_CAMERA_NUM, sizeof(camera_num)}, 0};

   status = mmal_port_parameter_set(camera->control, &camera_num.hdr);

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("Could not select camera : error %d", status);
      goto error;
   }

   if (!camera->output_num)
   {
      status = MMAL_ENOSYS;
      vcos_log_error("Camera doesn't have output ports");
      goto error;
   }

   status = mmal_port_parameter_set_uint32(camera->control, MMAL_PARAMETER_CAMERA_CUSTOM_SENSOR_CONFIG, state->sensor_mode);

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("Could not set sensor mode : error %d", status);
      goto error;
   }

   video_port = camera->output[MMAL_CAMERA_VIDEO_PORT];

   if (state->settings)
   {
      MMAL_PARAMETER_CHANGE_EVENT_REQUEST_T change_event_request =
         {{MMAL_PARAMETER_CHANGE_EVENT_REQUEST, sizeof(MMAL_PARAMETER_CHANGE_EVENT_REQUEST_T)},
          MMAL_PARAMETER_CAMERA_SETTINGS, 1};

      status = mmal_port_parameter_set(camera->control, &change_event_request.hdr);
      if ( status != MMAL_SUCCESS )
      {
         vcos_log_error("No camera settings events");
      }
   }

   // Enable the camera, and tell it its control callback function
   status = mmal_port_enable(camera->control, camera_control_callback);

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("Unable to enable control port : error %d", status);
      goto error;
   }

   //  set up the camera configuration
   {
      MMAL_PARAMETER_CAMERA_CONFIG_T cam_config =
      {
         { MMAL_PARAMETER_CAMERA_CONFIG, sizeof(cam_config) },
         .max_stills_w = state->width,
         .max_stills_h = state->height,
         .stills_yuv422 = 0,
         .one_shot_stills = 0,
         .max_preview_video_w = state->width,
         .max_preview_video_h = state->height,
         .num_preview_video_frames = 3,
         .stills_capture_circular_buffer_height = 0,
         .fast_preview_resume = 0,
         .use_stc_timestamp = MMAL_PARAM_TIMESTAMP_MODE_RAW_STC
      };
      mmal_port_parameter_set(camera->control, &cam_config.hdr);
   }

   // Now set up the port formats


   //enable dynamic framerate if necessary
   if (state->camera_parameters.shutter_speed)
   {
      if (state->framerate > 1000000./state->camera_parameters.shutter_speed)
      {
         state->framerate=0;
         if (state->verbose) {
            fprintf(stderr, "Enable dynamic frame rate to fulfil shutter speed requirement\n");
         }
      }
   }

   // Set the encode format on the video  port
   format = video_port->format;
   format->encoding_variant = MMAL_ENCODING_I420;

   if(state->camera_parameters.shutter_speed > 6000000)
   {
        MMAL_PARAMETER_FPS_RANGE_T fps_range = {{MMAL_PARAMETER_FPS_RANGE, sizeof(fps_range)},
                                                     { 50, 1000 }, {166, 1000}};
        mmal_port_parameter_set(video_port, &fps_range.hdr);
   }
   else if(state->camera_parameters.shutter_speed > 1000000)
   {
        MMAL_PARAMETER_FPS_RANGE_T fps_range = {{MMAL_PARAMETER_FPS_RANGE, sizeof(fps_range)},
                                                     { 167, 1000 }, {999, 1000}};
        mmal_port_parameter_set(video_port, &fps_range.hdr);
   }

   format->encoding = MMAL_ENCODING_I420;
   format->encoding_variant = MMAL_ENCODING_I420;

   format->es->video.width = VCOS_ALIGN_UP(state->width, 32);
   format->es->video.height = VCOS_ALIGN_UP(state->height, 16);
   format->es->video.crop.x = 0;
   format->es->video.crop.y = 0;
   format->es->video.crop.width = state->width;
   format->es->video.crop.height = state->height;
   format->es->video.frame_rate.num = state->framerate;
   format->es->video.frame_rate.den = VIDEO_FRAME_RATE_DEN;

   status = mmal_port_format_commit(video_port);

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("camera video format couldn't be set");
      goto error;
   }

   // Ensure there are enough buffers to avoid dropping frames
   if (video_port->buffer_num < VIDEO_OUTPUT_BUFFERS_NUM)
      video_port->buffer_num = VIDEO_OUTPUT_BUFFERS_NUM;

   /* Enable component */
   status = mmal_component_enable(camera);

   if (status != MMAL_SUCCESS)
   {
      vcos_log_error("camera component couldn't be enabled");
      goto error;
   }

   raspicamcontrol_set_all_parameters(camera, &state->camera_parameters);
//   mmal_port_parameter_set_boolean(video_port, MMAL_PARAMETER_ZERO_COPY, MMAL_TRUE);

   /* Create pool of buffer headers for the output port to consume */
   pool = mmal_port_pool_create(video_port, video_port->buffer_num, video_port->buffer_size);

   if (!pool)
   {
      vcos_log_error("Failed to create buffer header pool for camera video port %s", video_port->name);
   }

   state->camera_pool = pool;
   state->camera_component = camera;

   if (state->verbose) {
      fprintf(stderr, "Camera component done\n");
   }

   return status;

error:

   if (camera)
      mmal_component_destroy(camera);

   return status;
}

/**
 * Destroy the camera component
 *
 * @param state Pointer to state control struct
 *
 */
static void destroy_camera_component(VELOCITY_STATE *state)
{
   if (state->camera_component)
   {
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
//   sleep(2);
   // Going to abort on all other signals
//   exit(0);
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

   default_status(&state);

   // Initialize encoder
   encoder_init(&state.running);

   // Do we have any parameters
   if (argc == 1) {
      fprintf(stdout, "Sleipnir %s\n\n", VERSION_STRING);
      exit(EX_USAGE);
   }

   // Parse the command line and put options in to our status structure
   if (parse_cmdline(argc, argv, &state)) {
      status = -1;
      exit(EX_USAGE);
   }

   ret = pthread_attr_init(&tattr);
   ret = pthread_attr_setschedpolicy(&tattr, SCHED_BATCH);
   ret = pthread_attr_setinheritsched(&tattr, PTHREAD_EXPLICIT_SCHED);
   if ((rc = pthread_create(&io_thread, &tattr, thread_io_func, &state))) {
      vcos_log_error("Failed to create IO  thread");
   }
   ret = pthread_attr_destroy(&tattr);

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
      // run forever
      while (state.running) {
         usleep(10000);
           // state.bCapturing = !state.bCapturing;
//         if (mmal_port_parameter_set_boolean(camera_video_port, MMAL_PARAMETER_CAPTURE, state.bCapturing) != MMAL_SUCCESS) {
            // How to handle?
         // }
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
