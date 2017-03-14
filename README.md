# abcc
Automatic Best Connection Chooser - simple daemon to choose the best connection
in Linux system.

Description
---------
abcc is simple daemon written in Python. It periodically measures quality of
avaliable connections. In order to do this, it temporarily sets routing to given
IP via tested interface. When all interfaces are tested, the best is chosen and
default routing is switched to this interface. Switching is done by helper
scripts (plugins) written in Bash. User can set weights of parameters and IPs
in the configuration file. Logs are send to syslog.

Requirements
---------

Configuration
---------

Usage
---------

License
---------
See LICENSE file
