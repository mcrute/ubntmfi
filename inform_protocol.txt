Ubiquiti Inform Protocol
========================

The mFi uses the Ubiquiti inform protocol to handle all communications to and
from the controller. This is the way that it transmits the current state of the
system to the controller (looks like it just sends mca-dump output) as well as
how it receives the instructions from the controller as to what to enable or
disable.

Everything appears to be pull-based, even provisioning. This makes sense with
the cloud controller where the controller has no access to your network. I
haven't documented yet how anything works within the protocol, that's next.
This documents the overall protocol itself.

The device will inform by executing an HTTP POST with an encrypted payload to
http://controller:6080/inform at a regular interval (default is 10 seconds) and
will expect an encrypted payload to be returned. If the device gets a command
response instead of a noop response it will immediately do another inform; this
continues until the controller sends the next noop response. Responses never
appear to contain multiple commands.

Raw Packet Structure
--------------------
4 bytes          magic number            integer
4 bytes          version                 integer
6 bytes          hwaddr                  string
2 bytes          flags                   short
16 bytes         initialization vector   string
4 bytes          data version            integer
4 bytes          data length             integer
n bytes          encrypted payload       string

Raw Packet Constraints
----------------------
magic must == 1414414933
data version must < 1
flags & 0x1 != 0 means encrypted
flags & 0x2 != 0 means compressed

Payload Types
-------------
The payload is AES encrypted in CBC mode using PKCS5 padding. They key is the
device auth key from the database or a master key that is hard coded if the
device hasn't been provisioned yet. The master key is hard coded in the
controller code in the DeviceManager class and pretty easy to find.

MASTER_KEY = "ba86f2bbe107c7c57eb5f2690775c712"

On devices running protocol version 1 the encrypted payload is just JSON data.
In version 0 of the protocol the data was key=value pairs separated by
newlines. All of the mFi hardware I have access to uses protocol version 1.

The payloads break down into two categories; those coming into the controller
and those going out of the controller.

Output Payloads
---------------
Output payloads are those that originate from the controller and are bound for
the device. These always appear to contain a _type field. I have observed the
following output payloads.

    _type: firmware upgrade (upgrade)
        url: full url to firmware.bin
        datetime: rfc3339 formatted date, server time
        server_time_in_utc: server time in UTC as a unix timestamp (string)
        version: firmware version (string)
        time: server time as unix timestamp (int)
        _id: unknown id string (5232701de4b0457a2f2f031f)
        device_id: device ID from mongodb

    _type: config update (setparam)
        port_cfg: configuration for ports as string
        server_time_in_utc: server time in UTC as a unix timestamp (string)


    _type: reboot (reboot)
        datetime: rfc3339 formatted date, server time
        device_id: device ID from mongodb

    _type: heartbeat (noop)
        interval: next checkin time in seconds (integer)

    _type: command (cmd)
        _admin: admin data object
            _id: mongodb id of admin
            lang: admin language (en_US)
            name: admin username
            x_password: admin password
        _id: unknown id string (5232701de4b0457a2f2f031f)
        datetime: rfc3339 formatted date, server time
        server_time_in_utc: server time in UTC as a unix timestamp (string)
        time: server time as unix timestamp (int)
        device_id: device ID from mongodb
        cmd: command to use (mfi-output)
        mac: device mac address
        model: device model (Outlet for mPower)
        off_volt: ?? (int)
        port: device port to update (int)
        sId: sensor ID
        timer: ?? (int)
        val: output value (int)
        volt: ?? (int)

    // val and volt set to 1 to turn on, 0 to turn off


Input Payloads
--------------
Incoming packets appear to be a JSON version of the out put of the `mca-dump`
command on the device. There is definitely some AirOS legacy in here. I don't
document the whole input payload since most of it isn't interesting.

    callback from device: javascript object
        alarm: list of sensors
            index: port name
            sId: sensor ID hash
            time: device time

            // For mPort Only
            tag: kind of reading presented (magnetic, temperature, humidity)
            type: kind of device (input, analog, output)
            val: value (float)

            // For mPower Only
            entries: list of entry objects
                tag: kind of reading (output, pf, energy_sum, v_rms, i_rms, active_pwr)
                type: sensor type (output, analog, rmsSum, rms)
                val: value (float)

        hostname: hostname of device ("ubnt" unless changed)
        ip: IP of device
        mac: mac address of primary interface
        mfi: boolean, indicates if an mfi device
        model: device model name
        model_display: display name for device
        serial: device serial number
        uptime: uptime in seconds since last reboot
        version: firmware version
