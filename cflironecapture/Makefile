CC = g++ -fPIC
INC = -I/usr/include/libusb-1.0
CFLAGS = -Wall -g
LIBS = -ljpeg -ltiff -lusb-1.0 -lm
#OPENCV = `pkg-config opencv4 --cflags --libs`

default: 
	@echo \'make lib\' to create the shared lib lflirone
	@echo \'make clean\' to remove all .so

lib: flironecapture.o 
	g++ -shared -o flironecapture.so flironecapture.o -L/usr/local/lib -lusb-1.0 -ljpeg -ltiff

flironecapture.o: flironecapture.cpp plank.h
	$(CC) ${INC} ${CFLAGS} -c flironecapture.cpp ${LIBS}

palletes.o : palletes.h

clean: 
	rm -f flironecapture.o flironecapture.so