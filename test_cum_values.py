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

        """
        Energy consumption = Data22: total_today_load
        Self sufficiency = Data21: inv_today_gen
        import energy = <Energy consumption> - <Self sufficiency> = data3: sum_feed_in_today

        Energy: Data21: todayenergy
        self-consumption: <Energy> - <export energy>
        export energy: data3: sum_sell_today
        """
        data11 = await read_additional_modbus_data_1_part_1(client)
        data21 = await read_additional_modbus_data_2_part_1(client)
        data22 = await read_additional_modbus_data_2_part_2(client)
        data3 = await read_additional_modbus_data_3(client)

        energy_consumption = data22["total_today_load"]
        self_sufficiency = data21["inv_today_gen"]
        import_energy = energy_consumption - self_sufficiency
        generated_energy = data21["todayenergy"]
        export_energy = data3["sum_sell_today"]
        self_consumption = generated_energy - export_energy
        batt_perc = data11["batEnergyPercent"]

        print(f"Generated energy: {generated_energy} kWh")
        print(f"Self consumption: {self_consumption} kWh")
        print(f"Exported energy: {export_energy} kWh")
        print(f"Energy consumption: {energy_consumption} kWh")
        print(f"Self sufficiency: {self_sufficiency} kWh")
        print(f"Imported energy: {import_energy} kWh")
        print(f"Battery percentage: {batt_perc}%")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

# Run the main function
asyncio.run(main())