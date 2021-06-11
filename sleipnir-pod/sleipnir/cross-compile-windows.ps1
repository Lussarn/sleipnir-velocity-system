$SYS_GCC_RASPBERRY = "C:\SysGCC\raspberry"
$ROOT = "C:\raspberrypi\rootfs"

$GCC = $SYS_GCC_RASPBERRY + "\bin\arm-linux-gnueabihf-gcc.exe"
$GPP = $SYS_GCC_RASPBERRY + "\bin\arm-linux-gnueabihf-c++.exe"
$LD = $SYS_GCC_RASPBERRY + "\bin\arm-linux-gnueabihf-ld.exe"

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
    
Write-Output "Compiling RaspiCLI.c"
& $GCC -c RaspiCLI.c `
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

Write-Output "Linking files..."
& $GCC --sysroot="$ROOT" `
    -o sleipnir-pod sleipnir.o RaspiCamControl.o RaspiCLI.o jpegs.o `
    "-Wl,-rpath-link=$ROOT\usr\lib\arm-linux-gnueabihf" `
    "-Wl,-rpath-link=$ROOT\opt\vc\lib" `
    -L"$ROOT"\opt\vc\lib `
    -lvcos -lbcm_host -lturbojpeg -lcurl -lpthread -lmmal_core -lmmal -lmmal_components -lmmal_util
