#include <stdio.h>
#include <stdbool.h>

#include "interface/mmal/mmal.h"
#include "interface/mmal/mmal_logging.h"
#include "interface/mmal/mmal_buffer.h"
#include "interface/mmal/util/mmal_util.h"
#include "interface/mmal/util/mmal_util_params.h"
#include "interface/mmal/util/mmal_default_components.h"
#include "interface/mmal/util/mmal_connection.h"

#include "velocity_state.h"

/**
 * Assign a default set of parameters to the state passed in
 *
 * @param state Pointer to state structure to assign defaults to
 */
void velocity_state_default(VELOCITY_STATE *state)
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
   state->camera_version = CAMERA_VERSION_21;
   state->post_frames = false;
   state->camera_position = 0;

   // Set up the camera_parameters to default
   raspicamcontrol_set_defaults(&state->camera_parameters);
}

CAMERA_VERSION_PROPERTIES camera_version(int camera_version) {
    return camera_version_properties[camera_version];
}

