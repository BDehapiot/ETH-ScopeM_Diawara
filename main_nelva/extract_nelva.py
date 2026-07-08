#%% Imports -------------------------------------------------------------------

import pickle
import numpy as np
np.random.seed(42)
from skimage import io
from pathlib import Path

# functions
from functions import load_data, normalize_data, save_patches

#%% Inputs --------------------------------------------------------------------

# Path(s)
dataset = "nelva_40"
# data_path = Path(rf"C:\Users\bdeha\Projects\local\local_Diawara\data_{dataset}")
# data_path = Path(f"D:\local_Diawara\data_{dataset}")
data_path = Path(f"D:\local_Diawara\data_{dataset}")
nd2_paths = list(data_path.rglob("*nd2"))

# Parameters
patch_num  = 5 
patch_size = 512

#%% Function(s) ---------------------------------------------------------------

def extract(data_path):
    
        # Load
        stems, c0s, c1s, c2s = load_data(data_path)
        
        # Normalize
        c0s = normalize_data(c0s, low_qtl=0.25)
        c1s = normalize_data(c1s, low_qtl=0.25)
        c2s = normalize_data(c2s, low_qtl=0.25)
    
        # Save data
        io.imsave(data_path / "c0s.tif", c0s, check_contrast=False)
        io.imsave(data_path / "c1s.tif", c1s, check_contrast=False)
        io.imsave(data_path / "c2s.tif", c2s, check_contrast=False)
        with open(data_path / "stems.pkl", "wb") as f:
            pickle.dump(stems, f)
            
        # # Save patches
        # save_patches(
        #     c0s, stems, chn="c0", patch_num=patch_num, patch_size=patch_size)
        # save_patches(
        #     c2s, stems, chn="c2", patch_num=patch_num, patch_size=patch_size)

#%% Execute -------------------------------------------------------------------

if __name__ == "__main__":
    extract(data_path)