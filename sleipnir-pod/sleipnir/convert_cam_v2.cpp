#include <opencv2/opencv.hpp>

#include "convert_cam_v2.h"

char *convert_from_cam_v2(char *data) {

    cv::Mat srcImage = cv::Mat(720, 1280, CV_8U, data);
    cv::rotate(srcImage, srcImage, cv::ROTATE_90_CLOCKWISE);

    cv::Mat destImage;
    cv::Size destImageSize = cv::Size(320, 480);

    cv::resize(srcImage, destImage, destImageSize, 0, 0, CV_INTER_LINEAR);

    char* bytes = new char[destImageSize.width * destImageSize.height];
    std::memcpy(bytes, destImage.data, destImageSize.width * destImageSize.height * sizeof(char));



    return bytes;
}