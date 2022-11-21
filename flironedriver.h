#include <libusb-1.0/libusb.h>
#include <stdint.h>

#define REQ_TYPE    1
#define REQ         0xb
#define V_STOP      0
#define V_START     1
#define INDEX(i)    (i)
#define LEN(l)      (l)
#define BUF85SIZE   1048576  
#define COLOR_MAP_SIZE 768
#define RGB_IMAGE_WIDTH    640
#define RGB_IMAGE_HEIGHT   480
#define FRAME_FORMAT1   V4L2_PIX_FMT_MJPEG
#define FRAME_FORMAT2   V4L2_PIX_FMT_RGB24
// colorized thermal image
#define THERMAL_IMAGE_WIDTH    80
#define THERMAL_IMAGE_HEIGHT   60
#define THERMAL_IMAGE_SIZE     4800

class FlirOneDriver {
    public:
        static const size_t VENDOR_ID = 0x09cb;
        static const size_t PRODUCT_ID = 0x1996;
    private:
        libusb_device_handle * device_handle;
    public: 
        bool open(void);
        int read_stream(uint8_t * buffer, uint32_t &size);
        void close();
    private:
        bool connect_device();
        bool init_transfer();
};