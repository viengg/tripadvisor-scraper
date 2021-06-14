import os
import psutil

for proc in psutil.process_iter():
    # check whether the process name matches
    if proc.name() == "chrome" or proc.name() == "chromedriver":
        proc.kill()