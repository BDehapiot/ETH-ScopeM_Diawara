#%% Imports -------------------------------------------------------------------

from pathlib import Path

# functions
from main import Main
from display import Display

#%% Inputs --------------------------------------------------------------------

dataset = "nelva_40"

# Procedure
procedure = {
    
    "prepare" : 0,
    "predict" : 0,
    "process" : 0,
    "analyse" : 0,
    "display" : 1,
    
    }

# Parameters
parameters = {
        
    # Paths
    "root_path" : 
        Path(__file__).resolve().parent,
    "data_path" : 
        # Path(rf"\\scopem-idadata.ethz.ch\BDehapiot\remote_Diawara\data_{dataset}"),
        # Path(rf"C:\Users\bdeha\Projects\local\local_Diawara\data_{dataset}"),
        Path(f"D:\local_Diawara\data_{dataset}"),
       
    # Channels
    "prepare_channels" : ["c0", "c1", "c2"],
    "process_channels" : ["c1", "c2"],
    "compare_channels" : ["c1", "c2"],

    # Predict
    "segmentation"     : "instance",
    
    # Process
    "parallel"         : True,
    
    "c1" : {
        "obj_thresh_0" : 0.15,
        "obj_thresh_1" : 0.3,
        "obj_min_size" : 16,
        "clt_max_dist" : 5,
        "grd_sigma"    : 1,
        "clt_min_grd"  : 0.02,
        },
    
    "c2" : {
        "obj_thresh_0" : 0.2,
        "obj_thresh_1" : 0.5,
        "obj_min_size" : 16,
        "clt_max_dist" : 5,
        "grd_sigma"    : 1,
        "clt_min_grd"  : 0.02,
        },
    
    # Analyse
    "conditions"       : ["0.06", "0.125", "0.25", "0.5"],
    "categories"       : [3, 10],
    "min_clt_obj_num"  : 3,
    "min_clt_area"     : 1,
    "conds_color"      : ["gray", "red", "green", "blue"],
    "shade_color"      : [20, 40, 60],
    "chns_color"       : ["green", "red"],
    
    }
    
#%% Execute -------------------------------------------------------------------

if __name__ == "__main__":
    main = Main(procedure=procedure, parameters=parameters)
    display = Display(procedure=procedure, parameters=parameters)