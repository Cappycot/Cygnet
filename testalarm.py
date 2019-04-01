from datetime import datetime, timedelta
from serial import Serial

hour = 19
minute = 35
sameday = True
error = 1000
baud = 115200
port = "COM4"

top_error = 1000000 - error
while (True):
    current = datetime.now()
    if current.microsecond > top_error or current.microsecond < error:
        break
print("Current Time:", current)

seconds = hour * 3600 + minute * 60
seconds -= current.hour * 3600 + current.minute * 60 + current.second + (1 if current.microsecond > 500000 else 0)
recalcseconds = seconds
seconds %= 86400
hours = seconds // 3600
seconds %= 3600
minutes = seconds // 60
seconds %= 60

goal = current + timedelta(hours=hours, minutes=minutes, seconds=seconds)
if abs(goal.hour * 60 + goal.minute - hour * 60 - minute) > 1:
    seconds = recalcseconds - (goal.hour - hour) * 3600
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    goal = current + timedelta(hours=hours, minutes=minutes, seconds=seconds)

if not sameday and current.day == goal.day:
    goal += timedelta(hours=24)
    hours += 24

print("Alarm Set To:", goal)
print("Which is in...")
print(hours // 24, "days,")
print(hours % 24, "hours,")
print(minutes, "minutes,")
print(seconds, "seconds")

half_days = hours // 12
hours %= 12

seconds = (seconds << 2) | 1
minutes = (minutes << 2) | 2
hours = (hours << 4) | 8
half_days = (half_days << 5) | 16

ser = Serial()
ser.port = port
ser.baudrate = baud
ser.setDTR(False)
ser.open()
ser.write(bytes([seconds, minutes, hours, half_days, 128]))
ser.close()
