$SYS_GCC_RASPBERRY = "C:\SysGCC\raspberry"
$ROOT = "C:\raspberrypi\rootfs"

$GCC = $SYS_GCC_RASPBERRY + "\bin\arm-linux-gnueabihf-gcc.exe"
$GPP = $SYS_GCC_RASPBERRY + "\bin\arm-linux-gnueabihf-c++.exe"

Write-Output "Compiling RaspiCamControl.c"
& $GCC -c RaspiCamControl.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include `
    -I"$ROOT"\opt\vc\include\interface\vcos\pthreads `
    -I"$ROOT"\opt\vc\include\interface\vmcs_host\linux
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}
    
Write-Output "Compiling sleipnir.c"
& $GCC -c sleipnir.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include `
    -I"$ROOT"\opt\vc\include\interface\vcos\pthreads `
    -I"$ROOT"\opt\vc\include\interface\vmcs_host\linux
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling jpegs.c"
& $GCC -c jpegs.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling encoder.c"
& $GCC -c encoder.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include 
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling velocity_state.c"
& $GCC -c velocity_state.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include 
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling http_io.c"
& $GCC -c http_io.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include 
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling camera.c"
& $GCC -c camera.c `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include 
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Compiling fit_image.cpp"
& $GPP -c fit_image.cpp `
    -I"$ROOT"\usr\include `
    -I"$ROOT"\usr\include\arm-linux-gnueabihf `
    -I"$ROOT"\opt\vc\include `
    -I"$ROOT"\usr\include\opencv
If ($lastExitCode -ne "0") {
    exit $lastExitCode 
}

Write-Output "Linking files..."
& $GPP --sysroot="$ROOT" `
    -o sleipnir-pod sleipnir.o RaspiCamControl.o jpegs.o encoder.o velocity_state.o http_io.o camera.o fit_image.o `
    "-Wl,-rpath-link=$ROOT\usr\lib\arm-linux-gnueabihf" `
    "-Wl,-rpath-link=$ROOT\usr\lib\arm-linux-gnueabihf\blas" `
    "-Wl,-rpath-link=$ROOT\usr\lib\arm-linux-gnueabihf\lapack" `
    "-Wl,-rpath-link=$ROOT\opt\vc\lib" `
    -L"$ROOT"\opt\vc\lib `
    -lvcos -lbcm_host -lturbojpeg -lcurl -lpthread -lmmal_core -lmmal -lmmal_components -lmmal_util -llog4c `
    -lopencv_shape -lopencv_stitching -lopencv_superres -lopencv_videostab -lopencv_aruco -lopencv_bgsegm -lopencv_bioinspired -lopencv_ccalib -lopencv_datasets -lopencv_dpm -lopencv_face -lopencv_freetype -lopencv_fuzzy -lopencv_hdf -lopencv_line_descriptor -lopencv_optflow -lopencv_video -lopencv_plot -lopencv_reg -lopencv_saliency -lopencv_stereo -lopencv_structured_light -lopencv_phase_unwrapping -lopencv_rgbd -lopencv_viz -lopencv_surface_matching -lopencv_text -lopencv_ximgproc -lopencv_calib3d -lopencv_features2d -lopencv_flann -lopencv_xobjdetect -lopencv_objdetect -lopencv_ml -lopencv_xphoto -lopencv_highgui -lopencv_videoio -lopencv_imgcodecs -lopencv_photo -lopencv_imgproc -lopencv_core -lpopt
