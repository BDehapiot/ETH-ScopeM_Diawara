#%% Imports -------------------------------------------------------------------

import pickle
import numpy as np
np.random.seed(42)
from skimage import io
from pathlib import Path

# functions
from functions import load_data, normalize_data, save_patches

# bdtools
from bdtools.patch import extract_patches

# skimage
from skimage.feature import match_template

#%% Inputs --------------------------------------------------------------------

# Path(s)
dataset = "yagmur"
# data_path = Path(rf"C:\Users\bdeha\Projects\local\local_Diawara\data_{dataset}")
# data_path = Path(f"D:\local_Diawara\data_{dataset}")
data_path = Path(f"D:\local_Diawara\data_{dataset}")
normal_path = Path("data", "yagmur_normal")
hand_path = Path("data", "yagmur_hand")
nd2_paths = list(data_path.rglob("*nd2"))

# Parameters
patch_num  = 5 
patch_size = 256

#%% Function(s) ---------------------------------------------------------------

def extract(data_path):

        # Load
        stems, c0s, c1s = load_data(data_path)
        
        # Fix channel inversion
        new_c0s, new_c1s = [], []
        for s, stem in enumerate(stems):
            if "_00_" in stem:
                new_c0s.append(c0s[s])
                new_c1s.append(c1s[s])
            else:
                new_c0s.append(c1s[s])
                new_c1s.append(c0s[s])
        c0s = np.stack(new_c0s)
        c1s = np.stack(new_c1s)
        
        # Normalize
        c0s = normalize_data(c0s, low_qtl=0.25)
        c1s = normalize_data(c1s, low_qtl=0.25)
    
        # Save data
        io.imsave(data_path / "c0s.tif", c0s, check_contrast=False)
        io.imsave(data_path / "c1s.tif", c1s, check_contrast=False)
        with open(data_path / "stems.pkl", "wb") as f:
            pickle.dump(stems, f)
            
        # # Save patches
        # save_patches(
        #     c1s, stems, chn="c1", patch_num=patch_num, patch_size=patch_size)
        
def reextract_normal(dir_path):

    # Initialize
    c1_msk_pch_paths = list(dir_path.rglob("*_mask.tif"))
        
    # Load data #1
    stems, c0s, c1s = load_data(data_path)
    
    # Normalize
    c1s = normalize_data(c1s, low_qtl=0.25)
    
    for c1_msk_pch_path in c1_msk_pch_paths:

        # Parse mask patch stem
        tmp_stem = c1_msk_pch_path.stem
        parts = tmp_stem.split("_")
        stem = "_".join(parts[0:3])
        idx_i = int(parts[-3])
        idx_p = int(parts[-2])
        idx_s = stems.index(f"{stem}_{idx_i - 1:02d}")
        print(stem, idx_i, idx_p)

        # Load mask patch
        c1_msk_pch = io.imread(c1_msk_pch_path)

        # Extract image patch
        c1_img_pch = extract_patches(c1s[idx_s], patch_size, 0)[idx_p]
            
        # Save patch
        train_path = Path.cwd() / "data" / "c1_train" 
        c1_msk_pch_path = train_path / (stem + f"_c1_{idx_i - 1}_{idx_p:02d}_mask.tif")
        c1_img_pch_path = train_path / (stem + f"_c1_{idx_i - 1}_{idx_p:02d}.tif")
        io.imsave(c1_msk_pch_path, c1_msk_pch, check_contrast=False)
        io.imsave(c1_img_pch_path, c1_img_pch, check_contrast=False)

def reextract_hand(dir_path):
        
    # Initialize
    c1_msk_pch_paths = list(dir_path.rglob("*_mask.tif"))
    
    # Load data #1
    stems, c0s, c1s = load_data(data_path)
    
    # Normalize
    c1s = normalize_data(c1s, low_qtl=0.25)
    
    for i, c1_msk_pch_path in enumerate(c1_msk_pch_paths):
        
        c1_img_pch_path = Path(str(c1_msk_pch_path).replace("_mask", ""))

        # Parse mask names
        tmp_stem = c1_msk_pch_path.stem
        parts = tmp_stem.split("_")
        stem = "_".join(parts[0:3])
        idx_i = int(parts[-3])
        idx_s = stems.index(f"{stem}_{idx_i - 1:02d}")
        print(stem, idx_i)
        
        # Load data #2
        img = c1s[idx_s]
        ref = io.imread(c1_img_pch_path)
        c1_msk_pch = io.imread(c1_msk_pch_path)
        
        # Template matching
        corr = match_template(img, ref, pad_input=True)
        y, x = np.unravel_index(np.argmax(corr), corr.shape)
        y0 = y - ref.shape[0] // 2; y1 = y + ref.shape[0] // 2
        x0 = x - ref.shape[0] // 2; x1 = x + ref.shape[0] // 2
        c1_img_pch = img[y0:y1, x0:x1]
        
        # Save patch
        train_path = Path.cwd() / "data" / "c1_train" 
        c1_msk_pch_path = train_path / (stem + f"_c1_{idx_i - 1}_{i:02d}_mask.tif")
        c1_img_pch_path = train_path / (stem + f"_c1_{idx_i - 1}_{i:02d}.tif")
        io.imsave(c1_msk_pch_path, c1_msk_pch, check_contrast=False)
        io.imsave(c1_img_pch_path, c1_img_pch, check_contrast=False)

#%% Execute -------------------------------------------------------------------

if __name__ == "__main__":
    extract(data_path)
    # reextract_normal(normal_path)
    # reextract_hand(hand_path)