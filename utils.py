def decode_station_band(sta):
    tx = sta["tx_rate"] / 1000
    rx = sta["rx_rate"] / 1000
    is_a = sta.get("is_11a", None)
    is_n = sta.get("is_11n", False)

    if is_n:
        return "N"

    if is_a:
        return "A"

    if not is_n and any((rx > 11, rx > 11)):
        return "G"
    else:
        return "B"
