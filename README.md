# abcc
Automatic Best Connection Chooser - simple daemon to choose the best connection
in Linux system.

Description
---------
The abcc is simple daemon written in Python. It periodically measures quality of
the internet connections defined in the configuration file. In order to do this,
it temporarily sets, with the help of plugin scripts, routing to defined IP via
currently tested interface.

When all interfaces are tested, the best is chosen and given routing is set to
this interface. Routing switching is also done by helper scripts (plugins)
written in Bash.

The abcc is fully customizable, interface and route aware, so only routes
available on given interface will be set on that interface. User can set weights
of parameters and IPs in the configuration file. Logs are send to syslog.

Requirements
---------
- GNU/Linux
- Pytnon 2.7
- modules listed in requirements.txt

Configuration
---------
Configuration is performed by YAML configruation file, which can be specified
by *--config* parameter. Example configuration is provided in *example.yaml*.

It has two main blocks: *interfaces* and *routes*

The first one contains interfaces names. Each interface has to have set gateway
of the interface and list of routes available on given iterface. Each route has
to be defined in the routes section.

The second one contains information how given route should be tested and how
score for this route should be counted. There are three optional global parameters:
- loss_mult - loss multiplier, which tells how much packet loss counts for given
route
- lag_mult - lag multiplier, which tells how much delay is important for given route
- switch_cost - which prevents switching routing when score difference is too low

For each route there are defined IPs, which will be tested (pinged). Each IP can
have optional parameters:
- multiplier, which increases importance of all results for that IP
- count, which tells how many packets should be send to that IP

Defaults
---------
- lag_mult = 1
- loss_mult = 10
- count = 10

Usage
---------
- clone this repository
- pip install -r requirements.txt
- adjust config file (see example.yaml)
- run with --dry-run True

Contribution
---------
Help is always welcome, so clone this repository, send pull requests or create
issues if you find any bugs.

License
---------
See LICENSE file
