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
//   state->timeout = 5000;     // 5s delay before take image
   state->camera_version = CAMERA_VERSION_15;
   state->post_frames = false;
   state->camera_position = 0;

   // Set up the camera_parameters to default
   raspicamcontrol_set_defaults(&state->camera_parameters);
}

CAMERA_VERSION_PROPERTIES camera_version(int camera_version) {
    return camera_version_properties[camera_version];
}

/**
 * Parse the incoming command line and put resulting parameters in to the state
 *
 * @param argc Number of arguments in command line
 * @param argv Array of pointers to strings from command line
 * @param state Pointer to state structure to assign any discovered parameters to
 * @return Non-0 if failed for some reason, 0 otherwise
 */
int velocity_state_parse_cmdline(int argc, const char **argv, VELOCITY_STATE *state) {
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
         case CommandCameraVersion:
            if (sscanf(argv[i + 1], "%u", &state->camera_version) != 1)
               valid = 0;
            else
               if (state->camera_version == 15) 
                  state->camera_version = CAMERA_VERSION_15;
               else if (state->camera_version == 21) 
                  state->camera_version = CAMERA_VERSION_21;
               else {
                  state->camera_version = 0;
                  valid=0;
                  break;
               }
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

         default:
            break;
      }
   }

   if (!valid)
   {
      fprintf(stderr, "Invalid command line option (%s)\n", argv[i-1]);
      return 1;
   }
   return 0;
}
