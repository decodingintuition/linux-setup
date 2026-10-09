#define _GNU_SOURCE
#include <wayland-client.h>
#include "gamma-protocol.h"
#include <errno.h>
#include <math.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

typedef struct Output {
    uint32_t id, size;
    struct wl_output *output;
    struct zwlr_gamma_control_v1 *control;
    struct Output *next;
} Output;
static struct wl_display *display;
static struct zwlr_gamma_control_manager_v1 *manager;
static Output *outputs;
static double current = 1.0;
static volatile sig_atomic_t running = 1;

static int set_table(Output *output, double value) {
    if (!output->control || output->size < 2) return -1;
    size_t length = output->size * 3 * sizeof(uint16_t);
    uint16_t *table = malloc(length);
    if (!table) return -1;
    for (uint32_t i = 0; i < output->size; ++i) {
        uint16_t sample = (uint16_t)lround(pow((double)i / (output->size - 1), 1.0 / value) * 65535);
        table[i] = table[output->size + i] = table[2 * output->size + i] = sample;
    }
    int fd = memfd_create("waybar-gamma", MFD_CLOEXEC);
    size_t sent = 0;
    while (fd >= 0 && sent < length) {
        ssize_t count = write(fd, (char *)table + sent, length - sent);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) break;
        sent += (size_t)count;
    }
    free(table);
    int result = -1;
    if (sent == length && lseek(fd, 0, SEEK_SET) == 0) {
        zwlr_gamma_control_v1_set_gamma(output->control, fd);
        result = 0;
    }
    if (fd >= 0) close(fd);
    return result;
}

static void gamma_size(void *data, struct zwlr_gamma_control_v1 *control, uint32_t size) {
    (void)control;
    Output *output = data;
    output->size = size;
    if (current != 1.0) set_table(output, current);
}
static void gamma_failed(void *data, struct zwlr_gamma_control_v1 *control) {
    Output *output = data;
    fprintf(stderr, "Gamma control unavailable for output %u\n", output->id);
    output->size = 0;
    output->control = NULL;
    zwlr_gamma_control_v1_destroy(control);
}
static const struct zwlr_gamma_control_v1_listener gamma_listener = {gamma_size, gamma_failed};
static void acquire(Output *output) {
    output->control = zwlr_gamma_control_manager_v1_get_gamma_control(manager, output->output);
    zwlr_gamma_control_v1_add_listener(output->control, &gamma_listener, output);
}
static void global(void *data, struct wl_registry *registry, uint32_t id, const char *interface, uint32_t version) {
    (void)data;
    if (!strcmp(interface, wl_output_interface.name)) {
        Output *output = calloc(1, sizeof(*output));
        if (!output) return;
        output->id = id;
        output->output = wl_registry_bind(registry, id, &wl_output_interface, version < 2 ? version : 2);
        output->next = outputs;
        outputs = output;
        if (manager) acquire(output);
    } else if (!strcmp(interface, zwlr_gamma_control_manager_v1_interface.name)) {
        manager = wl_registry_bind(registry, id, &zwlr_gamma_control_manager_v1_interface, 1);
        for (Output *output = outputs; output; output = output->next) acquire(output);
    }
}
static void global_remove(void *data, struct wl_registry *registry, uint32_t id) {
    (void)data; (void)registry;
    for (Output **link = &outputs; *link; link = &(*link)->next) {
        Output *output = *link;
        if (output->id != id) continue;
        *link = output->next;
        if (output->control) zwlr_gamma_control_v1_destroy(output->control);
        wl_output_destroy(output->output);
        free(output);
        break;
    }
}
static const struct wl_registry_listener registry_listener = {global, global_remove};
static int available(void) {
    if (!manager || !outputs) return 0;
    for (Output *output = outputs; output; output = output->next)
        if (!output->control || output->size < 2) return 0;
    return 1;
}
static void stop(int signal_number) { (void)signal_number; running = 0; }

int main(int argc, char **argv) {
    if (argc != 2 || strlen(argv[1]) >= sizeof(((struct sockaddr_un *)0)->sun_path)) return 2;
    display = wl_display_connect(NULL);
    if (!display) return 1;
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &registry_listener, NULL);
    int server = -1, result = 1;
    if (wl_display_roundtrip(display) < 0 || wl_display_roundtrip(display) < 0 || !available()) goto cleanup;
    server = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (server < 0) goto cleanup;
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    strcpy(address.sun_path, argv[1]);
    if (bind(server, (struct sockaddr *)&address, sizeof(address)) < 0) {
        close(server);
        server = -1;
        goto cleanup;
    }
    if (listen(server, 8) < 0) goto cleanup;
    signal(SIGTERM, stop);
    signal(SIGINT, stop);
    signal(SIGPIPE, SIG_IGN);
    struct pollfd descriptors[2] = {{wl_display_get_fd(display), POLLIN, 0}, {server, POLLIN, 0}};
    result = 0;
    while (running) {
        if (wl_display_dispatch_pending(display) < 0 || wl_display_flush(display) < 0) break;
        if (poll(descriptors, 2, -1) < 0) {
            if (errno == EINTR) continue;
            break;
        }
        if (descriptors[0].revents & (POLLERR | POLLHUP)) break;
        if ((descriptors[0].revents & POLLIN) && wl_display_dispatch(display) < 0) break;
        if (!(descriptors[1].revents & POLLIN)) continue;
        int client = accept4(server, NULL, NULL, SOCK_CLOEXEC);
        if (client < 0) continue;
        struct timeval timeout = {.tv_sec = 1};
        setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        char request[64] = {0};
        ssize_t length = recv(client, request, sizeof(request) - 1, 0);
        char *end;
        double value = strtod(request, &end);
        int ok = length > 0 && end != request && (*end == '\n' || *end == '\0') && isfinite(value) && value >= 1 && value <= 3 && available();
        if (ok) {
            for (Output *output = outputs; output; output = output->next)
                if (set_table(output, value) < 0) ok = 0;
            if (wl_display_roundtrip(display) < 0 || !available()) ok = 0;
            if (ok) current = value;
        }
        send(client, ok ? "ok\n" : "error\n", ok ? 3 : 6, MSG_NOSIGNAL);
        close(client);
    }
cleanup:
    if (server >= 0) { close(server); unlink(argv[1]); }
    for (Output *output = outputs; output;) {
        Output *next = output->next;
        if (output->control) zwlr_gamma_control_v1_destroy(output->control);
        wl_output_destroy(output->output);
        free(output);
        output = next;
    }
    if (manager) zwlr_gamma_control_manager_v1_destroy(manager);
    wl_registry_destroy(registry);
    wl_display_flush(display);
    wl_display_disconnect(display);
    return result;
}
