#include <cstdio>
#include <stdint.h>
#include <libusb-1.0/libusb.h>
#include <string.h>
#include <vector>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include "flironedriver.h"
//#include <>

using namespace std;


bool FlirOneDriver::connect_device(){
    printf("Inicializar conexion...\n");
    if(libusb_init(NULL) < 0){
        printf("Inicializar Usb Device\n");
        return false;
    }
    
    printf("Open device Usb...\n");
    libusb_device_handle * handle;
    
    handle = libusb_open_device_with_vid_pid(NULL, VENDOR_ID, PRODUCT_ID);
    printf("Se abrio Usb...\n");
    //this->device_handle = libusb_open_device_with_vid_pid(NULL, VENDOR_ID, PRODUCT_ID);
    this->device_handle = handle;

    if(this->device_handle == NULL){
        printf("Usb device no se conecto\n");
        return false;
    }

    printf("Flir One Gen3 exitosamente conectado\n");
    
    if(libusb_set_configuration(this->device_handle, 3) < 0){
        printf("Error en la configuracion\n");
        return false;
    }
    
    printf("Exitosamente configurado \n");

    if(libusb_claim_interface(this->device_handle, 0)){
        printf("Error en libusb_claim_interface 0\n");
        return false;
    }
    
    if(libusb_claim_interface(this->device_handle, 1)){
        printf("Error en libusb_claim_interface 1\n");
        return false;
    }
    
    if(libusb_claim_interface(this->device_handle, 2)){
        printf("Error en libusb_claim_interface 2\n");
        return false;
    }
    
    printf("Interfaces 0, 1, 2 reclamadas con exito\n");
 

    return true;
};

bool FlirOneDriver::init_transfer(){
    uint8_t data[2] = {0,0};
    int timeout = 100;

    if(libusb_control_transfer(device_handle, REQ_TYPE, REQ, V_STOP, INDEX(2),
         data, LEN(0), timeout) < 0){
        printf("Error en libusb_control_transfer 1\n");
        return false;
    }

    if(libusb_control_transfer(device_handle, REQ_TYPE, REQ, V_STOP, INDEX(1),
         data, LEN(0), timeout) < 0){
        printf("Error en libusb_control_transfer 2\n");
        return false;
    }

    if(libusb_control_transfer(device_handle, REQ_TYPE, REQ, V_START, INDEX(1),
         data, LEN(0), timeout) < 0){
        printf("Error en libusb_control_transfer 3\n");
        return false;
    }


    if(libusb_control_transfer(device_handle, REQ_TYPE, REQ, V_START, INDEX(2),
         data, LEN(2), timeout * 2) < 0){
        printf("Error en libusb_control_transfer 4\n");
        return false;
    }

    return true;
}

void FlirOneDriver::close(){
    libusb_reset_device(device_handle);
    libusb_close(device_handle);
    libusb_exit(NULL);
}

int FlirOneDriver::read_stream(uint8_t *buffer, uint32_t &size ){
    int length_stream;
    libusb_bulk_transfer(device_handle, 0x85, buffer, size, &length_stream, 100);
    printf("Actual length bulk: %d \n", length_stream);
   
    uint8_t data[1024];
    int read_length;
    int ret;

    ret = libusb_bulk_transfer(device_handle, 0x81, data, 1024, &read_length, 10);
    ret = libusb_bulk_transfer(device_handle, 0x83, data, 1024, &read_length, 10);
    
    if (strcmp(libusb_error_name(ret), "LIBUSB_ERROR_NO_DEVICE")==0) {
            printf("EP 0x83 LIBUSB_ERROR_NO_DEVICE -> reset USB\n");
            return -1;
        }
    return length_stream;
}

bool FlirOneDriver::open(void){
    
    printf("Conectando a device...\n");

    bool success_connection = this->connect_device();
    
    if(!success_connection){ 
        close();   
        printf("Error al connectar dispositivo\n");
        return false;
    }

    if(!this->init_transfer()){
        printf("Error al iniciar tranferencia\n");
        return false;
    }

    //libusb_release_interface(device_handle, 0);
    return true;
}
