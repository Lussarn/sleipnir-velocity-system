#include <opencv2/opencv.hpp>

#include "fit_image.h"

 // fit_image allocates a new buffer if needed, otherwisee the buffer sent in is returned
 // If a new buffer is returned it is your responsibility to free it.
char *fit_image(char *buffer, int capture_width, int capture_height, int final_width, int final_height, int rotate) {
    char *bytes;

    bytes = buffer;
    if (capture_width != final_width || capture_height != final_height || rotate > 0) {
        cv::Mat srcImage = cv::Mat(capture_height, capture_width, CV_8U, buffer);
//    cv::rotate(srcImage, srcImage, cv::ROTATE_90_CLOCKWISE);

//        cv::Mat destImage;
        if (rotate != 0) {
            switch (rotate) {
                case 90:
                    cv::rotate(srcImage, srcImage, cv::ROTATE_90_CLOCKWISE);
                    break;
                case 180:
                    cv::rotate(srcImage, srcImage, cv::ROTATE_180);
                    break;
                case 270:
                    cv::rotate(srcImage, srcImage, cv::ROTATE_90_COUNTERCLOCKWISE);
                    break;
                default:
                    break;
            }
        } 

        cv::Size finalImageSize = cv::Size(final_width, final_height);
        if (capture_width != final_width || capture_height != final_height) {
            cv::resize(srcImage, srcImage, finalImageSize, 0, 0, CV_INTER_LINEAR);
        }

        bytes = new char[finalImageSize.width * finalImageSize.height];
        std::memcpy(bytes, srcImage.data, finalImageSize.width * finalImageSize.height * sizeof(char));  
    }

    return bytes;
}