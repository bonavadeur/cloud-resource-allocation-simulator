import numpy as np
import time

np.random.seed(1)
LAMDA = 10
TIME = 60

def dist(lamda):
    duration = round(60 * np.random.exponential(scale=1/lamda))
    return duration


time_second = TIME * 60

startTime = int(time.time())
while int(time.time()) - startTime < time_second:
    dur = dist(LAMDA)
    print(dur)
    time.sleep(dur)