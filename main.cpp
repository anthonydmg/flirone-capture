#include <cstdio>
#include <stdint.h>
#include <libusb-1.0/libusb.h>
#include <string.h>
#include <vector>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgcodecs.hpp>
#include <linux/videodev2.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <cmath>

#include "flironecapture.h"
//#include <>

#define REQ_TYPE    1
#define REQ         0xb
#define V_STOP      0
#define V_START     1
#define INDEX(i)    (i)
#define LEN(l)      (l)
#define BUF85SIZE   1048576  
#define COLOR_MAP_SIZE 768
#define FRAME_WIDTH1    640
#define FRAME_HEIGHT1   480
#define FRAME_FORMAT1   V4L2_PIX_FMT_MJPEG
#define FRAME_FORMAT2   V4L2_PIX_FMT_RGB24
// colorized thermal image
#define FRAME_WIDTH2    80
#define FRAME_HEIGHT2   60
#define SH 0.65
#define SW 0.65

using namespace std;
using namespace cv;
double hfov = 38;
double vfov = 50;


double convertAreaMeters(double areaPixels, double altura, int heigth, int width){
        // RGB images distances
        double Vdh = 2 * altura * tan(0.5 * hfov * (M_PI/ 180.0));
        double Vdv = 2 * altura * tan(0.5 * vfov * (M_PI / 180.0));
        // Scale to thermal distances
        double Tdh = Vdh * SH;
        double Tdv = Vdv * SW;

        double pixelSize = (Tdv * Tdh) / (heigth * width);
        double areaMeters = areaPixels * pixelSize;
        return areaMeters;
    }

int main(){
    FlirOneCapture * flirOneCap = new FlirOneCapture;

    ThermalFrame * thermalFrame = new ThermalFrame;
   
    char palname[10] = "rainbow";

    thermalFrame->set_pallete(palname);
    uint8_t TFrameD[80][60][3];
    double Temperatures[80 * 60];
    uint32_t jpg_size = 0;
    uint32_t thermal_size = 0;
    uint32_t pyload_size = 0;
    uint8_t tframe_data[350000];
    uint16_t gray16frame[4800];
    uint8_t TFrame[80 * 60 * 3];
    uint32_t minval_gray;
    uint32_t maxval_gray;
    uint8_t mask[80][60];
    uint8_t frame_color[1440 * 1080 * 3];
    char path[100] = "./images";
    //flirOneCap->open();
    libusb_device_handle * device_handle = flirOneCap->open();
    if(device_handle == NULL){
        printf("Hubo un error en la conexion\n");
        return 0;
    }


    while (1)
    {   
        read_thermal_frame(device_handle,tframe_data, jpg_size, thermal_size,  pyload_size );
        read_gray16(tframe_data, gray16frame, thermal_size, minval_gray, maxval_gray);
        read_thermal_frame_color(gray16frame, TFrame, minval_gray, maxval_gray );
        if(read_visible_frame_color(tframe_data, frame_color, thermal_size, jpg_size, 1440,1080)){
                Mat VisibleImage = Mat(1440, 1080, CV_8UC3, &frame_color);
                namedWindow("VisibleImage", WINDOW_NORMAL);
                resizeWindow("VisibleImage", 640, 480);
                imshow("VisibleImage", VisibleImage);
                save_flir_images(path, gray16frame, 60, 80, frame_color,1080,1440 );
        }
  


        Mat ThermalImage = Mat(80, 60, CV_8UC3, &TFrame);

        //save_image_16bits_tiff(gray16frame,60,80,1);

        namedWindow("Image", WINDOW_NORMAL);
        resizeWindow("Image", 640, 480);
        imshow("Image", ThermalImage);

        char c= (char) waitKey(1);
        if(c==27)
            break;
    }
    
    destroyAllWindows();
 

    return 0;
    //Mat imageT(80,60, CV_8UC3, TFrame.data());  
    
    // Create a grabar termal image
    // retornr 
    // create funcion read_frame que tenga este bucle. Va recibir esta informacion 
    // y la va a usar para algo
    // asi asi no mas por que de ahi tengo que colocarle como un script para que se ejecute
    
    //return 0;
}   

// Hacer esto https://thecodinginterface.com/blog/opencv-Mat-from-array-and-vector/



// Hacer esto https://thecodinginterface.com/blog/opencv-Mat-from-array-and-vector/

