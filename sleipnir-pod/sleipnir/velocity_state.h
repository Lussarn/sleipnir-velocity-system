#ifndef VELOCITY_STATE_H_
#define VELOCITY_STATE_H_

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

/** Structure containing all state information for the current run
 */
typedef struct VELOCITY_STATE_T
{
    bool running;                       /// still running
    int camera_version;                 /// version of camera

    char *identifier;                   /// identifier for this camera ie. cam1 or cam2
    char *url;                          /// Url for posting data
    bool post_frames;
    int camera_position;

    RASPICAM_CAMERA_PARAMETERS camera_parameters; /// Camera setup parameters
    MMAL_COMPONENT_T *camera_component;    /// Pointer to the camera component
    MMAL_POOL_T *camera_pool;            /// Pointer to the pool of buffers used by camera video port

} VELOCITY_STATE;

void velocity_state_default(VELOCITY_STATE *state);

#define CAMERA_VERSION_13 0
#define CAMERA_VERSION_21 1

typedef struct
{
   int version;
   int sensor_mode;
   int framerate;

   // 1. Capture size
   int capture_width;
   int capture_height;

   // 2. Region of interest (crop)
   int roi_left;
   int roi_top;
   int roi_width;
   int roi_height;

   // 3. Rotate
   int rotate;

   // 4. Resize
   int final_width;
   int final_height;


} CAMERA_VERSION_PROPERTIES;

static CAMERA_VERSION_PROPERTIES camera_version_properties[] =
{
   { CAMERA_VERSION_13, 7, 90,  // Camera mode, framerate
      320, 480,                 // capture width, height
      0, 0, 320, 480,           // region of interest
      0,                        // rotate
      320, 480 },               // final width height

   { CAMERA_VERSION_21, 6, 90,  // Camera mode, framerate
      1280, 660,                // capture width, height
      130, 0, 1020, 660,       // region of interest
      90,                       // rotate
      320, 480 }                // final width height

};

CAMERA_VERSION_PROPERTIES camera_version(int camera_version);

/// Command ID's and Structure defining our command line options
#define CommandIdentifier    15
#define CommandUrl           16
#define CommandCameraVersion 17

static COMMAND_LIST cmdline_commands[] =
{
   { CommandIdentifier,    "-identifier", "id", "Command identifer for this camera", 1},
   { CommandUrl,           "-url",        "u",  "Url to post data to", 1},
   { CommandCameraVersion, "-camversion", "cv", "Camera version (15, 21)", 1},
};
static int cmdline_commands_size = sizeof(cmdline_commands) / sizeof(cmdline_commands[0]);

int velocity_state_parse_cmdline(int argc, const char **argv, VELOCITY_STATE *state);

#endif