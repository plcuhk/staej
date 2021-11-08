## Bug fixed compared to original repository

1. Solving matlab axis data type issue

    in ```matpllotlibdrawingarea.py```
    Changing line 89-90 and 130-131 to
    ```
    highlight.set_xdata(np.asarray(x))
    highlight.set_ydata(np.asarray(y))
    ```
    such that the axis data is np.array instead of list


2. Solving video unable to play normally issue

    Reference: [Stackoverflow: How to show a video in a Gtk dialog?](https://stackoverflow.com/questions/40563216/how-to-show-a-video-in-a-gtk-dialog) Reply from ```gcurse```.

    Using gstreamer's ```gtksink``` and pack it into the gtk box widget instead.
    
## Side note

- ```Import gi``` issue
```
sudo apt install libgirepository1.0-dev
pip install pygobject
```

- Other python packages required
```
pip install matplotlib
pip install peewee
```

- Make sure you have the ```playbin3``` and ```gtksink``` gstreamer plugins installed
```
gst-inspect-1.0 | grep 'playbin3\|gtksink'
```