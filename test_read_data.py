"""
To read:

Real time information:

data11: batEnergyPercent, pv1Power, pv2Power
data12: CT_GridPowerWatt, (Don't use pvPower, seems delayed)

Cumulative information:
Data22: total_today_load, sell_today_energy, feedin_today_energy
"""

import asyncio, json
from pymodbus.client import AsyncModbusTcpClient
from hugo_saj.modbus_data_readers import *


async def main():
    # Initialize the ModbusClient
    client = AsyncModbusTcpClient(
        host="192.168.1.103",  # Replace with your inverter's IP address
        port=502  # Replace with your inverter's port
    )

    try:
        # Connect to the inverter
        await client.connect()

        data = await read_modbus_inverter_data(client)
        print("Inverter Data:", json.dumps(data, indent=4))

        data = await read_modbus_realtime_data(client)
        print("Realtime Data:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_1_part_1(client)
        print("Data11:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_1_part_2(client)
        print("\nData12:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_2_part_1(client)
        print("Data21:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_2_part_2(client)
        print("Data22:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_3(client)
        print("Data3:", json.dumps(data, indent=4))

        data = await read_additional_modbus_data_4(client)
        print("Data4:", json.dumps(data, indent=4))

        data = await read_battery_data(client)
        print("DataB:", json.dumps(data, indent=4))

        data = await read_first_charge_data(client)
        print("DataFC:", json.dumps(data, indent=4))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

# Run the main function
asyncio.run(main())