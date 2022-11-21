#include <iostream>

using namespace std;

/* struct ThermalFrame
{
    uint32_t jpg_size = 0;
    uint32_t thermal_size = 0;
    uint32_t pyload_size = 0;
    uint32_t pointer = 0;
    const int32_t TFRAME_WIDTH = 80;
    const int32_t TFRAME_HEIGHT = 60;
    const int32_t VISUAL_WIDTH = 640;
    const int32_t VISUAL_HEIGHT = 480;
    const int32_t TFRAME_SIZE=(4800);
    const int32_t COLOR_IMAGE_SIZE=(VISUAL_WIDTH*VISUAL_HEIGHT);
    uint8_t buffer_data[350000];
    uint8_t * palette_colormap;
    bool complete = false;
    uint16_t TFrameGray16[80][60];
    uint16_t * gray16frame ;
    uint16_t maxval_gray = 0;
    uint16_t minval_gray = 65536;
    uint16_t max_x = 0;
    uint16_t max_y = 0;
}; */

extern "C" {
    void my_func(double * array){
        array[0] = 65;
        array[1] = 68;
        //func(array);
    }
    
    void read_tframe( uint8_t tframe_data[350000] , uint32_t  &jpg_size,  uint32_t  &thermal_size,  uint32_t  &pyload_size ){
        jpg_size = 100;
        thermal_size = 200;
        pyload_size = 500;
        tframe_data[0] = 1;
        tframe_data[1] = 3;
        tframe_data[2] = 1;
        tframe_data[3] = 3;
        //tframe_data = buffer_data;
    }

    void read_gray16_scale(uint8_t tframe_data[350000], uint16_t gray16frame [4800], uint32_t  &thermal_size ){
        tframe_data[0] = 1;
        tframe_data[1] = 3;
        tframe_data[2] = 1;
        tframe_data[3] = 3;
        printf("gray16frame = %d\n", gray16frame[0]);
        gray16frame[0] = 100;
        printf("gray16frame = %d\n", gray16frame[0]);
        gray16frame[1] = 5;
        gray16frame[2] = 52;
        //tframe_data = buffer_data;
    }
}