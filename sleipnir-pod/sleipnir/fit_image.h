#ifdef __cplusplus
#define EXTERNC extern "C"
#else
#define EXTERNC
#endif

EXTERNC char *fit_image(char *buffer, int capture_width, int capture_height, int final_width, int final_height, int rotate);