![IJ Badge](https://img.shields.io/badge/ImageJ-1.54f-blue?logo=imageJ&logoColor=rgb(149%2C157%2C165)&labelColor=rgb(50%2C60%2C65))  
![Author Badge](https://img.shields.io/badge/Author-Benoit_Dehapiot-blue?labelColor=rgb(50%2C60%2C65)&color=rgb(149%2C157%2C165))
![Date Badge](https://img.shields.io/badge/Created-2023--10--23-blue?labelColor=rgb(50%2C60%2C65)&color=rgb(149%2C157%2C165))
![License Badge](https://img.shields.io/badge/Licence-GNU%20General%20Public%20License%20v3.0-blue?labelColor=rgb(50%2C60%2C65)&color=rgb(149%2C157%2C165))  

# ETH_ScopeM_Diawara
Bacteria cluster segmentation

## Intallation

### 1 - Download GitHub repository: 
- Download this repository by clicking the following 
[link](https://github.com/BDehapiot/ETH-ScopeM_Diawara/archive/refs/heads/main.zip)  
- Unzip the file to a known location (e.g. `~/Desktop`)

### 2 - Install / Update Fiji
https://imagej.net/software/fiji/  

<ins>Fiji **is not** installed on your system:</ins>

- Download Fiji from the official website (link above)
- Unzip the file to a known location

<ins>Fiji **is** already installed on your system:</ins>

Option #1
- Update ImageJ by clicking > `Help` > `Update ImageJ...`
- Update Fiji by clicking > `Help` > `Update...`

Option #2
- Install a new Fiji instance to avoid modifying your own

### 3 - Run the macro
- Drag and drop the `.ijm` file(s) to you Fiji interface
- Click `run` in the new IDE window to execute the macro

## Usage

Open a two channels hyperstack, where C1 will be used to normalize C2, and run the macro as describe above.

### Parameters
- `Furrow ROI scaling factor` (*float*): Scaling factor to adjust the size of the cleavage furrow ROI.

### Process
- Open hyperstack
- Run the macro
- Adjust parameters 
- Select z-plane of interest
- Draw mother and daughter cell ROIs
- Indicate cleavage furrow position

### Outputs
The following outputs will be saved in folder your folder containing the opened hyperstack. 

#### Images

- `C1_raw.tif` : C1 raw image of the selected z-plane.
- `C2_raw.tif` : C2 raw image of the selected z-plane.
- `C1_norm.tif` : C1 image normalized to the median value of membrane signal.
- `C2_norm.tif` : C2 image normalized to the median value of membrane signal.
- `C2C1.tif` : C2_norm divided by C1_norm. 

#### CSV files

- Results.csv

    - `C1_med` : C1 median value of membrane signal
    - `C2_med` : C2 median value of membrane signal
    - `C1_norm_furrow_med` : C1 median furrow normalized signal
    - `C2_norm_furrow_med` : C2 median furrow normalized signal
    - `C2C1_furrow_med` : C2_norm/C1_norm ratio furrow signal

- Profiles.csv

    - `1st column` : Distance in µm
    - `2nd column` : Furrow line profile of C1 median furrow normalized signal
    - `3rd column` : Furrow line profile of C2 median furrow normalized signal
    - `4th column` : Furrow line profile of C2_norm/C1_norm ratio furrow signal
 
#### ROIs

- RoiSet.zip

    - `mother_cell` : Drawn mother cell ROI
    - `daughter_cell` : Drawn daughter cell ROI
    - `furrow_points` : Drawn furrow points
    - `furrow_line` : Line profile ROI (inferred from furrow points)
    - `furrow_area` : Line area ROI (inferred from furrow points)