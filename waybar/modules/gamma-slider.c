#include <gtk/gtk.h>
#include <math.h>
#include <glib/gstdio.h>
#include <unistd.h>

/* Waybar CFFI ABI v1: the module owns the GTK content inside its root. */
const size_t wbcffi_version = 1;
typedef struct wbcffi_module wbcffi_module;
typedef struct {
    wbcffi_module *obj;
    const char *waybar_version;
    GtkContainer *(*get_root_widget)(wbcffi_module *);
    void (*queue_update)(wbcffi_module *);
} wbcffi_init_info;
typedef struct { const char *key, *value; } wbcffi_config_entry;
typedef struct {
    GtkWidget *box, *label, *scale;
    char *controller, *state_path, *reply_path;
    guint poll, pending, request;
    gint64 request_started;
    double desired;
    gboolean syncing, dragging, dirty, busy;
} GammaSlider;

static void display_value(GammaSlider *s, double value) {
    char text[32];
    g_snprintf(text, sizeof(text), "γ %.2f", value);
    gtk_label_set_text(GTK_LABEL(s->label), text);
}

static gboolean apply(gpointer data);

static void launch(GammaSlider *s, const char *operation, const char *value) {
    if (s->reply_path) g_unlink(s->reply_path);
    g_free(s->reply_path);
    s->reply_path = g_strdup_printf("%s/gamma-slider-%d-%p-%u.reply",
                                   g_get_user_runtime_dir(), (int)getpid(), (void *)s, ++s->request);
    char *argv[8] = {"python3", s->controller, (char *)operation};
    size_t next = 3;
    if (value) argv[next++] = (char *)value;
    argv[next++] = "--reply-file";
    argv[next++] = s->reply_path;
    argv[next] = NULL;
    GError *error = NULL;
    s->busy = TRUE;
    s->request_started = g_get_monotonic_time();
    if (!g_spawn_async(NULL, argv, NULL, G_SPAWN_SEARCH_PATH | G_SPAWN_STDOUT_TO_DEV_NULL,
                       NULL, NULL, NULL, &error)) {
        g_warning("Gamma slider: %s", error->message);
        g_clear_error(&error);
        s->busy = FALSE;
    }
}

static gboolean apply(gpointer data) {
    GammaSlider *s = data;
    s->pending = 0;
    if (s->busy || !s->dirty) return G_SOURCE_REMOVE;
    s->dirty = FALSE;
    char value[16];
    g_ascii_formatd(value, sizeof(value), "%.2f", s->desired);
    launch(s, "set", value);
    return G_SOURCE_REMOVE;
}

static void changed(GtkRange *range, gpointer data) {
    GammaSlider *s = data;
    display_value(s, gtk_range_get_value(range));
    if (s->syncing) return;
    s->desired = gtk_range_get_value(range);
    s->dirty = TRUE;
    if (!s->pending && !s->busy) s->pending = g_timeout_add(80, apply, s);
}

static gboolean scroll(GtkWidget *widget, GdkEventScroll *event, gpointer data) {
    (void)widget;
    GammaSlider *s = data;
    double delta = 0;
    if (event->direction == GDK_SCROLL_UP || event->direction == GDK_SCROLL_RIGHT) delta = 0.01;
    else if (event->direction == GDK_SCROLL_DOWN || event->direction == GDK_SCROLL_LEFT) delta = -0.01;
    else if (event->direction == GDK_SCROLL_SMOOTH) {
        double dx = 0, dy = 0;
        gdk_event_get_scroll_deltas((GdkEvent *)event, &dx, &dy);
        if (dx != 0 || dy != 0) delta = (dy != 0 ? dy < 0 : dx > 0) ? 0.01 : -0.01;
    }
    gtk_range_set_value(GTK_RANGE(s->scale), gtk_range_get_value(GTK_RANGE(s->scale)) + delta);
    return TRUE;
}

static gboolean press(GtkWidget *widget, GdkEventButton *event, gpointer data) {
    (void)widget;
    (void)event;
    ((GammaSlider *)data)->dragging = TRUE;
    return FALSE;
}

static gboolean release(GtkWidget *widget, GdkEventButton *event, gpointer data) {
    (void)widget;
    (void)event;
    GammaSlider *s = data;
    s->dragging = FALSE;
    if (s->pending && !s->busy) {
        g_source_remove(s->pending);
        apply(s);
    }
    return FALSE;
}

static gboolean sync_value(gpointer data) {
    GammaSlider *s = data;
    if (s->busy) {
        char *reply = NULL;
        if (g_file_get_contents(s->reply_path, &reply, NULL, NULL)) {
            if (!g_str_has_prefix(reply, "ok")) g_warning("Gamma slider update failed");
            g_free(reply);
            g_unlink(s->reply_path);
            s->busy = FALSE;
        } else if (g_get_monotonic_time() - s->request_started > 5000000) {
            g_warning("Gamma slider update timed out");
            s->busy = FALSE;
        }
    }
    if (s->dirty && !s->busy && !s->pending) s->pending = g_timeout_add(80, apply, s);
    if (s->dragging || s->pending || s->busy || s->dirty) return G_SOURCE_CONTINUE;
    char *contents = NULL;
    if (g_file_get_contents(s->state_path, &contents, NULL, NULL)) {
        double value = g_ascii_strtod(contents, NULL);
        if (isfinite(value) && value >= 1 && value <= 3) {
            s->syncing = TRUE;
            gtk_range_set_value(GTK_RANGE(s->scale), value);
            display_value(s, value);
            s->syncing = FALSE;
        }
        g_free(contents);
    }
    return G_SOURCE_CONTINUE;
}

void *wbcffi_init(const wbcffi_init_info *info, const wbcffi_config_entry *config, size_t len) {
    (void)config;
    (void)len;
    GammaSlider *s = g_new0(GammaSlider, 1);
    s->controller = g_build_filename(g_get_user_config_dir(), "waybar/scripts/gamma.py", NULL);
    s->state_path = g_build_filename(g_get_user_runtime_dir(), "hypr-gamma-state", NULL);
    s->box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_widget_set_name(s->box, "gamma-slider");
    gtk_widget_set_tooltip_text(s->box, "Gamma 1.00–3.00 · drag or scroll · steps of 0.01");
    s->label = gtk_label_new("γ 1.00");
    gtk_label_set_width_chars(GTK_LABEL(s->label), 6);
    s->scale = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 1, 3, 0.01);
    gtk_scale_set_draw_value(GTK_SCALE(s->scale), FALSE);
    gtk_scale_set_digits(GTK_SCALE(s->scale), 2);
    gtk_range_set_increments(GTK_RANGE(s->scale), 0.01, 0.10);
    gtk_widget_set_size_request(s->scale, 120, -1);
    gtk_box_pack_start(GTK_BOX(s->box), s->label, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(s->box), s->scale, FALSE, FALSE, 0);
    gtk_container_add(info->get_root_widget(info->obj), s->box);
    g_signal_connect(s->scale, "value-changed", G_CALLBACK(changed), s);
    g_signal_connect(s->scale, "button-press-event", G_CALLBACK(press), s);
    g_signal_connect(s->scale, "button-release-event", G_CALLBACK(release), s);
    g_signal_connect(s->scale, "scroll-event", G_CALLBACK(scroll), s);
    gtk_widget_show_all(s->box);
    sync_value(s);
    s->poll = g_timeout_add(50, sync_value, s);
    launch(s, "status", NULL);
    return s;
}

void wbcffi_deinit(void *instance) {
    GammaSlider *s = instance;
    if (s->poll) g_source_remove(s->poll);
    if (s->pending) g_source_remove(s->pending);
    if (s->reply_path) g_unlink(s->reply_path);
    g_free(s->reply_path);
    g_free(s->controller);
    g_free(s->state_path);
    g_free(s);
}
