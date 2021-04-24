#!/usr/bin/env python3
import os
import signal
import subprocess
import sys

import gpiozero
import time
import click
from functools import partial
import logging
from typing import TypedDict, Optional

TRIGGER_BUTTON_PIN = 5
RESET_BUTTON_PIN = 6

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


class ConfigDict(TypedDict):
    """A dict representing all the values passed from running the command through click.

    :param command: The command to run when the button is pressed.
    :type command: str
    :param endcommand: The command to run when the timeout has passed.
    :type endcommand: str, None
    :param wait: The time to wait before running the endcommand if an endcommand is passed.
    :type wait: int in seconds
    :param reset: Option to allow resetting the device.
    :type reset: bool
    :param verbose: Log level to use. 0 = WARNING, 1 = INFO, 2 = DEBUG.
    :type verbose: int
    :param reset_pin: GPIO pin for resetting the device.
    :type reset_pin: int
    :param button_pin: GPIO pin for the button.
    :type button_pin: int
    :param quiet: Disable script output.
    :type quiet: bool
    """
    command: str
    endcommand: Optional[str]
    wait: int
    reset: bool
    verbose: int
    reset_pin: int
    button_pin: int
    quiet: bool


def on_reset_button():
    """Resets the device"""
    logger.info("Reset button pressed. Rebooting machine.")
    try:
        subprocess.run(["sudo", "reboot", "-f"])
    except:
        logger.error("Could not reboot machine:", sys.exc_info()[0])


def on_trigger(config: ConfigDict):
    """Runs a command

    Optionally runs another command after a timeout.
    """
    logger.info("Running command...")
    try:
        output = subprocess.run([config["command"]], capture_output=True)
    except:
        logger.error("Error running command:", sys.exc_info()[0])
    else:
        if output.returncode:
            logger.warning("Command exited with error code %s", output.returncode)
        if not config["quiet"]:
            logger.info("Command output:\n%s", output.stdout.decode("utf-8"))
    if config["endcommand"] is not None:
        logger.debug("Waiting %s seconds before running timeout command", config["wait"])
        time.sleep(config["wait"])
        on_timeout(config)


def on_timeout(config: ConfigDict):
    """Runs a command"""
    logger.debug("Timeout. Calling end command...")
    try:
        output = subprocess.run([config["endcommand"]], capture_output=True)
    except:
        logger.error("Error running timeout command:", sys.exc_info()[0])
    else:
        if output.returncode:
            logger.warning("Timeout command exited with error code %s", output.returncode)
        if not config["quiet"]:
            logger.info("Command output:\n%s", output.stdout.decode("utf-8"))


@click.command()
@click.argument(
    "command",
    type=click.STRING,
    envvar="command"
)
@click.argument(
    "endcommand",
    type=click.STRING,
    envvar="endcommand",
    required=False
)
@click.option(
    '--wait',
    type=click.IntRange(
        min=0,
        clamp=True
    ),
    envvar="wait",
    default=120,
    help="Number of seconds to wait before running disable script.",
)
@click.option(
    '--allow-reset',
    "reset",
    is_flag=True,
    default=False,
    envvar="allowreset",
    help="Enables the possibility of restarting the machine by buttonpress",
)
@click.option(
    "-v",
    "--verbose",
    default=0,
    count=True,
    help="Defaults to warnings only. One v is info. Two v is debug.",
)
@click.option(
    "--reset-pin",
    type=click.IntRange(
        min=1,
        max=21,
    ),
    envvar="reset_pin",
    default=RESET_BUTTON_PIN,
    help="Pin to listen for reset signal",
)
@click.option(
    "--button-pin",
    type=click.IntRange(
        min=1,
        max=21,
    ),
    envvar="button_pin",
    default=TRIGGER_BUTTON_PIN,
    help="Pin to listen for button signal",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    default=False,
    envvar="quiet",
    help="Disables logging of command outputs",
)
def main(**kwargs: ConfigDict):
    """Runs a command when the button connected to pin 5 is pressed.
    If you enter a second command it will be run after a configureable amount of time after the first command.
    The pin can be configured with the --button-pin option.
    
    Also restarts the machine if button connected to pin 6 is pressed.
    This feature is enabled by using the --allow-reset flag.
    The pin can be configured with the --reset-pin option.
    """
    config = ConfigDict(**kwargs)  # Hack to get around typing limitations
    logger.setLevel(logging.WARNING - (config["verbose"] * 10))

    logger.info("Setting up...")
    if kwargs["reset"]:
        logging.info("Enabling reset button on pin %s", config["reset_pin"])
        reset_button = gpiozero.Button(config["reset_pin"], bounce_time=0.1)
        reset_button.when_activated = on_reset_button

    logging.info("Enabling button on pin %s", kwargs["button_pin"])
    script_button = gpiozero.Button(config["button_pin"], bounce_time=0.1)
    script_button.when_activated = partial(on_trigger, config)

    logger.info("Ready. Waiting for button presses.")
    try:
        signal.pause()
    except AttributeError:
        # Workaround for Windows not having signal.pause()
        os.system("pause")


if __name__ == '__main__':
    main()
