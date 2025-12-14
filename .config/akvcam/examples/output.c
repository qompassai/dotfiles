#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define VIDEO_OUTPUT "/dev/video7"
/*
 * V4L2_CAP_READWRITE for rw
 * V4L2_CAP_STREAMING for mmap and userptr
 */
//#define CAPTURE_METHOD V4L2_CAP_READWRITE
#define CAPTURE_METHOD V4L2_CAP_STREAMING
/*
 *
 * V4L2_MEMORY_MMAP
 * V4L2_MEMORY_USERPTR
 */
#define MEMORY_TYPE V4L2_MEMORY_MMAP

#define N_BUFFERS 4

#define FPS 30
#define DURATION_SECONDS 30
#define N_FRAMES (FPS * DURATION_SECONDS)

struct DataBuffer
{
    char *start;
    size_t length;
};

int main()
{
    int fd = open(VIDEO_OUTPUT, O_RDWR | O_NONBLOCK, 0);

    struct v4l2_format fmt;
    memset(&fmt, 0, sizeof(struct v4l2_format));
    fmt.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    ioctl(fd, VIDIOC_G_FMT, &fmt);
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_RGB24;
    fmt.fmt.pix.width = 640;
    fmt.fmt.pix.height = 480;
    ioctl(fd, VIDIOC_S_FMT, &fmt);
    struct v4l2_capability capabilities;
    memset(&capabilities, 0, sizeof(struct v4l2_capability));
    ioctl(fd, VIDIOC_QUERYCAP, &capabilities);
    struct DataBuffer *buffers = NULL;
    if (CAPTURE_METHOD == V4L2_CAP_READWRITE
        && capabilities.capabilities & V4L2_CAP_READWRITE) {
        buffers = calloc(1, sizeof(struct DataBuffer));
        buffers->length = fmt.fmt.pix.sizeimage;
        buffers->start = calloc(1, fmt.fmt.pix.sizeimage);
    } else if (CAPTURE_METHOD == V4L2_CAP_STREAMING
               && capabilities.capabilities & V4L2_CAP_STREAMING) {
        struct v4l2_requestbuffers requestBuffers;
        memset(&requestBuffers, 0, sizeof(struct v4l2_requestbuffers));
        requestBuffers.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
        requestBuffers.memory = MEMORY_TYPE;
        requestBuffers.count = N_BUFFERS;
        ioctl(fd, VIDIOC_REQBUFS, &requestBuffers);
        buffers = calloc(requestBuffers.count,
                         sizeof(struct DataBuffer));
        for (__u32 i = 0; i < requestBuffers.count; i++) {
            if (MEMORY_TYPE == V4L2_MEMORY_MMAP) {
                struct v4l2_buffer buffer;
                memset(&buffer, 0, sizeof(struct v4l2_buffer));
                buffer.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
                buffer.memory = V4L2_MEMORY_MMAP;
                buffer.index = i;
                ioctl(fd, VIDIOC_QUERYBUF, &buffer);
                buffers[i].length = buffer.length;
                buffers[i].start = mmap(NULL,
                                        buffer.length,
                                        PROT_READ | PROT_WRITE,
                                        MAP_SHARED,
                                        fd,
                                        buffer.m.offset);
            } else {
                buffers[i].length = fmt.fmt.pix.sizeimage;
                buffers[i].start = calloc(1, fmt.fmt.pix.sizeimage);
            }
        }
        for (__u32 i = 0; i < requestBuffers.count; i++) {
            struct v4l2_buffer buffer;
            memset(&buffer, 0, sizeof(struct v4l2_buffer));
            if (MEMORY_TYPE == V4L2_MEMORY_MMAP) {
                buffer.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
                buffer.memory = V4L2_MEMORY_MMAP;
                buffer.index = i;
            } else {
                buffer.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
                buffer.memory = V4L2_MEMORY_USERPTR;
                buffer.index = i;
                buffer.m.userptr = (unsigned long) buffers[i].start;
                buffer.length = buffers[i].length;
            }
            ioctl(fd, VIDIOC_QBUF, &buffer);
        }
        enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
        ioctl(fd, VIDIOC_STREAMON, &type);
    }
    srand(time(0));
    for (int i = 0; i < N_FRAMES; i++) {
        if (CAPTURE_METHOD == V4L2_CAP_READWRITE
            && capabilities.capabilities & V4L2_CAP_READWRITE) {
            for (size_t byte = 0; byte < buffers->length; byte++)
                buffers->start[byte] = rand() & 0xff;
            write(fd, buffers->start, buffers->length);
        } else if (CAPTURE_METHOD == V4L2_CAP_STREAMING
                   && capabilities.capabilities & V4L2_CAP_STREAMING) {
            struct v4l2_buffer buffer;
            memset(&buffer, 0, sizeof(struct v4l2_buffer));
            buffer.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
            buffer.memory = MEMORY_TYPE;
            ioctl(fd, VIDIOC_DQBUF, &buffer);
            for (size_t byte = 0; byte < buffer.bytesused; byte++)
                buffers[buffer.index].start[byte] = rand() & 0xff;

            ioctl(fd, VIDIOC_QBUF, &buffer);
        }

        struct timespec ts;
        ts.tv_sec = 0;
        ts.tv_nsec = 1e9 / FPS;
        nanosleep(&ts, &ts);
    }

    if (CAPTURE_METHOD == V4L2_CAP_READWRITE
        && capabilities.capabilities & V4L2_CAP_READWRITE) {
        free(buffers->start);
    } else if (CAPTURE_METHOD == V4L2_CAP_STREAMING
               && capabilities.capabilities & V4L2_CAP_STREAMING) {
        enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
        ioctl(fd, VIDIOC_STREAMOFF, &type);

        for (__u32 i = 0; i < N_BUFFERS; i++) {
            if (MEMORY_TYPE == V4L2_MEMORY_MMAP)
                munmap(buffers[i].start, buffers[i].length);
            else
                free(buffers[i].start);
        }
    }
    free(buffers);
    close(fd);
    return 0;
}
