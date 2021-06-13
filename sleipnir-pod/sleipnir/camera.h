#ifndef CAMERA_H_
#define CAMERA_H_

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

// Standard port setting for the camera component
#define MMAL_CAMERA_VIDEO_PORT 1

MMAL_STATUS_T camera_create_component(VELOCITY_STATE *state, MMAL_PORT_BH_CB_T cb);
void camera_destroy_component(VELOCITY_STATE *state);

#endif