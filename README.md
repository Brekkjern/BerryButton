# BerryButton

```
Usage: berrybutton.py [OPTIONS] COMMAND [ENDCOMMAND]

  Runs a command when the button connected to pin 5 is pressed. If you enter
  a second command it will be run after a configureable amount of time after
  the first command. The pin can be configured with the --button-pin option.

  Also restarts the machine if button connected to pin 6 is pressed. This
  feature is enabled by using the --allow-reset flag. The pin can be
  configured with the --reset-pin option.

Options:
  --wait INTEGER RANGE        Number of seconds to wait before running disable
                              script.

  --allow-reset               Enables the possibility of restarting the
                              machine by buttonpress

  -v, --verbose               Defaults to warnings only. One v is info. Two v
                              is debug.

  --reset-pin INTEGER RANGE   Pin to listen for reset signal
  --button-pin INTEGER RANGE  Pin to listen for button signal
  --help                      Show this message and exit.
```

