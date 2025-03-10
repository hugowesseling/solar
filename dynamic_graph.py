import tkinter as tk
import asyncio
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import dates
from pymodbus.client import AsyncModbusTcpClient
import datetime, time
from hugo_saj.modbus_data_readers import *

MAX_DATA_POINTS = 600

async def getSolarData(client):
    start_time = time.time()
    data11 = await read_additional_modbus_data_1_part_1(client)
    after1_time = time.time()
    data12 = await read_additional_modbus_data_1_part_2(client)
    data = {}
    try:
        data = {"pv1": data11["pv1Power"], "pv2": data11["pv2Power"],
                "use": data12["totalgridPower"], "batt": data11["batEnergyPercent"],
                "import": data12["CT_GridPowerWatt"], "bpow": data12["batteryPower"]}
    except KeyError:
        print(f"Missing keys in data: {data11}, {data12}")
    print(f"time1: {(after1_time - start_time) * 1000:.2f}ms, time2: {(time.time() - after1_time) * 1000:.2f}ms, data: {data}")
    return data

class SolarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solar Data Monitor")
        
        # Create Matplotlib figure and axis
        self.fig = Figure(figsize=(10, 5))
        self.fig.tight_layout()
        self.fig.subplots_adjust(right=0.85)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid()
        self.ax.xaxis.set_major_formatter(dates.DateFormatter("%H:%M:%S"))
        self.ax.set_title("Solar")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Power (W)")

        # Create a second y-axis for battery charge
        self.ax2 = self.ax.twinx()  
        self.ax2.set_ylabel("Battery Charge (%)")  # Label for the second y-axis
        
        self.x_data, self.y_data_use, self.y_data_pv1, self.y_data_pv2, self.y_data_batt, self.y_data_import, self.y_data_bpow = [], [], [], [], [], [], []
        
        # Create line objects for each data series
        self.line_use, = self.ax.plot(self.x_data, self.y_data_use, "g-", label="Use")
        self.line_pv1, = self.ax.plot(self.x_data, self.y_data_pv1, "b-", label="PV1")
        self.line_pv2, = self.ax.plot(self.x_data, self.y_data_pv2, "c-", label="PV2")
        self.line_import, = self.ax.plot(self.x_data, self.y_data_import, "r-", label="Import")
        self.line_bpow, = self.ax.plot(self.x_data, self.y_data_bpow, "y-", label="Batt")
        #self.line_batt, = self.ax2.plot(self.x_data, self.y_data_batt, "y-", label="Batt")

        self.ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
        # self.ax2.legend(loc="upper left", bbox_to_anchor=(1, 0.75))

        self.batt_fill = None
        
        # Create canvas for Matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()

        self.loop_thread = threading.Thread(target=self.start_update_graph, daemon=True)
        self.loop_thread.start()

    def start_update_graph(self):
        asyncio.run(self.update_graph())

    async def update_graph(self):
        client = AsyncModbusTcpClient(host="192.168.1.103", port=502)
        await client.connect()
        print(f"client={client}")
        while True:
            data = await getSolarData(client) # pv1, pv2, use, batt, import
            if len(data) == 0:
                print("Data problem, reconnecting")
                await client.connect()
                print("Reconnection attempt done")
                continue
            
            self.x_data.append(datetime.datetime.now())
            self.y_data_use.append(data["use"])
            self.y_data_pv1.append(data["pv1"])
            self.y_data_pv2.append(data["pv2"])
            self.y_data_batt.append(data["batt"])
            self.y_data_import.append(data["import"])
            self.y_data_bpow.append(data["bpow"])

            if len(self.x_data) > MAX_DATA_POINTS:
                self.x_data.pop(0)
                self.y_data_use.pop(0)
                self.y_data_pv1.pop(0)
                self.y_data_pv2.pop(0)
                self.y_data_batt.pop(0)
                self.y_data_import.pop(0)
                self.y_data_bpow.pop(0)
            
            self.line_use.set_xdata(self.x_data)
            self.line_use.set_ydata(self.y_data_use)
            
            self.line_pv1.set_xdata(self.x_data)
            self.line_pv1.set_ydata(self.y_data_pv1)
            
            self.line_pv2.set_xdata(self.x_data)
            self.line_pv2.set_ydata(self.y_data_pv2)
            
            #self.line_batt.set_xdata(self.x_data)
            #self.line_batt.set_ydata(self.y_data_batt)
            
            self.line_import.set_xdata(self.x_data)
            self.line_import.set_ydata(self.y_data_import)

            self.line_bpow.set_xdata(self.x_data)
            self.line_bpow.set_ydata(self.y_data_bpow)

            # Clear the previous fill and create a new one
            if self.batt_fill is not None:
                self.batt_fill.remove()
            # Update the fill under the battery curve
            self.batt_fill = self.ax2.fill_between(self.x_data, self.y_data_batt, color='orange', alpha=0.1)
            
            # Relimit and autoscale the view for the plot
            self.ax.relim()
            self.ax.autoscale_view()
            self.ax2.relim()
            self.ax2.autoscale_view()
            self.canvas.draw()
            
            await asyncio.sleep(1)

def main():
    root = tk.Tk()
    SolarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
