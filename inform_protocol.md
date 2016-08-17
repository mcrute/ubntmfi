# Ubiquiti Inform Protocol

The mFi uses the Ubiquiti inform protocol to handle all communications to and
from the controller. This is the way that it transmits the current state of the
system to the controller (looks like it just sends mca-dump output) as well as
how it receives the instructions from the controller as to what to enable or
disable.

Everything appears to be pull-based, even provisioning. This makes sense with
the cloud controller where the controller has no access to your network. I
have not documented yet how anything works within the protocol, that is next.
This documents the overall protocol itself.

The device will inform by executing an HTTP POST with an encrypted payload to
http://controller:6080/inform at a regular interval (default is 10 seconds) and
will expect an encrypted payload to be returned. If the device gets a command
response instead of a noop response it will immediately do another inform; this
continues until the controller sends the next noop response. Responses never
appear to contain multiple commands.

## Raw Packet Structure
| Size     | Purpose               | Data Type |
| -------- | --------------------- | --------- |
| 4 bytes  | magic number          | integer   |
| 4 bytes  | version               | integer   |
| 6 bytes  | hwaddr                | string    |
| 2 bytes  | flags                 | short     |
| 16 bytes | initialization vector | string    |
| 4 bytes  | data version          | integer   |
| 4 bytes  | data length           | integer   |
| n bytes  | AES encrypted payload | string    |

## Raw Packet Constraints
* magic must == `1414414933` (TNBU)
* data version must < `1`
* `flags & 0x1 != 0` means encrypted
* `flags & 0x2 != 0` means compressed

## Payload Types
The payload is AES encrypted in CBC mode using PKCS5 padding. They key is the
device auth key from the database or a master key that is hard coded if the
device has not been provisioned yet. The master key is hard coded in the
controller code in the DeviceManager class and pretty easy to find.

    MASTER_KEY = "ba86f2bbe107c7c57eb5f2690775c712"

On devices running protocol version 1 the encrypted payload is just JSON data.
In version 0 of the protocol the data was key=value pairs separated by
newlines. All of the mFi hardware I have access to uses protocol version 1.

The payloads break down into two categories; those coming into the controller
and those going out of the controller.


## Output Payloads
Output payloads are those that originate from the controller and are bound for
the device. These always appear to contain a \_type field. I have observed the
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


## Input Payloads
Incoming packets appear to be a JSON version of the out put of the `mca-dump`
command on the device. There is definitely some Unifi legacy in here. It
appears that mFi is just using the Unfi firmware and has hacked it a bit for
their use-case so most of the fields outside of alarm are not relevant to the
mFi use-case.

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

        if_table: list of interfaces and stats
            ip: interface ip
            mac: interface mac address
            name: interface device name (dev handle)
            rx_bytes: bytes received on the interface
            rx_dropped: packets dropped by the interface
            rx_errors: receive errors on the interface
            rx_packets: packets received on the interface
            tx_bytes: bytes transmitted by the interface
            tx_dropped: trasmit drops on the interface
            tx_errors: transmit errors on the interface
            tx_packets: number of packets transmitted by the interface
            type: appears to be the same as name

        radio_table: list of radios in the device
            builtin_ant_gain: gain of builtin antenna
            builtin_antenna: boolean, does device have antenna
            max_txpower: maximum transmit power
            name: name of radio
            radio: radio type (ex: ng)
            scan_table: list, unknown
            
        vap_table: table of joined wireless networks
            bssid: network SSID
            ccq: client connection qality
            channel: channel number
            essid: network friendly name
            id: mode? (ex: user)
            name: uplink device name
            num_sta: number of connected stations (always 0)
            radio: radio type (ex: ng)
            rx_bytes: bytes received on the interface
            rx_dropped: packets dropped by the interface
            rx_errors: receive errors on the interface
            rx_packets: packets received on the interface
            tx_bytes: bytes transmitted by the interface
            tx_dropped: trasmit drops on the interface
            tx_errors: transmit errors on the interface
            tx_packets: number of packets transmitted by the interface
            rx_crypts: unknown
            rx_frags: received fragmented packets
            rx_nwids: received network beacons
            tx_power: transmitting power of the radio (assumed in dBm)
            tx_retries: number of transmit retries on interface
            usage: same as id

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
        cfgversion: string, unknown (ex: c3846443e1b4860b)
        guest_token: string, unknown (ex: 364E8B215D16AB963A53232E3873000C)
        inform_url: string, url to which the device is reporting
        isolated: boolean, can the device reach the rest of the network
        localversion: string, unknown (ex: ?)
        locating: boolean, is the device in locating mode (blinking LED)
        portversion: string, unknown (ex: 443eb55240f26367)
        time: integer, device time as unix timestamp
        trackable: boolean as string, unknown
        uplink: string, unix device name (dev handle) of the primary uplink device


## Config Samples
These are some observed configuration payloads for the configuration packets.

### mgmt cfg
    mgmt.is_default=false
    mgmt.authkey=41d6529fd555fbb1bdeeafeb995510fa
    mgmt.cfgversion=f1bb359840b519a4
    mgmt.servers.1.url=http://172.16.0.38:6080/inform
    mgmt.selfrun_guest=pass
    selfrun_guest=pass
    cfgversion=f1bb359840b519a4


### port cfg
    port.0.sensorId=52210822e4b0959e7fe94009
    vpower.1.rep_output=1
    vpower.1.rep_pf=1
    vpower.1.rep_energy_sum=1
    vpower.1.rep_v_rms=1
    vpower.1.rep_i_rms=1
    vpower.1.rep_active_pwr=1
    vpower.1.relay=1
    vpower.1.output_tag=output
    vpower.1.pf_tag=pf
    vpower.1.energy_sum_tag=energy_sum
    vpower.1.v_rms_tag=v_rms
    vpower.1.i_rms_tag=i_rms
    vpower.1.active_pwr_tag=active_pwr
    port.1.sensorId=5221082be4b0959e7fe9400a
    vpower.2.rep_output=1
    vpower.2.rep_pf=1
    vpower.2.rep_energy_sum=1
    vpower.2.rep_v_rms=1
    vpower.2.rep_i_rms=1
    vpower.2.rep_active_pwr=1
    vpower.2.relay=1
    vpower.2.output_tag=output
    vpower.2.pf_tag=pf
    vpower.2.energy_sum_tag=energy_sum
    vpower.2.v_rms_tag=v_rms
    vpower.2.i_rms_tag=i_rms
    vpower.2.active_pwr_tag=active_pwr
    port.2.sensorId=5221083be4b0959e7fe9400b
    vpower.3.rep_output=1
    vpower.3.rep_pf=1
    vpower.3.rep_energy_sum=1
    vpower.3.rep_v_rms=1
    vpower.3.rep_i_rms=1
    vpower.3.rep_active_pwr=1
    vpower.3.relay=0
    vpower.3.output_tag=output
    vpower.3.pf_tag=pf
    vpower.3.energy_sum_tag=energy_sum
    vpower.3.v_rms_tag=v_rms
    vpower.3.i_rms_tag=i_rms
    vpower.3.active_pwr_tag=active_pwr


### system cfg
    # users
    users.status=enabled
    users.1.name=admin
    users.1.password=Mq9xt5C8DjcLA
    users.1.status=enabled
    # bridge
    bridge.status=disabled
    bridge.1.devname=br0
    bridge.1.fd=1
    bridge.1.stp.status=disabled
    bridge.1.port.1.devname=eth1
    snmp.status=disabled
    ppp.status=disabled
    pwdog.status=disabled
    dnsmasq.status=disabled
    dhcpd.status=disabled
    httpd.status=disabled
    httpd.port.http=80
    httpd.port=80
    igmpproxy.status=disabled
    telnetd.status=disabled
    tshaper.status=disabled
    netmode=bridge
    ntpclient.status=disabled
    ntpclient.1.server=pool.ntp.org
    ntpclient.1.status=disabled
    syslog.status=enabled
    resolv.status=enabled
    resolv.host.1.name=OfficePowerStrip
    resolv.nameserver.1.status=disabled
    resolv.nameserver.2.status=disabled
    dhcpc.status=enabled
    dhcpc.1.status=enabled
    dhcpc.1.devname=eth1
    route.status=enabled
    vlan.status=disabled
    radio.1.ack.auto=disabled
    radio.1.ackdistance=300
    radio.1.acktimeout=30
    radio.1.ampdu.status=enabled
    radio.1.clksel=1
    radio.1.countrycode=840
    radio.1.cwm.enable=0
    radio.1.cwm.mode=1
    radio.1.forbiasauto=0
    radio.1.channel=0
    radio.1.ieee_mode=11nght40
    radio.1.mcastrate=auto
    radio.1.mode=managed
    radio.1.puren=0
    radio.1.rate.auto=enabled
    radio.1.rate.mcs=auto
    radio.1.txpower=auto
    # wlans (radio)
    radio.status=enabled
    radio.countrycode=840
    aaa.status=disabled
    wireless.status=enabled
    dhcpc.2.status=enabled
    dhcpc.2.devname=ath0
    bridge.1.port.2.devname=ath0
    radio.1.devname=ath0
    radio.1.status=enabled
    aaa.1.br.devname=br0
    aaa.1.devname=ath0
    aaa.1.driver=madwifi
    aaa.1.ssid=
    aaa.1.status=disabled
    wireless.1.mode=managed
    wireless.1.devname=ath0
    wireless.1.status=enabled
    wireless.1.authmode=1
    wireless.1.l2_isolation=disabled
    wireless.1.is_guest=false
    wireless.1.security=none
    wireless.1.addmtikie=disabled
    wireless.1.ssid=
    wireless.1.hide_ssid=enabled
    wireless.1.mac_acl.status=disabled
    wireless.1.mac_acl.policy=deny
    wireless.1.wmm=enabled
    # netconf
    netconf.status=enabled
    netconf.1.devname=eth1
    netconf.1.autoip.status=disabled
    netconf.1.ip=0.0.0.0
    netconf.1.promisc=enabled
    netconf.1.status=enabled
    netconf.1.up=enabled
    netconf.2.devname=br0
    netconf.2.autoip.status=disabled
    netconf.2.ip=0.0.0.0
    netconf.2.status=enabled
    netconf.2.up=enabled
    netconf.3.devname=ath0
    netconf.3.autoip.status=disabled
    netconf.3.ip=0.0.0.0
    netconf.3.promisc=enabled
    netconf.3.status=enabled
    netconf.3.up=enabled
    qos.status=enabled
    qos.group.1.rate=100
    qos.group.2.rate=100
    qos.group.6.rate=100
    qos.if.1.devname=eth1
    qos.if.1.devspeed=100
    qos.if.1.group=1
    qos.if.2.devname=ath0
    qos.if.2.devspeed=150
    qos.if.2.group=20
