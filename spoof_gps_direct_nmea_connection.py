import serial
import pynmea2
import time, datetime, math
import requests

url = "http://127.0.0.1:56781/mavlink/" #https://diydrones.com/forum/topics/real-time-export-telemetry-data-from-mission-planner
port_name = 'COM27'
baudrate = 4800

# Create a serial port object
ser = serial.Serial(port_name, baudrate)

def decimal_to_degrees(decimal):
    decimal = abs(decimal)
    degrees = math.floor(decimal)
    decimal_minutes = (decimal - degrees) * 60
    # minutes = math.floor(decimal_minutes)
    # seconds = (decimal_minutes - minutes) * 60
    # print(decimal,degrees, minutes, seconds, degrees + minutes/100 + seconds/10000)
    return degrees + decimal_minutes/100 #+ seconds/10000
try:
    # Open the serial port
    if not ser.isOpen():
        ser.open()
    while True:
        try:
            '''
            Json get
            '''
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception("Failed to fetch data. Status code:" + str(response.status_code))
            json_data = response.json()
            '''
            Json parse
            '''
            gps_data = json_data.get("GPS_RAW_INT", {}).get("msg", {})
            gps_time = gps_data.get("time_usec")
            latitude = decimal_to_degrees(gps_data.get("lat") / 1e7)  # Convert from integer to degrees
            longitude = decimal_to_degrees(gps_data.get("lon") / 1e7)  # Convert from integer to degrees
            sats = gps_data.get("satellites_visible")
            alt = gps_data.get("alt")
            alt_ellipsoid = gps_data.get("alt_ellipsoid")
            '''
            GPS pipe
            '''
            current_time = datetime.datetime.now(datetime.timezone.utc).timestamp()
            current_time = "{:.2f}".format(current_time)
            #standard https://docs.arduino.cc/learn/communication/gps-nmea-data-101/
            gps_sentence = pynmea2.GGA('GP', 'GGA', (str(current_time), "{:07.8f}".format(abs(latitude)*100), 'N', "{:07.8f}".format(abs(longitude)*100), 'W', '4', str(sats), '2.6', "{:.5f}".format(0.3048*abs(alt)/1000), 'M', "{:.2f}".format(abs(alt_ellipsoid)/1000), 'M', '', '0000'))
            # gps_sentence = pynmea2.GGA('GP', 'GGA', (str(current_time), '3746.49400', 'N', '12225.16400', 'W', '4', '13', '2.6', '100.00', 'M', '33.9', 'M', '', '0000'))
            nmea_bytes = str(gps_sentence) + '\r\n'
            nmea_bytes = nmea_bytes.encode('utf-8')
            ser.write(nmea_bytes)
            print("Sent:", nmea_bytes.decode())
        except Exception as e:
            print(e)
        time.sleep(1)

except requests.exceptions.RequestException as e:
    print("Error:", e)
except KeyboardInterrupt:
    print("Interrupted")

finally:
    # Close the serial port
    ser.close()