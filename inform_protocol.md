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

    "mgmt_cfg": "mgmt.is_default=false\nmgmt.authkey=41d6529fd555fbb1bdeeafeb995510fa\nmgmt.cfgversion=f1bb359840b519a4\nmgmt.servers.1.url=http://172.16.0.38:6080/inform\nmgmt.selfrun_guest=pass\nselfrun_guest=pass\ncfgversion=f1bb359840b519a4\n",
    "port_cfg": "port.0.sensorId=52210822e4b0959e7fe94009\nvpower.1.rep_output=1\nvpower.1.rep_pf=1\nvpower.1.rep_energy_sum=1\nvpower.1.rep_v_rms=1\nvpower.1.rep_i_rms=1\nvpower.1.rep_active_pwr=1\nvpower.1.relay=1\nvpower.1.output_tag=output\nvpower.1.pf_tag=pf\nvpower.1.energy_sum_tag=energy_sum\nvpower.1.v_rms_tag=v_rms\nvpower.1.i_rms_tag=i_rms\nvpower.1.active_pwr_tag=active_pwr\nport.1.sensorId=5221082be4b0959e7fe9400a\nvpower.2.rep_output=1\nvpower.2.rep_pf=1\nvpower.2.rep_energy_sum=1\nvpower.2.rep_v_rms=1\nvpower.2.rep_i_rms=1\nvpower.2.rep_active_pwr=1\nvpower.2.relay=1\nvpower.2.output_tag=output\nvpower.2.pf_tag=pf\nvpower.2.energy_sum_tag=energy_sum\nvpower.2.v_rms_tag=v_rms\nvpower.2.i_rms_tag=i_rms\nvpower.2.active_pwr_tag=active_pwr\nport.2.sensorId=5221083be4b0959e7fe9400b\nvpower.3.rep_output=1\nvpower.3.rep_pf=1\nvpower.3.rep_energy_sum=1\nvpower.3.rep_v_rms=1\nvpower.3.rep_i_rms=1\nvpower.3.rep_active_pwr=1\nvpower.3.relay=0\nvpower.3.output_tag=output\nvpower.3.pf_tag=pf\nvpower.3.energy_sum_tag=energy_sum\nvpower.3.v_rms_tag=v_rms\nvpower.3.i_rms_tag=i_rms\nvpower.3.active_pwr_tag=active_pwr\n",
    "system_cfg": "# users\nusers.status=enabled\nusers.1.name=admin\nusers.1.password=Mq9xt5C8DjcLA\nusers.1.status=enabled\n# bridge\nbridge.status=disabled\nbridge.1.devname=br0\nbridge.1.fd=1\nbridge.1.stp.status=disabled\nbridge.1.port.1.devname=eth1\nsnmp.status=disabled\nppp.status=disabled\npwdog.status=disabled\ndnsmasq.status=disabled\ndhcpd.status=disabled\nhttpd.status=disabled\nhttpd.port.http=80\nhttpd.port=80\nigmpproxy.status=disabled\ntelnetd.status=disabled\ntshaper.status=disabled\nnetmode=bridge\nntpclient.status=disabled\nntpclient.1.server=pool.ntp.org\nntpclient.1.status=disabled\nsyslog.status=enabled\nresolv.status=enabled\nresolv.host.1.name=OfficePowerStrip\nresolv.nameserver.1.status=disabled\nresolv.nameserver.2.status=disabled\ndhcpc.status=enabled\ndhcpc.1.status=enabled\ndhcpc.1.devname=eth1\nroute.status=enabled\nvlan.status=disabled\nradio.1.ack.auto=disabled\nradio.1.ackdistance=300\nradio.1.acktimeout=30\nradio.1.ampdu.status=enabled\nradio.1.clksel=1\nradio.1.countrycode=840\nradio.1.cwm.enable=0\nradio.1.cwm.mode=1\nradio.1.forbiasauto=0\nradio.1.channel=0\nradio.1.ieee_mode=11nght40\nradio.1.mcastrate=auto\nradio.1.mode=managed\nradio.1.puren=0\nradio.1.rate.auto=enabled\nradio.1.rate.mcs=auto\nradio.1.txpower=auto\n# wlans (radio)\nradio.status=enabled\nradio.countrycode=840\naaa.status=disabled\nwireless.status=enabled\ndhcpc.2.status=enabled\ndhcpc.2.devname=ath0\nbridge.1.port.2.devname=ath0\nradio.1.devname=ath0\nradio.1.status=enabled\naaa.1.br.devname=br0\naaa.1.devname=ath0\naaa.1.driver=madwifi\naaa.1.ssid=\naaa.1.status=disabled\nwireless.1.mode=managed\nwireless.1.devname=ath0\nwireless.1.status=enabled\nwireless.1.authmode=1\nwireless.1.l2_isolation=disabled\nwireless.1.is_guest=false\nwireless.1.security=none\nwireless.1.addmtikie=disabled\nwireless.1.ssid=\nwireless.1.hide_ssid=enabled\nwireless.1.mac_acl.status=disabled\nwireless.1.mac_acl.policy=deny\nwireless.1.wmm=enabled\n# netconf\nnetconf.status=enabled\nnetconf.1.devname=eth1\nnetconf.1.autoip.status=disabled\nnetconf.1.ip=0.0.0.0\nnetconf.1.promisc=enabled\nnetconf.1.status=enabled\nnetconf.1.up=enabled\nnetconf.2.devname=br0\nnetconf.2.autoip.status=disabled\nnetconf.2.ip=0.0.0.0\nnetconf.2.status=enabled\nnetconf.2.up=enabled\nnetconf.3.devname=ath0\nnetconf.3.autoip.status=disabled\nnetconf.3.ip=0.0.0.0\nnetconf.3.promisc=enabled\nnetconf.3.status=enabled\nnetconf.3.up=enabled\nqos.status=enabled\nqos.group.1.rate=100\nqos.group.2.rate=100\nqos.group.6.rate=100\nqos.if.1.devname=eth1\nqos.if.1.devspeed=100\nqos.if.1.group=1\nqos.if.2.devname=ath0\nqos.if.2.devspeed=150\nqos.if.2.group=20\n"

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
        analog_cfg: analog port config (empty for mPower)
        authorized_guests: authorized guests file (empty)
        blocked_sta: blocked stations (empty)
        cfgversion: management config version
        mgmt_cfg: management config file
        port_cfg: output port config (set for mPower)
        system_cfg: system config file
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
        default: boolean, device is unconfigured
