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

TRIGGER_BUTTON_PIN = 5
RESET_BUTTON_PIN = 6

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


def on_reset_button():
    """Resets the device"""
    logger.info("Reset button pressed. Rebooting machine.")
    try:
        subprocess.run(["sudo", "reboot", "-f"])
    except:
        logger.error("Could not reboot machine:", sys.exc_info()[0])


def on_trigger(script: str, timeout_command: str, wait: int):
    """Runs a command

    Optionally runs another command after a timeout.
    """
    logger.info("Running command...")
    try:
        output = subprocess.run([script], capture_output=True)
    except:
        logger.error("Error running command:", sys.exc_info()[0])
    else:
        if output.returncode:
            logger.warning("Command exited with error code %s", output.returncode)
        logger.info("Command output:\n%s", output.stdout.decode("utf-8"))
    if timeout_command is not None:
        logger.debug("Waiting %s seconds", wait)
        time.sleep(wait)
        on_timeout(timeout_command)


def on_timeout(command: str):
    """Runs a command"""
    logger.debug("Timeout. Calling end command.")
    try:
        output = subprocess.run([command], capture_output=True)
    except:
        logger.error("Error running timeout command:", sys.exc_info()[0])
    else:
        if output.returncode:
            logger.warning("Timeout command exited with error code %s", output.returncode)
        logger.info("Command output:\n%s", output.stdout)


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
def main(command: str, endcommand: str, wait: int, reset: bool, verbose: int, reset_pin: int, button_pin: int):
    f"""Runs a command when the button connected to pin {TRIGGER_BUTTON_PIN} is pressed.
    If you enter a second command it will be run after a configureable amount of time after the first command.
    
    Also restarts the machine if button connected to pin {RESET_BUTTON_PIN} is pressed.
    This feature is enabled by using the --allow-reset flag.
    """

    logger.setLevel(logging.WARNING - (verbose * 10))

    logger.info("Setting up...")
    if reset:
        logging.info("Enabling reset button on pin %s", reset_pin)
        reset_button = gpiozero.Button(reset_pin, bounce_time=0.1)
        reset_button.when_activated = on_reset_button

    logging.info("Enabling button on pin %s", button_pin)
    script_button = gpiozero.Button(button_pin, bounce_time=0.1)
    script_button.when_activated = partial(on_trigger, command, endcommand, wait)

    logger.info("Ready. Waiting for button presses.")
    try:
        signal.pause()
    except AttributeError:
        # Workaround for Windows not having signal.pause()
        os.system("pause")


if __name__ == '__main__':
    main()