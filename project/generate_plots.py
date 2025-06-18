import matplotlib.pyplot as plt
import numpy as np

def generate_plots(visibilities, scan, output_path):
    data = {'Ib': {'RR': [], 'LL': [], 'LR': [], 'RL': []}, 
            'Ir': {'RR': [], 'LL': [], 'LR': [], 'RL': []},
            'IbIr': {'RR': [], 'LL': [], 'LR': [], 'RL': []}}
    baselines = {0: 'Ib', 1: 'IbIr', 2: 'Ir'}
    polarizations = {0: 'RR', 1: 'RL', 2: 'LR', 3: 'LL'}
    for subband in range(len(visibilities)):
        for baseline in range(3):
            for pol in range(4):
                data[baselines[baseline]][polarizations[pol]].extend(visibilities[subband][baseline][pol])
    
    # Autocorrelation plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
    
    ax1.plot(np.arange(len(data['Ir']['RR'])), np.abs(data['Ir']['RR']), color='red', label='Ir RR')
    ax1.plot(np.arange(len(data['Ir']['LL'])), np.abs(data['Ir']['LL']), color='lime', label='Ir LL')
    ax1.set_title('Autocorrelation Ir', fontsize=12)
    ax1.set_ylabel('Amplitude', fontsize=12)
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(np.arange(len(data['Ib']['RR'])), np.abs(data['Ib']['RR']), color='red', label='Ib RR')
    ax2.plot(np.arange(len(data['Ib']['LL'])), np.abs(data['Ib']['LL']), color='lime', label='Ib LL')
    ax2.set_title('Autocorrelation Ib', fontsize=12)
    ax2.set_xlabel("Channel", fontsize=12)
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(f'{output_path}/{scan["scan_nr"]}/auto.png')
    
    # Cross-correlation plot
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
    
    # Phases
    ax1.scatter(np.arange(len(data['IbIr']['RR'])), np.angle(data['IbIr']['RR'], deg=True), color='red', label='IbIr RR')
    ax1.scatter(np.arange(len(data['IbIr']['LL'])), np.angle(data['IbIr']['LL'], deg=True), color='lime', label='IbIr LL')
    ax1.scatter(np.arange(len(data['IbIr']['RL'])), np.angle(data['IbIr']['RL'], deg=True), color='blue', label='IbIr RL')
    ax1.scatter(np.arange(len(data['IbIr']['LR'])), np.angle(data['IbIr']['LR'], deg=True), color='aqua', label='IbIr LR')
    ax1.set_title('Cross-correlation IbIr', fontsize=12)
    ax1.set_ylabel('Phase (deg)', fontsize=12)
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Amplitudes
    ax2.plot(np.arange(len(data['IbIr']['RR'])), np.abs(data['IbIr']['RR']), color='red', label='IbIr RR')
    ax2.plot(np.arange(len(data['IbIr']['LL'])), np.abs(data['IbIr']['LL']), color='lime', label='IbIr LL')
    ax2.plot(np.arange(len(data['IbIr']['RL'])), np.abs(data['IbIr']['RL']), color='blue', label='IbIr RL')
    ax2.plot(np.arange(len(data['IbIr']['LR'])), np.abs(data['IbIr']['LR']), color='aqua', label='IbIr LR')
    ax2.set_title('Cross-correlation IbIr', fontsize=12)
    ax2.set_xlabel("Channel", fontsize=12)
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(f'{output_path}/{scan["scan_nr"]}/cross.png')