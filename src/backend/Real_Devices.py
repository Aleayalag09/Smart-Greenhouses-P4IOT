import board
import Adafruit_DHT
import time

class Measurements():
    def __init__(self, pin):
        self.DHT11 = Adafruit_DHT.DHT11(board.pin)
        self.humidity = None
        self.temperature = None
        
    def read_measurements(self):
        """
        This function read the temperature and humidity from the DHT11 sensor
        pin - input assigned to sensor in Raspberry 
        Input format (e.g. pin= board.D23)
        """
        
        while True: 
            if self.humidity is not None and self.temperature is not None:
                return self.humidity, self.temperature
            else:
                self.humidity = self.DHT11.humidity
                self.temperature = self.DHT11.temperature

if __name__ == "__main__":
    while not done:
            DHT11 = Measurements("D23")
            humidity, temperature = DHT11.read_measurements()
            print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
            print("press e to exit")         
            user_input = input()
            if user_input == "e":
                done = True
            else:
                pass
            time.sleep(1)
            