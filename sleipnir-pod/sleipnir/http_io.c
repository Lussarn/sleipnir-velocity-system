#define _GNU_SOURCE

#include <stdlib.h>
#include <curl/curl.h>
#include <stdbool.h>
#include <pthread.h>

#include <log4c.h>

#include "velocity_state.h"
#include "jpegs.h"

static pthread_t http_io_thread;
static log4c_category_t* cat;

void *http_io_thread_func(void *arg);

int http_io_init(VELOCITY_STATE *state) {
    int ret, rc;
    pthread_attr_t tattr;

    cat = log4c_category_get("sleipnir.jpegs");
    log4c_category_debug(cat, "Initializing http IO");

    ret = pthread_attr_init(&tattr);
    ret = pthread_attr_setschedpolicy(&tattr, SCHED_BATCH);
    ret = pthread_attr_setinheritsched(&tattr, PTHREAD_EXPLICIT_SCHED);

    if ((rc = pthread_create(&http_io_thread, &tattr, http_io_thread_func, state))) {
        log4c_category_fatal(cat, "Unable to create IO thread");
        return 1;
    }
    ret = pthread_attr_destroy(&tattr);
    return ret;
}

size_t http_io_curl_callback(void *ptr, size_t size, size_t nmemb, void *chunk){
   size_t realsize = size * nmemb;
   snprintf(chunk, 255, "%s", (char *)ptr);
   return realsize;
}

int http_io_post(CURL *curl, char *url, void *post_data, int post_size, void *answer) {
   CURLcode res = 0;
   char chunk[256];
   struct curl_slist *headerlist=NULL;
   static const char buf[] = "Expect:";

   headerlist = curl_slist_append(headerlist, buf);
   curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headerlist);
   curl_easy_setopt(curl, CURLOPT_URL, url);
   curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data);
   curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, &http_io_curl_callback);
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

void *http_io_thread_func(void *arg) {
   static char post_data[300000];
   char answer[256];
   CURL *curl;
   CURLcode res;
   VELOCITY_STATE *state = (VELOCITY_STATE *) arg;
   char url[256];
   int cx;

   curl = curl_easy_init();

   while (state->running) {
      state->post_frames = false;
      jpegs_reset();
      state->camera_position = 0;
      while(state->running) {
         cx = snprintf(url, 256, "%s?action=startcamera&cam=%s", state->url, state->identifier);
         if (cx < 0 || cx >= 256) {
            printf("Error snprintf in thread_io_func");
         }
         memset(answer,0,strlen(answer));  // Is this necesary?
         res = http_io_post(curl, url, "", 0, &answer);
         if (res != CURLE_OK) {
            usleep(100000);
            continue;
         }
         if (strcmp(answer, "START") == 0) break;
         usleep(100000);
      }

      state->post_frames = true;
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
         res = http_io_post(curl, url, jpegs_get_by_position(frame_number).data, jpegs_get_by_position(frame_number).data_size, &answer);
         if (res != CURLE_OK) {
            break;
         }

         if (strcmp(answer, "STOP") == 0) {
            state->post_frames = false;
            if (frame_number > (state->camera_position - 50)) break;
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