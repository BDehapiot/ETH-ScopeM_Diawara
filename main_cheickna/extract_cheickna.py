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
dataset = "cheickna"
# data_path = Path(rf"C:\Users\bdeha\Projects\local\local_Diawara\data_{dataset}")
# data_path = Path(f"D:\local_Diawara\data_{dataset}")
data_path = Path(f"D:\local_Diawara\data_{dataset}")
nd2_paths = list(data_path.rglob("*nd2"))

# Parameters
patch_num  = 10
patch_size = 256

#%% Function(s) ---------------------------------------------------------------

def extract(data_path):
    
        # Load
        stems, c0s, c1s = load_data(data_path)
        
        # Normalize
        c0s = normalize_data(c0s, low_qtl=None)
        c1s = normalize_data(c1s, low_qtl=0.25)
    
        # Save data
        io.imsave(data_path / "c0s.tif", c0s, check_contrast=False)
        io.imsave(data_path / "c1s.tif", c1s, check_contrast=False)
        with open(data_path / "stems.pkl", "wb") as f:
            pickle.dump(stems, f)
            
        # # Save patches
        # save_patches(
        #     c1s, stems, patch_num=patch_num, patch_size=patch_size, chn="c1")

#%% Execute -------------------------------------------------------------------

if __name__ == "__main__":
    extract(data_path)