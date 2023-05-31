#include "flironecapture.h"
#include <cstdio>
#include <cstring>
#include "plank.h"
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <cmath>
#include <libusb-1.0/libusb.h>
#include "palletes.h"
#include <stdint.h>
#include <vector>
#include <tiffio.h>
#include <string>
#include <sys/time.h>
#include <jpeglib.h>

using namespace std;

bool startWithMagicByte(uint8_t * buffer){
    uint8_t magic_byte[] = {0xEF, 0xBE, 0x00, 0x00};
    for (int i = 0; i<4; i++){
        if (buffer[i] != magic_byte[i]){
        return false;
        }
    }
    return true;
}

bool startWithMagicByteJpg(uint8_t * buffer){
    uint8_t magic_byte[] = {0xFF, 0xD8, 0xFF};
    for (int i = 0; i<3; i++){
        if (buffer[i] != magic_byte[i]){
        return false;
        }
    }
    return true;
}

int findMagicBytes(uint8_t * buffer, int length){
    for(int i =0; i< length - 4; i ++){
        if(startWithMagicByte(buffer + i)){
            return i;
        }
    }
    return -1;
}

libusb_device_handle * FlirOneCapture::connect_device(){
    printf("Inicializar conexion...\n");
    if(libusb_init(NULL) < 0){
        printf("Inicializar Usb Device\n");
        return NULL;
    }
    
    printf("Open device Usb...\n");
    libusb_device_handle * handle;
    
    handle = libusb_open_device_with_vid_pid(NULL, VENDOR_ID, PRODUCT_ID);
    printf("Se abrio Usb...\n");
    //this->device_handle = libusb_open_device_with_vid_pid(NULL, VENDOR_ID, PRODUCT_ID);
    

    if(handle == NULL){
        printf("Usb device no se conecto\n");
        return NULL;
    }

    printf("Flir One Gen3 exitosamente conectado\n");
    
    if(libusb_set_configuration(handle, 3) < 0){
        printf("Error en la configuracion\n");
        return NULL;
    }
    
    printf("Exitosamente configurado \n");

    if(libusb_claim_interface(handle, 0)){
        printf("Error en libusb_claim_interface 0\n");
        return NULL;
    }
    
    if(libusb_claim_interface(handle, 1)){
        printf("Error en libusb_claim_interface 1\n");
        return NULL;
    }
    
    if(libusb_claim_interface(handle, 2)){
        printf("Error en libusb_claim_interface 2\n");
        return NULL;
    }
    
    printf("Interfaces 0, 1, 2 reclamadas con exito\n");
    
    return handle;
};


bool FlirOneCapture::init_transfer(libusb_device_handle * device_handle){
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

libusb_device_handle * FlirOneCapture::open(){
    /*printf("Capture Init...\n");
    printf("opened = %d ",this->opened);
    this->opened = (this->flirOneDriver)->open();
    return this->opened;*/
        
    printf("Conectando a device...\n");

    libusb_device_handle * handle = this->connect_device();
    
    if(handle == NULL){ 
        close(handle);   
        printf("Error al connectar dispositivo\n");
        return NULL;
    }

    if(!this->init_transfer(handle)){
        printf("Error al iniciar tranferencia\n");
        return NULL;
    }

    //libusb_release_interface(device_handle, 0);
    return handle;
}


void FlirOneCapture::close(libusb_device_handle * device_handle){
    libusb_reset_device(device_handle);
    libusb_close(device_handle);
    libusb_exit(NULL);
}

bool FlirOneCapture::isOpened(){
    return opened;
}

bool FlirOneCapture::load_color_map(){
    FILE * file = fopen("./palettes/Rainbow.raw", "rb");
    
    if(file == NULL) return false;

    if(fread(colormap, sizeof(uint8_t), COLOR_MAP_SIZE, file) < COLOR_MAP_SIZE){
        fclose(file);
        return false;
    }

    fclose(file);

    return true;
}


int FlirOneCapture::read_stream(libusb_device_handle * device_handle, uint8_t *buffer, uint32_t &size ){
    int length_stream;
    printf("Read Buffer = %d\n", device_handle);
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

bool FlirOneCapture::read(ThermalFrame * thermalFrame, libusb_device_handle * device_handle){
    printf("Inicia lectura\n");
    uint8_t buffer[BUF85SIZE];
    uint32_t size = (u_int32_t) sizeof(buffer);
    STATE_READ state =  STATE_SEARCH_HEAD;
    int mb_idx;
    // Funcion read
    printf("Reset\n");
    //thermalFrame->reset();
    while (1)
    {  
        printf("Init read stream\n");
        int length_stream = this->read_stream(device_handle,buffer, size);
        printf("Fin read stream\n");
        if(length_stream < 0){
            this->close(device_handle);
            return  false ; 
        }

        printf("State = %d\n", state);
        switch (state)
        {
            case STATE_SEARCH_HEAD:
                mb_idx = findMagicBytes(buffer, length_stream);
                if (mb_idx >= 0){
                    printf("Magic Byte in: %d\n", mb_idx);
                    thermalFrame->push_header(buffer + mb_idx, length_stream - mb_idx);
                    if (thermalFrame->isComplete()){
                        printf("Se completo el frame\n");
                        state = STATE_FINISH;
                    } else{
                    state = STATE_PUSH_DATA;
                    }
                }
                break;

            case STATE_PUSH_DATA:
                thermalFrame->push_data(buffer, length_stream);
                if (thermalFrame->isComplete()){
                    printf("Se completo el frame\n");
                    state = STATE_FINISH;
                }
                break;

            default:
                break;
        }

        if(state  == STATE_FINISH ){
            printf("Ya se encontro\n");
            break;
        }
    }
    return true;
}


bool ThermalFrame::isComplete(){
    return complete;
}

void ThermalFrame::setComplete(bool isComplete){
    this->complete = isComplete;
}

void ThermalFrame::read_size(uint8_t * buffer){
    printf("LLamada a read size\n");
    this->pyload_size  = buffer[8]  +  (buffer[9] << 8) + (buffer[10] << 16) + (buffer[11] << 24);
    this->thermal_size = buffer[12] + (buffer[13] << 8) + (buffer[14] << 16) + (buffer[15] << 24);
    this->jpg_size     = buffer[16] + (buffer[17] << 8) + (buffer[18] << 16) + (buffer[19] << 24);
    
}

void ThermalFrame::push_header(uint8_t * buffer, uint32_t length){
    if(length >= 28){
       read_size(buffer);
    }
    this->pointer = 0;
    push_data(buffer, length);
}

void ThermalFrame::push_data(uint8_t * buffer, uint32_t length){
    memmove(this->buffer_data + this->pointer, buffer, length);
    printf("\nHeader: pyload_size = %d, thermal_size=%d, jpg_size =%d, pointer=%d\n", pyload_size, thermal_size, jpg_size, pointer);
    this->pointer = this->pointer + length;

    if(this->thermal_size == 0 && this->pointer > 28){
        read_size(this->buffer_data);
    }
    
    printf("\n2 Header: pyload_size = %d, thermal_size=%d, jpg_size =%d, pointer=%d\n", pyload_size, thermal_size, jpg_size, pointer);
    
    if (this->pyload_size != 0 && this->pyload_size + 28 <= this->pointer){
        printf("\nSe complento el payload : pyload_size = %d, pointer= %d, thermal_size=%d, jpg_size =%d\n", pyload_size, pointer, thermal_size, jpg_size);
        this->calcule_tframe_gray16();
        this->setComplete(true);
    }
}

void ThermalFrame::reset(){
    printf("Reseteando thermal frame \n");
    this->pointer = 0;
    this->pyload_size  = 0;
    this->thermal_size = 0;
    this->jpg_size     = 0;
    this->complete = false;
}

void ThermalFrame::set_pallete(char * palname){
    this->palette_colormap = rainbow;
}

void ThermalFrame::calcule_tframe_gray16(){

    uint32_t pos;
    uint16_t value;
    for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
        for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){
            // aqui esta fallando
            pos = 2 * ( y * (THERMAL_IMAGE_WIDTH + 2) + x) + 32;
            //printf("data[%d] = %d\n", pos,buffer_data[pos]);
            value =  this->buffer_data[pos] | this->buffer_data[pos + 1] << 8;
            //printf("value = %d, min_val = %d, max_val = %d\n", value, min_val, max_val); 
            this->TFrameGray16[x][y] = value;
            
            if( value < this->minval_gray){
                this->minval_gray = value;       
            }

            if(value > this->maxval_gray){
                this->maxval_gray = value;
                this->max_x = x;
                this->max_y = y;
            }
        }
    }
}

void ThermalFrame::get_thermal_frame(uint8_t TFrame[THERMAL_IMAGE_SIZE]){
    
    //vector <uint16_t> GRAY16_TFRAME(THERMAL_IMAGE_SIZE, 0x00); // valores radiometricos 
    
    /*uint32_t pos;
    uint16_t value;
    uint16_t min_val = 65536;
    uint16_t max_val = 0;
    uint16_t max_x = 0;
    uint16_t max_y = 0;

    printf("Matriz radiometrica\n");*/
    /*for(int i = 0; i < pointer ; i++){
        printf("Matriz radiometrica\n");
        printf("Data[i] = %d", buffer_data[i]);
    }*/

    
    /*for(int y = 0; y < this->THERMAL_IMAGE_HEIGHT; y++){
        for(int x = 0; x< this->THERMAL_IMAGE_WIDTH; x++){
            // aqui esta fallando
            pos = 2 * ( y * (this->THERMAL_IMAGE_WIDTH + 2) + x) + 32;
            //printf("data[%d] = %d\n", pos,buffer_data[pos]);
            value =  this->buffer_data[pos] | this->buffer_data[pos + 1] << 8;
            //printf("value = %d, min_val = %d, max_val = %d\n", value, min_val, max_val); 
            GRAY16_TFRAME[ y * this->THERMAL_IMAGE_WIDTH + x] = value;
            
            if( value < min_val){
                min_val = value;       
            }

            if(value > max_val){
                max_val = value;
                max_x = x;
                max_y = y;
            }
        }
    }*/

   
    uint16_t scale;
    uint16_t delta;
    uint8_t val_pix;
    //printf("\nmin_val = %d, max_val = %d\n", min_val, max_val); 
    //printf("\nd=%d\n", min_val, max_val); 
    delta = this->maxval_gray - this->minval_gray;
    printf("Delta: %d\n", delta);
    if( delta == 0)
        delta = 1;

    scale = 0x10000 / delta;
    
    printf("Thermal Image\n");
    
    for(int y = 0; y < this->TFRAME_HEIGHT; y++){
    
        for(int x = 0; x< this->TFRAME_WIDTH; x++){
            
            val_pix = (this->TFrameGray16[x][y] - this->minval_gray) * scale >> 8;
            //printf("val_pix = %d, y = %d, x = %d\n", val_pix,y,x);
            for(int c = 0 ; c < 3 ; c++){
                //TFrame[x][y][c] = this->palette_colormap[3 * val_pix + c];
                TFrame[c *this->TFRAME_WIDTH * this->TFRAME_HEIGHT  +  y * this->TFRAME_WIDTH + x + c] = this->palette_colormap[3 * val_pix + c];
                //TFrame[c *this->TFRAME_WIDTH * this->TFRAME_HEIGHT  +  y * this->TFRAME_WIDTH + x] = this->palette_colormap[256 * c + val_pix];
                //TFrame[3 * y * this->TFRAME_WIDTH + 3 *x + c] = this->palette_colormap[3 * val_pix + c];
            }
        }
    }
}


double ThermalFrame::raw2temperature(uint16_t raw){
    // mystery correction factor
    raw *= 4;
    // calc amount of radiance of reflected objects ( Emissivity < 1 )
    double RAWrefl=PlanckR1/(PlanckR2*(exp(PlanckB/(TempReflected+273.15))-PlanckF))-PlanckO;
    // get displayed object temp max/min
    double RAWobj=(raw-(1-Emissivity)*RAWrefl)/Emissivity;
    // calc object temperature
    return PlanckB/log(PlanckR1/(PlanckR2*(RAWobj+PlanckO))+PlanckF)-273.15;
}

double ThermalFrame::pixel_temperature(uint8_t x, uint8_t y ){
    return this->raw2temperature(this->TFrameGray16[x][y]);
}

void ThermalFrame::get_temperatures(double Temperatures[THERMAL_IMAGE_SIZE]){
    
    for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
       for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){   
            Temperatures[y * THERMAL_IMAGE_WIDTH + x] = this->raw2temperature(this->TFrameGray16[x][y]);
       }
    }
}

void ThermalFrame::save_img(){
    //vector<Mat> imgs;
    //Mat grey16Img = Mat(80, 60, CV_16UC1, &this->TFrameGray16);
    //time_t t = time(0);   // get time now
    //struct tm * now = localtime( & t );

    //char name[80];
    //strftime(name, 80,"%Y-%m-%d.tiff",now);
    //imwrite(name, grey16Img);
    return;
}

FlirOneCapture::FlirOneCapture(){
    //this->flirOneDriver = new FlirOneDriver;
}


void read_header(uint8_t * buffer, uint32_t & pyload_size, uint32_t & thermal_size, uint32_t & jpg_size){
    //printf("LLamada a read size\n");
    pyload_size  = buffer[8]  +  (buffer[9] << 8) + (buffer[10] << 16) + (buffer[11] << 24);
    thermal_size = buffer[12] + (buffer[13] << 8) + (buffer[14] << 16) + (buffer[15] << 24);
    jpg_size     = buffer[16] + (buffer[17] << 8) + (buffer[18] << 16) + (buffer[19] << 24);
    //printf("\n pyload_size = %d, thermal_size=%d, jpg_size =%d\n", pyload_size, thermal_size, jpg_size);
    
}


//void setComplete(bool isComplete);


bool t_frame_iscomplete(uint32_t pyload_size, uint32_t pointer){
      if (pyload_size != 0 && pyload_size + 28 <= pointer){
        return true;
    }
    return false;
}


bool read_thermal_frame(libusb_device_handle * device_handle, uint8_t* tframe_data, uint32_t  &jpg_size,  uint32_t  &thermal_size,  uint32_t  &pyload_size ){
        //printf("Inicia lectura\n");
        uint8_t buffer[BUF85SIZE];
        uint32_t size = (u_int32_t) sizeof(buffer);
        int mb_idx;
        uint32_t pointer  = 0;
        thermal_size = 0;
        jpg_size = 0;
        pyload_size = 0;

        //printf("Reset\n");
        FlirOneCapture flirOneCapture;
        bool found_header = false;

        while (1)
        {  
            //printf("Init read stream\n");
            int length_stream = flirOneCapture.read_stream(device_handle, tframe_data + pointer, size);
    
            //printf("Fin read stream\n");
            
            ///thermalFrame->reset();
            
            if(length_stream < 0){
                flirOneCapture.close(device_handle);
                return  false ; 
            }

            

            if (!found_header){
                mb_idx = findMagicBytes(tframe_data, length_stream);
                if (mb_idx >= 0){
                    printf("Magic Byte in: %d\n", mb_idx);
                        
                    if(mb_idx > 0){
                        memmove(tframe_data, tframe_data + mb_idx, length_stream - mb_idx);
                    }

                    found_header = true;
                }
            } 
            
            if(found_header){
                pointer = pointer + length_stream;
                if(thermal_size == 0 && pointer >= 28 ){
                    read_header(tframe_data, pyload_size, thermal_size, jpg_size);
                }
    
                if(t_frame_iscomplete(pyload_size, pointer)){
                      printf("\nSe complento el payload : pyload_size = %d, pointer= %d, thermal_size=%d, jpg_size =%d\n", pyload_size, pointer, thermal_size, jpg_size);
                   break;
                }
            }
        }

        //memmove(tframe_data, buffer, pointer);
        return true;
    }

void read_gray16(uint8_t tframe_data[450000], uint16_t gray16frame [4800], uint32_t  &thermal_size, uint32_t  &minval_gray, uint32_t  &maxval_gray ){
        uint32_t pos;
        uint16_t value;
        for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
            for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){
                // aqui esta fallando
                pos = 2 * ( y * (THERMAL_IMAGE_WIDTH + 2) + x) + 32;
                //printf("data[%d] = %d\n", pos,buffer_data[pos]);
                value =  tframe_data[pos] | tframe_data[pos + 1] << 8;
                //printf("value = %d, min_val = %d, max_val = %d\n", value, min_val, max_val); 
                gray16frame[y* THERMAL_IMAGE_WIDTH + x] = value;
                
                if( value < minval_gray){
                    minval_gray = value;       
                }

                if(value > maxval_gray){
                    maxval_gray = value;
                }
            }
        }
    }
   void read_thermal_frame_color(uint16_t gray16frame [4800], uint8_t  tframe_color[80 * 60 * 3], uint32_t  &minval_gray, uint32_t  &maxval_gray ){
        uint16_t scale;
        uint16_t delta;
        uint8_t val_pix;
        //printf("\nmin_val = %d, max_val = %d\n", min_val, max_val); 
        //printf("\nd=%d\n", min_val, max_val); 
        delta = maxval_gray - minval_gray;
        printf("Delta: %d\n", delta);
        if( delta == 0)
            delta = 1;

        scale = 0x10000 / delta;
        
        printf("Thermal Image\n");
        
        for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
        
            for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){
                
                val_pix = (gray16frame[x + y * THERMAL_IMAGE_WIDTH] - minval_gray) * scale >> 8;
                for(int c = 0 ; c < 3 ; c++){
                    //tframe_color[c *THERMAL_IMAGE_WIDTH * THERMAL_IMAGE_HEIGHT  +  y * THERMAL_IMAGE_WIDTH + x] = rainbow[3 * val_pix + c];
                    tframe_color[3 *y  +  x * THERMAL_IMAGE_HEIGHT * 3 + c] = rainbow[3 * val_pix + c];
                }
            }
        }
    }

double raw2temperature(uint16_t raw){
    // mystery correction factor
    raw *= 4;
    // calc amount of radiance of reflected objects ( Emissivity < 1 )
    double RAWrefl=PlanckR1/(PlanckR2*(exp(PlanckB/(TempReflected+273.15))-PlanckF))-PlanckO;
    // get displayed object temp max/min
    double RAWobj=(raw-(1-Emissivity)*RAWrefl)/Emissivity;
    // calc object temperature
    return PlanckB/log(PlanckR1/(PlanckR2*(RAWobj+PlanckO))+PlanckF)-273.15;
}


long long current_timestamp() {
    struct timeval te; 
    gettimeofday(&te, NULL); // get current time
    long long milliseconds = te.tv_sec*1000LL + te.tv_usec/1000; // calculate milliseconds
    // printf("milliseconds: %lld\n", milliseconds);
    return milliseconds;
}

double save_image_16bits_tiff(uint16_t * imageGray16, char * name , uint32_t weight, uint32_t heigth, uint32_t channels ){

    TIFF *out = TIFFOpen(name, "w");
    if(out == NULL){
        printf("No se puedo realizar el guardado\n");
        return 0;
    }

    TIFFSetField(out, TIFFTAG_IMAGEWIDTH, weight);
    TIFFSetField(out, TIFFTAG_IMAGELENGTH, heigth);
    TIFFSetField(out, TIFFTAG_SAMPLESPERPIXEL, channels);
    TIFFSetField(out, TIFFTAG_BITSPERSAMPLE, 16);
    TIFFSetField(out, TIFFTAG_ORIENTATION, ORIENTATION_TOPLEFT);
    TIFFSetField(out, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
    TIFFSetField(out, TIFFTAG_COMPRESSION, COMPRESSION_NONE);
    TIFFSetField(out, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_MINISBLACK);

    tsize_t result_size = TIFFWriteEncodedStrip(out, 0 , imageGray16,  weight * heigth * sizeof(imageGray16[0]));
   
    if (result_size < 0){
          printf("No se puedo realizar el guardado\n");
    }

    printf("Guardado exitoso\n");
    TIFFClose(out);
}

/* void load_image_16bits_tiff(char pathname[100], uint16_t image_gray16[80 * 60]){

    TIFF *out = TIFFOpen(pathname, "r");
    if(out == NULL){
        printf("No se puedo realizar el guardado\n");
        return ;
    }

    tstrip_t strip;
    printf("(tsize_t) -1) = %d \n", (tsize_t) -1);
    for (strip = 0; strip < 2; strip++){
		printf("TIFFNumberOfStrips: %d\n", TIFFNumberOfStrips(out));
        TIFFReadEncodedStrip(out, strip, image_gray16, -1);
    }
    //_TIFFfree(buf);
    TIFFClose(out);
    printf("Lectura exitosa\n");
}
 */

void load_image_16bits_tiff(char pathname[100], uint16_t image_gray16[80 * 60]){

    TIFF *tif = TIFFOpen(pathname, "r");
    if(tif == NULL){
        printf("No se puedo realizar el guardado\n");
        return ;
    }

    tstrip_t strip;
    uint32_t* bc;
	uint32_t stripsize;
    
    TIFFGetField(tif, TIFFTAG_STRIPBYTECOUNTS, &bc);
    printf("TIFFNumberOfStrips: %d\n", TIFFNumberOfStrips(tif));
    printf("StripSize = %d\n",bc[0]);
    printf("StripSize = %d\n",bc[1]);
    printf("StripSize = %d\n",bc[2]);
    stripsize = 0;
    for (strip = 0; strip < TIFFNumberOfStrips(tif); strip++) {
		TIFFReadRawStrip(tif, strip, image_gray16 + stripsize / 2, -1);
        stripsize = bc[strip];
	}
}

bool save_jpg_image_from_buffer(uint8_t * bmp_buffer, char * name, uint32 width, uint32  height){
    FILE* fHandle;
    struct jpeg_compress_struct info;
	struct jpeg_error_mgr err;
    
	fHandle = fopen(name, "wb");
	if(fHandle == NULL) {
		return false;
	}

    info.err = jpeg_std_error(&err);
	jpeg_create_compress(&info);


	jpeg_stdio_dest(&info, fHandle);
	info.image_width = width;
	info.image_height = height;
	info.input_components = 3;
	info.in_color_space = JCS_RGB;

    jpeg_set_defaults(&info);
	jpeg_set_quality(&info, 100, TRUE);

    jpeg_start_compress(&info, TRUE);

    /* Write every scanline ... */
    unsigned char* lpRowBuffer[1];
	while(info.next_scanline < info.image_height) {
		lpRowBuffer[0] =  bmp_buffer + info.next_scanline * (width * 3);
		jpeg_write_scanlines(&info, lpRowBuffer, 1);
	}

	jpeg_finish_compress(&info);
	fclose(fHandle);
	jpeg_destroy_compress(&info);
	return 0;
}

uint8 * decompress_jpg_image(uint8_t * jpg_buffer, uint32_t size){
    struct jpeg_decompress_struct info;
    struct jpeg_error_mgr jerr;
    int width, height, pixel_size, row_stride;
    
    info.err= jpeg_std_error(&jerr);
    jpeg_create_decompress(&info);
    //printf("Creando decompress\n");
    jpeg_mem_src(&info, jpg_buffer, size);
    //printf("Estableciendo fuente\n");
    try
    {
        int rc= jpeg_read_header(&info,TRUE);
         
        if (rc != 1){
            printf("Hubo un error al descomprimir imagen\n");
            return NULL;
        }
    }
    catch(const std::exception& e)
    {
        return NULL;
    }
    
   

    //printf("Comenzando decompresion\n");
    
    jpeg_start_decompress(&info);

    width =info.output_width;
    height=info.output_height;
    pixel_size=info.output_components;
    
    row_stride=width*pixel_size;

    int bmp_size= width * height *pixel_size;
    //uint8_t bmp_buffer[bmp_size];
    unsigned char *bmp_buffer=new unsigned char[bmp_size];

    while (info.output_scanline < info.output_height)
    {   unsigned char *buffer_array[1];
        buffer_array[0]= bmp_buffer + (info.output_scanline) *row_stride;
        //printf("buffer_array = %d", buffer_array);
        jpeg_read_scanlines(&info,buffer_array,1);
    }
    //printf("Finalizando decompresion\n");
    jpeg_finish_decompress(&info);
    jpeg_destroy_decompress(&info);
    
    return bmp_buffer;
}

bool save_flir_images_prev(char * path, uint16_t * imageGray16, uint32_t thermal_weight, uint32_t thermal_heigth, uint8_t * frame_color, uint32_t frame_weight, uint32_t frame_heigth ){
    long long ms = current_timestamp();
    char thermal_image_name[100];
    sprintf(thermal_image_name, "%s/flir_thermal_16gray_%lld.tiff", path ,ms);

    char visible_image_name[100];
    sprintf(visible_image_name, "%s/flir_visible_image_%lld.jpg", path, ms);

    save_image_16bits_tiff(imageGray16, thermal_image_name , thermal_weight, thermal_heigth, 1 );

    save_jpg_image_from_buffer(frame_color, visible_image_name, frame_weight, frame_heigth);
}

bool save_flir_images(char * path, char * visible_image_name, char * thermal_image_name, uint16_t * imageGray16, uint32_t thermal_weight, uint32_t thermal_heigth, uint8_t * frame_color, uint32_t frame_weight, uint32_t frame_heigth ){
    long long ms = current_timestamp();
    char path_thermal_image[100];
    sprintf(path_thermal_image, "%s/%s.tiff", path, thermal_image_name);

    char path_visible_image[100];
    sprintf(path_visible_image, "%s/%s.jpg", path, visible_image_name);

    save_image_16bits_tiff(imageGray16, path_thermal_image , thermal_weight, thermal_heigth, 1 );

    save_jpg_image_from_buffer(frame_color, path_visible_image, frame_weight, frame_heigth);
}

bool read_visible_frame_color( uint8_t tframe_data[350000], uint8_t frame_color[1440 * 1080 * 3] , uint32_t  &thermal_size , uint32_t  &jpg_size , uint32_t width, uint32_t heigth){
    uint8 *  bmp_buffer ;
    //printf("Comenzando la descompresion\n");
    //printf("thermal_size = %d, jpg_size = %d\n", thermal_size, jpg_size);
    
    if(!startWithMagicByteJpg(tframe_data + 28 + thermal_size)){
        return false;
    }

    bmp_buffer = decompress_jpg_image(tframe_data + 28 + thermal_size, jpg_size);
    
    if (bmp_buffer == NULL)
        return false;
    //printf("Descomprimio la imagen\n");
    for(int y = 0; y < heigth; y++){
            for(int x = 0; x< width; x++){
                uint32_t bmp_offset=(x+y*width)*3;
                //printf("x = %d, y = %d, bmp_offset = %d\n", x ,y, bmp_offset);
                for(int c = 0 ; c < 3 ; c++){
                    //printf("bmp_buffer[%d] = %d\n", bmp_offset + c,  bmp_buffer[bmp_offset + c]);
                    //printf("[3 *y  +  x * heigth * 3 + c] = %d\n", 3 *y  +  x * heigth * 3 + c);
                    frame_color[3 *y  +  x * heigth * 3 + c] = bmp_buffer[bmp_offset + c];
                }
            }
        }
    return true;
}

void read_thermal_frame_temperatures(uint16_t gray16frame [4800], double Temperatures[80 * 60]){
        for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
            for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){   
                    Temperatures[y + x * THERMAL_IMAGE_HEIGHT] = raw2temperature(gray16frame[x + y * THERMAL_IMAGE_WIDTH]);
            }
        }
}  

extern "C" {
    FlirOneCapture * new_flironecapture(){
        FlirOneCapture * cap = new FlirOneCapture;
        return cap;
    } 

    libusb_device_handle * open_device(){ 
        FlirOneCapture * cap = new FlirOneCapture;
        return cap->open();
    }


    bool read_tframe(libusb_device_handle * device_handle, uint8_t* tframe_data, uint32_t  &jpg_size,  uint32_t  &thermal_size,  uint32_t  &pyload_size ){
       return  read_thermal_frame( device_handle, tframe_data,jpg_size,thermal_size,pyload_size );
    }

    void read_gray16_scale(uint8_t tframe_data[350000], uint16_t gray16frame [4800], uint32_t  &thermal_size, uint32_t  &minval_gray, uint32_t  &maxval_gray ){
        read_gray16(tframe_data, gray16frame, thermal_size, minval_gray, maxval_gray);
    }
    
    void read_tframe_color(uint16_t gray16frame [4800], uint8_t  tframe_color[80 * 60 * 3], uint32_t  &minval_gray, uint32_t  &maxval_gray ){
        read_thermal_frame_color(gray16frame, tframe_color, minval_gray, maxval_gray );
    }

    void read_tframe_temperatures(uint16_t gray16frame [4800], double Temperatures[80 * 60]){
           for(int y = 0; y < THERMAL_IMAGE_HEIGHT; y++){
                for(int x = 0; x< THERMAL_IMAGE_WIDTH; x++){   
                        Temperatures[y + x * THERMAL_IMAGE_HEIGHT] = raw2temperature(gray16frame[x + y * THERMAL_IMAGE_WIDTH]);
                }
            }
    }  

    bool read_frame_color( uint8_t tframe_data[350000], uint8_t frame_color[1440 * 1080 * 3], uint32_t  &thermal_size , uint32_t  &jpg_size , uint32_t width, uint32_t heigth){
        return read_visible_frame_color(tframe_data, frame_color, thermal_size, jpg_size, width, heigth);
    }
    
    bool save_flirone_images(char * path,char * visible_image_name, char * thermal_image_name, uint16_t * imageGray16, uint32_t thermal_weight, uint32_t thermal_heigth, uint8_t * frame_color, uint32_t frame_weight, uint32_t frame_heigth ){
        return save_flir_images(path, visible_image_name, thermal_image_name, imageGray16, thermal_weight, thermal_heigth, frame_color,frame_weight,frame_heigth );
    }
    
    void load_thermal_image_16bits_tiff(char pathname[100], uint16_t image_gray16[80 * 60]){
        return load_image_16bits_tiff(pathname, image_gray16);
    }
}
