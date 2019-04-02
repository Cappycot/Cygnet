![Cygnet](https://azurlane.koumakan.jp/w/images/5/5f/CygnetKaiChibi.png "Cygnet")
----
# Cygnet

Source code used in making [my new desktop computer](https://pcpartpicker.com/b/CDsZxr).

![Cygnet's Rigging](https://cdn.pcpartpicker.com/static/forever/images/userbuild/250412.938d1f7c93186aa8c8f2e48df6a94192.1600.jpg "The Rig")
----
# Itemized Notes

**Cygnet.ino**

This is the C++ code for the Arduino unit that is connected to the motherboard and chassis.

**icueenums.py and icuestructs.py**

Values for iCUE SDK objects. This was taken from [this repository](https://github.com/10se1ucgo/cue_sdk).

**showtest.py**

This Python program uses the iCUE SDK to control a Corsair Commander Pro and a Corsair MM800 Polaris RGB mousepad. The Commander has 6 LL120 fans on the first channel and 4 Corsair RGB strips on the second. It can play nearly any custom Beat Saber map as a red and blue light show.

**testalarm.py**

This Python program sends a set of bytes to the Arduino through the USB serial to tell it how long to count down before an automatic startup.

**To-Do I am probably going to procrastinate on indefinitely:**

I still need to properly credit the repositories that I drew Corsair iCUE SDK Python code from.
