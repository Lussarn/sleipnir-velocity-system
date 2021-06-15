#ifdef __cplusplus
#define EXTERNC extern "C"
#else
#define EXTERNC
#endif

EXTERNC char *fit_image(char *buffer, int capture_width, int capture_height, int roi_left, int roi_top, int roi_width, int roi_height, int rotate, int final_width, int final_height);
