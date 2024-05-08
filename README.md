# Optmybat

Manages a Sungrow hybrid inverter with connected battery to get the most out of the battery.
It's primary goals are:

1. Reduce the wear on the battery by preventing it from falling to 0%
2. Optimise mains power usage by maintaining a minimum charge during low cost periods to ensure
   that there is sufficient charge to avoid drawing mains power during high cost periods

The provided sample config (`config/sample-config.yml`) explains the logic in some detail.

## The big picture

Sungrow Hybrid Inverters with the WiNet-S dongle provides a web interface at http://<your.inverter.host.here>.
Using this web interface, you can login as an administrator to view and edit various configuration parameters
(aka registers).
One set of those parameters (`Energy Management Parameters`) controls force charging and,
using the force charging parameters, you can:

- enable or disable force charging
- if enabled, specify whether it applies on week days only or all days of the week
- if enabled, define up to two time ranges and target battery state of charges (SOCs)
- if the time on the inverter is in one of the specified ranges, it will:
  - disable discharging - the battery __WILL NOT__ be used even if it has more charge than the target
  - it will draw solar and/or mains power to charge the battery to the target SOC (actually a little below the target)
  - if there is excess solar, it will charge the battery even if the battery is already charged to more than the target

Optmybat uses the same calls (but not the actual web interface) to manipulate the force charging parameters.

## Compatibility

Optmybat was developed by reverse engineering the WiNet-S web interface (http://<your.inverter.host.here>)
against the following devices:

- A Sungrow SH5.0RS hybrid inverter
- A Sungrow SBR128 battery
- A Sungrow WiNet-S dongle (version M_WiNet-S_V01_V01_A)

My expectation is that, regardless of which battery is attached, Optmybat will be compatible with any Sungrow
hybrid inverter using a WiNet-S dongle but I make no gaurantees about compatibility with other devices.
I would however be interested in hearing from anybody who tries it out with other devices and possibly
working with you to get your devices supported.

## Configuration

Copy `config/sample-config.yml` to `config/config.yml` then edit `config.yml` to, at the least,
update the `sg_host` parameter to the host name or IP address of your hybrid inverter (e.g. `192.168.1.123`).

If you don't know your inverter's address, you can run `optmybat --scan` to search your local network for an
inverter.

## Running it

Optmybat was developed and tested on a Fedora Linux system using Python 3.12.
In theory it should run on other systems but that has not been tried or tested.
If you wish to run it on anything other than Linux, I suggest you build a container
and use podman or docker to run it.

### Directly with Python on Linux

If you are comfortable with Python development, you can run Optmybat directly using a Python virtual environment:

```bash
   cd optmybat     # The location of the git repository
   python -v venv .venv
   source .venv/bin/activate
   pip install --upgrade -r requirements.txt
   ./optmybat
```

If you get any weird errors, it's probably your Python version - check that you are running Python3 at least 3.10 or later.

### Using a container

Alternatively, you can build and run optmybat in a container but there are a couple of complexities with using a container:

- Containers generally run in UTC time - you must set the timezone configuration parameter correctly or ensure that the
  container's time zone is correct using something like `podman run --tz`
- Build the container using the command `podman build -t optmybat --build-arg=IGNORE_TESTS=y .`
- Optmybat is designed to pick up live changes to the config file so you can change its behaviour
  without having to stop and restart it.  For this to work with a container, you have to mount the
  config directory in to the container, using something like:

   ```bash
   podman run --rm --security-opt label=disable --name optmybat -v ./config:/optmybat/config optmybat
   ```

- If you don't know the address of your inverter, you can scan your network to find it using something like:

   ```bash
   podman run --rm optmybat ./optmybat --scan 192.168.1.0/24
   ```

   __NOTE__: You must specify the network if scanning from a container
