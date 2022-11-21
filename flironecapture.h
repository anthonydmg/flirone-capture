//#include "flironedriver.h"
#include <stdint.h>
#include <unistd.h>
#include <libusb-1.0/libusb.h>

#define REQ_TYPE    1
#define REQ         0xb
#define V_STOP      0
#define V_START     1
#define INDEX(i)    (i)
#define LEN(l)      (l)
#define BUF85SIZE   1048576  
#define THERMAL_IMAGE_WIDTH    80
#define THERMAL_IMAGE_HEIGHT   60
#define THERMAL_IMAGE_SIZE     4800
#define COLOR_MAP_SIZE 768

enum STATE_READ {STATE_SEARCH_HEAD, STATE_PUSH_DATA, STATE_FINISH};



class ThermalFrame {
    public:
        uint32_t jpg_size = 0;
        uint32_t thermal_size = 0;
        uint32_t pyload_size = 0;
        uint32_t pointer = 0;
        const int32_t TFRAME_WIDTH = THERMAL_IMAGE_WIDTH;
        const int32_t TFRAME_HEIGHT = THERMAL_IMAGE_HEIGHT;
        const int32_t VISUAL_WIDTH = 640;
        const int32_t VISUAL_HEIGHT = 480;
        const int32_t TFRAME_SIZE=(THERMAL_IMAGE_SIZE);
        const int32_t COLOR_IMAGE_SIZE=(VISUAL_WIDTH*VISUAL_HEIGHT);
        uint8_t buffer_data[350000];
    private:
        uint8_t * palette_colormap;
        bool complete = false;
        uint16_t TFrameGray16[80][60];
        uint16_t maxval_gray = 0;
        uint16_t minval_gray = 65536;
        uint16_t max_x = 0;
        uint16_t max_y = 0;
       
    public:
        bool isComplete();
        void setComplete(bool isComplete);
        void push_data(uint8_t * buffer, uint32_t length);
        void push_header(uint8_t * buffer, uint32_t length);
        void set_pallete(char * palname);
        void get_thermal_frame(uint8_t TFrame[THERMAL_IMAGE_SIZE]);
        void reset();
        void get_temperatures(double Temperatures[THERMAL_IMAGE_SIZE]);
        void calcule_tframe_gray16();
        double raw2temperature(uint16_t raw);
        double pixel_temperature(uint8_t x, uint8_t y);
        void save_img();
    private: 
        void read_size(uint8_t * buffer);
};


class FlirOneCapture{
    public:
        static const size_t VENDOR_ID = 0x09cb;
        static const size_t PRODUCT_ID = 0x1996;
    private: 
        bool opened;
    private:
        //FlirOneDriver * flirOneDriver;
        uint8_t buffer[BUF85SIZE];
        uint8_t colormap[COLOR_MAP_SIZE];
        //libusb_device_handle * device_handle;
        //u_int32_t size = (u_int32_t) sizeof(buffer);
    public: 
        FlirOneCapture();
        libusb_device_handle * open();
        bool isOpened();
        bool read(ThermalFrame * thermalFrame, libusb_device_handle * device_handle);
        bool load_color_map();
        libusb_device_handle * connect_device();
        bool init_transfer(libusb_device_handle * device_handle);
        int read_stream(libusb_device_handle * device_handle, uint8_t *buffer, uint32_t &size );
        void close(libusb_device_handle * device_handle);
};

bool read_thermal_frame(libusb_device_handle * device_handle, uint8_t* tframe_data, uint32_t  &jpg_size,  uint32_t  &thermal_size,  uint32_t  &pyload_size );
void read_gray16(uint8_t tframe_data[350000], uint16_t gray16frame [4800], uint32_t  &thermal_size, uint32_t  &minval_gray, uint32_t  &maxval_gray );
void read_thermal_frame_color(uint16_t gray16frame [4800], uint8_t  tframe_color[80 * 60 * 3], uint32_t  &minval_gray, uint32_t  &maxval_gray );
double save_image_16bits_tiff(uint16_t * imageGray16, uint32_t weight, uint32_t heigth, uint32_t channels );
bool read_visible_frame_color( uint8_t tframe_data[350000], uint8_t * frame_color , uint32_t  &thermal_size , uint32_t  &jpg_size , uint32_t width, uint32_t heigth);
bool save_flir_images(char * path, uint16_t * imageGray16, uint32_t thermal_weight, uint32_t thermal_heigth, uint8_t * frame_color, uint32_t frame_weight, uint32_t frame_heigth );