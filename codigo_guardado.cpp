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

double save_image_16bits_tiff(uint16_t * imageGray16, char * name , uint32_t weight, uint32_t heigth, uint32_t channels ){

    TIFF *out = TIFFOpen(name, "w");
    if(out == NULL){
        printf("No se puedo realizar el guardado\n");
        return 0;
    }

    TIFFSetField(out, TIFFTAG_IMAGEWIDTH, weight);
    TIFFSetField(out, TIFFTAG_IMAGELENGTH, heigth);
    TIFFSetField(out, TIFFTAG_SAMPLESPERPIXEL, channels)save_image_16bits_tiff;
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

bool save_flir_images(char * path, char * visible_image_name, char * thermal_image_name, uint16_t * imageGray16, uint32_t thermal_weight, uint32_t thermal_heigth, uint8_t * frame_color, uint32_t frame_weight, uint32_t frame_heigth ){
    long long ms = current_timestamp();
    char path_thermal_image[100];
    sprintf(path_thermal_image, "%s/%s.tiff", path, thermal_image_name);

    char path_visible_image[100];
    sprintf(path_visible_image, "%s/%s.jpg", path, visible_image_name);

    save_image_16bits_tiff(imageGray16, path_thermal_image , thermal_weight, thermal_heigth, 1 );

    save_jpg_image_from_buffer(frame_color, path_visible_image, frame_weight, frame_heigth);
}