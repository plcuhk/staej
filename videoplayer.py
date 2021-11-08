import sys
from gi.repository import GObject, Gtk, Gst, GstVideo
from gnotifier import GNotifier


Gst.FRAME = Gst.SECOND // 30

def getXid(window) :
    if sys.platform == "win32":
        if not window.ensure_native():
            print("Error - video playback requires a native window")
        import ctypes
        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
        gpointer = ctypes.pythonapi.PyCapsule_GetPointer(window.__gpointer__, None)
        gdkdll = ctypes.CDLL ("libgdk-3-0.dll")
        return gdkdll.gdk_win32_window_get_handle(gpointer)
    else:
        from gi.repository import GdkX11
        return window.get_xid()

class VideoPlayer(GNotifier) :
    __video_duration = 0
    __video_position = 0
    __video_position_timeout = None

    def __init__(self, **properties):
        GNotifier.__init__(self, **properties)

        # setting up the player pipeline
        self.playbin = Gst.ElementFactory.make('playbin3', None)
        if not self.playbin :
            print("'playbin' gstreamer plugin missing\n")
            sys.stderr.write("'playbin' gstreamer plugin missing\n")
            sys.exit(1)
        else:
            print("loaded playbin plugin")
        self.playerFactory = self.playbin.get_factory()
        self.gtksink = self.playerFactory.make('gtksink')
        self.playbin.set_property("video-sink", self.gtksink)
        # self.gtksink.props.widget.show()

        self.pipeline = Gst.Pipeline()
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.onEOS)
        self.bus.connect('message::error', self.onVideoError)
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.onSyncMessage)
        self.pipeline.add(self.playbin)

        GObject.timeout_add(100, self.triggerVideoPosition)

    def packGtkBoxWidget(self, video_gtk_box):
        ## adding to the gtkbox ui
        video_gtk_box.pack_end(self.gtksink.props.widget, True, True, 0)
        self.gtksink.props.widget.show()


    def triggerVideoPosition(self):
        self.set_property("video-position", -1)
        return True

    @GObject.Property(type=bool, default=False)
    def video_playing(self):
        for x in self.pipeline.get_state(10000) :
            if type(x) is Gst.State and x == Gst.State.PLAYING :
                return True
        return False

    @video_playing.setter
    def video_playing(self, value):
        print("Video playing setter:", value)
        self.pipeline.set_state(Gst.State.PLAYING if value else Gst.State.PAUSED)

    @property
    def video_duration(self):
        success, duration = self.pipeline.query_duration(Gst.Format.TIME)
        if success and self.__video_duration != duration :
            self.__video_duration = duration
            # send signal
        return self.__video_duration

    @GObject.Property(type=GObject.TYPE_LONG)
    def video_position(self):
        success, position = self.pipeline.query_position(Gst.Format.TIME)
        if success and position != self.__video_position:
            #print (position)
            self.__video_position = position
        return self.__video_position

    @video_position.setter
    def video_position(self, value):
        if value < 0 : return
        self.seek(value, Gst.Format.TIME)

    def load(self, path):
        self.pause()

        # testing
        # path = "https://www.freedesktop.org/software/gstreamer-sdk" + \
        #                                 "/data/media/sintel_trailer-480p.webm"

        # original
        url_path = path if Gst.uri_is_valid(path) else Gst.filename_to_uri(path)
        uri = url_path
        print("Loading uri path: ", uri, "Original Path: ", path)

        self.pipeline.set_state(Gst.State.READY)
        self.playbin.set_property('uri', uri)

        # print("self.video_player.get_property('window')", self.video_player.get_property('window'))
        # print("xid", getXid(self.video_player.get_property('window')))

        self.play()
        self.pause()

    def playpause(self, *dontcare):
        # self.xid = getXid(self.video_player.get_property('window'))

        self.video_playing = not self.video_playing

    def play(self, *dontcare):
        # self.xid = getXid(self.video_player.get_property('window'))
        self.video_playing = True

    def pause(self, *dontcare):
        # self.xid = getXid(self.video_player.get_property('window'))
        self.video_playing = False

    def relativeSeek(self, button):
        offset = int(button.get_name().replace('seek:','')) * Gst.FRAME
        self.video_position += offset

    def seek(self, position, format = Gst.Format.TIME):
        return self.pipeline.seek_simple(
            format,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE,
            position)

    def onSyncMessage(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            print('prepare-window-handle XID:', self.xid)
            msg.src.set_window_handle(self.xid)

            print(msg)
            print(msg.src)

    def onEOS(self, bus, msg):
        print('onEOS(): seeking to start of video')
        self.pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            0
        )

    def onVideoError(self, bus, msg):
        print('onVideoError():', msg.parse_error())