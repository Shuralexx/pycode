import pandas as pd
import pyqtgraph as pg
import numpy as np
from scipy import fftpack, stats
from scipy.signal import kaiserord


def fft_analysis(self,data,fs):
        clip = 0.01    # INL DNL 误差排除比例
        sideBin = 200    # 信号谱线宽
        sideBin_thd = 30    # 信号谱线宽
        lowCut = 2     # 去除低频数据点数
        harmonic = 7  # THD 计算谐波数
        N = len(data)
        Nd2 = int(np.floor(N/2))
        freq = np.arange(0,(Nd2-1))/N*fs
        fdata = data/(np.max(data)-np.min(data))
        spec = np.power(np.abs(fftpack.fft(fdata)),2)
        spec = spec[0:Nd2-1]
        spec = spec/(N^2)*16
        spec[0:lowCut-1] = spec[lowCut]
        bin = list(spec).index(np.max(spec))

        bin_list = np.arange(int(np.max([bin-sideBin,1])),int(np.min([bin+sideBin,Nd2])),1)
        sig = np.sum(spec[bin_list])
        thd1=0
        pwr = 10*np.log10(sig)
        for i in np.arange(2,harmonic):
            b=self.fclip((bin-1)*i,N)
            thd_bin_list = np.arange(int(np.max([b+1-sideBin_thd,1])),int(np.min([b+1+sideBin_thd,Nd2])),1)
            thd1 = thd1+np.sum(spec[thd_bin_list])
        spec[np.arange(np.max([bin-sideBin,1]),np.min([bin+sideBin,Nd2]))] = 0
        thdn=np.sum(spec)
        sbin = list(spec).index(np.max(spec))
        spur = np.sum(spec[np.arange(np.max([sbin-sideBin_thd,1]),np.min([sbin+sideBin_thd,Nd2]))])
        noi=thdn-thd1
        SINAD = 10*np.log10(sig/thdn)
        SNR = 10*np.log10(sig/noi)
        THD = 10*np.log10(thd1/sig)
        SFDR = 10*np.log10(sig/spur)
        return [SINAD,SNR,THD,SFDR]

def main():
    pd_read = pd.read_csv("D:/SynologyDrive/code/CM1348_Eval_GUI/10k_4V_osc_res.csv")
    print(pd_read)


if __name__ == '__main__':
    main()