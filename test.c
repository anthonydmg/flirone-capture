#include <sys/time.h>
#include <stdio.h>

long long current_timestamp() {
    struct timeval te; 
    gettimeofday(&te, NULL); // get current time
    long long milliseconds = te.tv_sec*1000LL + te.tv_usec/1000; // calculate milliseconds
    // printf("milliseconds: %lld\n", milliseconds);
    return milliseconds;
}


int main(){
    long long ms = current_timestamp();
    char name[100];
    sprintf(name, "flir_thermal_16gray_%lld.tiff", ms);

}