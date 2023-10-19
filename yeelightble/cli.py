import logging
import click
import sys
import atexit
import redis
import time
from .proxy import ProxyService
from .message import MessageService, Command
from .btle import BTLEScanner
from .lamp import Lamp

pass_dev = click.make_pass_decorator(Lamp)
logger = logging.getLogger(__name__)


def message_handler(proxy_service: ProxyService, message):
    uuid, command = message.get('uuid'), message.get('command', None)
    if uuid and command:
        command, payload = command.get('type'), command.get('payload', None)
        logger.info('message_handler: received message from %s: command=%s and payload=%s' % (uuid, command, payload))
        proxy_service.cmd(uuid, Command(command, payload))
    else:
        logger.warning("message_handler: received invalid message:", message)


def status_cb(data):
    click.echo("Got notification: %s" % data)


@click.group(invoke_without_command=True)
@click.option('--mac', envvar="YEELIGHTBLE_MAC", required=False)
@click.option('-d', '--debug', default=False, count=True)
@click.pass_context
def cli(ctx, mac, debug):
    """ A tool to query Yeelight bedside lamp. """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)s [%(name)s] %(message)s', level=level)

    # if we are scanning, we do not need to connect.
    if ctx.invoked_subcommand == "scan":
        return

    if ctx.invoked_subcommand is None:
        ctx.invoke(daemon)
        return

    if mac is None:
        logger.error("mac address is missing, set YEELIGHTBLE_MAC environment variable or pass --mac option")
        sys.exit(1)

    ctx.obj = Lamp(mac, status_cb)


@cli.command()
@click.option('--redis-host', envvar="YEELIGHTBLE_REDIS_HOST", default='localhost', show_default=True)
@click.option('--redis-port', envvar="YEELIGHTBLE_REDIS_PORT", default=6379, show_default=True)
def daemon(redis_host, redis_port):
    """Starts yeelightble daemon, you shouldn't invoke it directly, but by adding yeelightble.service to systemd"""
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    message_service = MessageService(redis_client)
    proxy_service = ProxyService(message_service)
    message_service.subscribe_control(lambda message: message_handler(proxy_service, message))
    atexit.register(redis_client.close())


@cli.command()
@click.argument("timeout", default=5, required=False)
def scan(timeout):
    scanner = BTLEScanner(timeout=timeout)
    scanner.scan()


@cli.command(name="info")
@pass_dev
def device_info(dev: Lamp):
    """Returns hw & sw version."""
    dev.get_version_info()
    dev.wait_for_notifications()
    dev.get_serial_number()
    dev.wait_for_notifications()


@cli.command(name="time")
@click.argument("new_time", default=None, required=False)
@pass_dev
def time_(dev: Lamp, new_time):
    """Gets or sets the time."""
    if new_time:
        click.echo("Setting the time to %s" % new_time)
        dev.set_time(new_time)
    else:
        click.echo("Requesting time.")
        dev.get_time()


@cli.command()
@pass_dev
def on(dev: Lamp):
    """ Turns the lamp on. """
    dev.turn_on()


@cli.command()
@pass_dev
def off(dev: Lamp):
    """ Turns the lamp off. """
    dev.turn_off()


@cli.command()
@pass_dev
def wait_for_notifications(dev: Lamp):
    """Wait for notifications."""
    dev.wait_for_notifications()


@cli.command()
@click.argument("brightness", type=int, default=None, required=False)
@pass_dev
def brightness(dev: Lamp, brightness):
    """ Gets or sets the brightness. """
    if brightness:
        click.echo("Setting brightness to %s" % brightness)
        dev.set_brightness(brightness)
    else:
        click.echo("Brightness: %s" % dev.brightness)


@cli.command()
@click.argument("red", type=int, default=None, required=False)
@click.argument("green", type=int, default=None, required=False)
@click.argument("blue", type=int, default=None, required=False)
@click.argument("brightness", type=int, default=None, required=False)
@pass_dev
def color(dev: Lamp, red, green, blue, brightness):
    """ Gets or sets the color. """
    if red or green or blue:
        click.echo("Setting color: %s %s %s (brightness: %s)" % (red, green, blue, brightness))
        dev.set_color(red, green, blue, brightness)
    else:
        click.echo("Color: %s" % (dev.color,))


@cli.command()
@pass_dev
def name(dev: Lamp):
    dev.get_name()
    dev.wait_for_notifications()


@cli.command()
@click.argument("number", type=int, default=255, required=False)
@click.argument("name", type=str, required=False)
@pass_dev
def scene(dev: Lamp, number, name):
    if name:
        dev.set_scene(number, name)
    else:
        dev.get_scene(number)


@cli.command()
@click.argument("number", type=int, default=255, required=False)
@pass_dev
def alarm(dev: Lamp, number):
    """Gets alarms."""
    dev.get_alarm(number)


@cli.command()
@pass_dev
def night_mode(dev: Lamp):
    """Gets or sets night mode settings."""
    dev.get_nightmode()


@cli.command()
@click.argument("number", type=int, default=255, required=False)
@pass_dev
def flow(dev: Lamp, number):
    dev.get_flow(number)


@cli.command()
@click.argument("time", type=int, default=0, required=False)
@pass_dev
def sleep(dev: Lamp, time):
    dev.get_sleep()


@cli.command()
@pass_dev
def state(dev: Lamp):
    """ Requests the state from the device. """
    dev.state()
    dev.wait_for_notifications()
    click.echo("MAC: %s" % dev.mac)
    click.echo("State: %s" % dev.state())
    click.echo("Mode: %s" % dev.mode)
    click.echo("Color: %s" % (dev.color,))
    click.echo("Temperature: %s" % dev.temperature)
    click.echo("Brightness: %s" % dev.brightness)


@cli.command()
@pass_dev
def mode(dev: Lamp):
    click.echo("Mode: %s" % dev.mode)


@cli.command()
@click.argument('temperature', type=int, default=None, required=False)
@click.argument('brightness', type=int, default=None, required=False)
@pass_dev
def temperature(dev: Lamp, temperature, brightness):
    """ Gets and sets the color temperature 1700-6500K """
    if temperature:
        click.echo("Setting the temperature to %s (brightness: %s)" % (temperature, brightness))
        dev.set_temperature(temperature, brightness)
    else:
        click.echo("Temperature: %s" % dev.temperature)


if __name__ == "__main__":
    cli()
