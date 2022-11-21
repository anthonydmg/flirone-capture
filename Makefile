CC = g++ -fPIC
INC = -I/usr/include/libusb-1.0
CFLAGS = -Wall -g
LIBS = -ljpeg -ltiff -lusb-1.0 -lm
OPENCV = `pkg-config opencv4 --cflags --libs`

all: main.o flironecapture.o flironedriver.o palletes.o
	$(CC) $(INC) $(CFLAGS) -o flirone main.o flironedriver.o flironecapture.o ${LIBS} ${OPENCV}

main.o: main.cpp flironecapture.h palletes.h
	$(CC) ${INC} ${CFLAGS} -c main.cpp ${LIBS} ${OPENCV}


palletes.o : palletes.h

flironedriver.o: flironedriver.cpp
	$(CC) ${INC} ${CFLAGS} -c flironedriver.cpp ${LIBS} ${OPENCV}

flironecapture.o: flironecapture.cpp flironedriver.h plank.h
	$(CC) ${INC} ${CFLAGS} -c flironecapture.cpp ${LIBS} ${OPENCV}
clean: 
	rm -f main.o flironecapture.o flironedriver.o flirone