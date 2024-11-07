# Optmybat

Manages a Sungrow hybrid inverter with connected battery to get the most out of the battery.
It's primary goals are:

1. Reduce the wear on the battery by preventing it from falling to 0%
2. Optimise mains power usage by maintaining a minimum charge during low cost periods to ensure
   that there is sufficient charge to avoid drawing mains power during high cost periods

The provided sample config (`config/sample-config.yml`) explains the logic in some detail.

## The big picture

Sungrow Hybrid Inverters with the WiNet-S dongle provide a web interface at https://<your.inverter.host.here>.
Using this web interface, you can login as an administrator to view and edit various configuration parameters
(aka registers).
One set of those parameters (`Energy Management Parameters`) controls force charging and,
using the force charging parameters, you can:

- enable or disable force charging
- if enabled, specify whether it applies on week days only or all days of the week
- if enabled, define up to two time ranges and target battery state of charges (SOCs)
- if the time on the inverter is in one of the specified ranges, it will:
  - disable discharging - the battery __WILL NOT__ be used even if it has more charge than the target
  - it will draw solar and/or mains power to charge the battery to the target SOC
  - if there is excess solar, the solar will charge the battery even if the battery is already charged
    to more than the target

Optmybat uses the same calls (but not the actual web interface) to manipulate the force charging parameters.

## Compatibility

Optmybat was developed by reverse engineering the WiNet-S web interface (https://<your.inverter.host.here>)
against the following devices:

- A Sungrow SH5.0RS hybrid inverter
- A Sungrow SBR128 battery
- A Sungrow WiNet-S dongle (version M_WiNet-S_V01_V01_A)

My expectation is that, regardless of which battery is attached, Optmybat will be compatible with any Sungrow
hybrid inverter using a WiNet-S dongle but I make no gaurantees about compatibility with other devices.
I would however be interested in hearing from anybody who tries it out with other devices and possibly
working with you to get your devices supported.

## Firmware versions

### WINET-SV200.001.00.P024

With the release of the WNet-S firmware `WINET-SV200.001.00.P024`, Sungrow have finally made some small steps
to securing the devices.  Most importanly, it no longer provides any unauthenticated access to the device and
it also requires you to change the password before you can access the device.  As a result, you can no longer
simply use the default login credentials.

If optmybat shows a `401 - I18N_COMMON_INTER_ABNORMAL` error, you will need to go to the web interface, login
and change the password:

- Go to `http://<inverter>` where `<inverter>` is the name or IP address of the hybrid inverter
- You will be prompted to login - use `admin` and either `pw8888` (the default password) or whatever
  password you previously configured
- You will then be prompted to enter a new password which must obey the rules shown in the dialogue
- Update `config/config.yml` to use your new password

### WINET-SV200.001.00.P026

With the release of the WNet-S firmware `WINET-SV200.001.00.P026`, Sungrow have further tightened up the security
of the devices by using TLS for all communications.  Instead of using port 80 for the UI and port 8082 for
websocket, all traffic must now use port 443.

It appears that they are using the same, self-signed certificate for all WiNet-S dongles:

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number:
            69:e8:fb:aa:0c:31:f9:0d:60:42:9a:14:2c:55:52:80:c7:87:4c:fa
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=CN, ST=AnHui, L=HeFei, OU=Sungrow, CN=Sungrow
        Validity
            Not Before: Mar 30 10:16:35 2023 GMT
            Not After : Mar 27 10:16:35 2033 GMT
        Subject: C=CN, ST=AnHui, L=HeFei, OU=Sungrow, CN=Sungrow
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    00:f5:a9:50:ae:56:15:4e:a5:67:68:85:87:8d:dd:
                    4b:c9:4b:5a:fc:67:fd:b9:a5:3c:40:b3:e0:2b:3f:
                    b1:1c:5a:d9:ae:65:92:c5:ce:00:3e:97:c4:d2:11:
                    82:72:8c:ea:e5:f3:b8:79:29:28:2b:85:0c:72:d7:
                    9b:3d:62:58:82:40:a4:b5:aa:4f:be:43:8a:ef:7c:
                    2c:b5:77:d1:c6:4b:68:0f:ad:6d:06:07:ff:ee:33:
                    5d:fb:73:18:a5:37:7e:ee:ad:35:cc:9b:02:3c:95:
                    02:2c:a7:d0:73:1a:0c:cf:15:98:ca:9c:ad:d9:8c:
                    70:2f:78:ab:6a:8d:df:23:30:52:ed:6a:7b:ef:34:
                    22:4a:fb:2f:c2:fb:9e:e6:76:67:92:5a:5a:97:65:
                    06:59:83:a0:cd:2e:58:b6:56:c7:60:f1:0d:c1:4f:
                    23:27:d8:3b:cc:be:48:f6:80:e7:75:63:24:b5:1c:
                    65:7c:fa:f1:eb:e0:7e:1e:f3:21:b1:48:bc:10:46:
                    b2:b5:f6:00:8f:03:1c:63:04:78:16:99:e7:1d:2c:
                    2f:5c:c3:d4:47:a0:67:0d:ad:15:42:40:7e:d4:42:
                    f7:05:8f:7b:aa:15:ea:18:82:39:da:a6:19:dd:4f:
                    69:02:aa:be:0e:b2:9e:ef:a6:f0:73:78:f6:89:42:
                    f7:83
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 Basic Constraints: 
                CA:FALSE
            X509v3 Key Usage: 
                Digital Signature, Non Repudiation, Key Encipherment
            X509v3 Subject Alternative Name: 
                IP Address:169.254.12.12, IP Address:11.11.11.1, IP Address:127.0.0.1
    Signature Algorithm: sha256WithRSAEncryption
    Signature Value:
        32:d1:ca:03:c3:32:9b:ce:d0:85:97:6d:5e:8a:5f:0d:10:9a:
        71:9a:d7:73:3b:67:24:0a:cf:83:f0:a1:30:29:9f:ad:f9:4e:
        8e:86:00:fa:d8:b1:41:3d:3e:c3:1a:e8:36:c9:05:69:9f:37:
        56:47:eb:d4:ee:61:2f:0f:8c:fb:be:f8:07:3c:02:e1:c8:df:
        13:fa:e6:a6:1b:c0:b1:23:2c:46:09:7c:13:60:9e:6a:73:16:
        4d:01:5f:05:0c:0a:e1:84:8f:fe:24:6d:24:9c:07:92:00:e8:
        78:9e:17:f8:91:b5:1e:4b:7a:29:a3:9f:fa:3f:bd:d1:a0:bc:
        5f:32:dc:2f:6a:bb:5e:06:d0:fa:62:0d:60:5b:a0:43:6a:c5:
        c2:ba:ed:58:f3:b4:55:a5:20:8a:75:c9:6a:10:be:99:74:38:
        50:01:aa:34:fd:81:4a:2a:b8:e8:75:50:7d:20:5b:8d:48:4a:
        df:e1:27:7e:9f:e9:b3:68:c7:3a:35:02:b6:f4:6c:f1:6d:09:
        da:2a:43:fb:2c:cd:04:c8:3c:a9:25:50:94:3f:83:33:98:3f:
        3b:c6:52:68:10:26:1f:15:9f:d3:14:3f:5e:8f:55:62:55:5c:
        f0:27:68:75:02:99:5c:a7:53:b0:e9:bf:31:d5:d0:1b:5e:d2:
        28:7c:b1:62
```

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
