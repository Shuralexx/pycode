import pandas as pd
import numpy as np
from scipy import fftpack, stats
from scipy.signal import kaiserord
import matplotlib.pyplot as plt

def main():
    wave = np.loadtxt('data',delimiter=',')
    wave_volt = wave/np.power(2,23)*2.5/1.06
    x = np.arange(len(wave_volt))
    plt.plot(x,wave_volt)
    plt.show()

if __name__ == '__main__':
    main()