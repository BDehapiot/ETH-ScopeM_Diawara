#%% Imports -------------------------------------------------------------------

from pathlib import Path

# functions
from main import Main
from display import Display

#%% Inputs --------------------------------------------------------------------

dataset = "chris"

# Procedure
procedure = {
    
    "prepare" : 0,
    "predict" : 0,
    "process" : 0,
    "analyse" : 1,
    "display" : 0,
    
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
    "process_channels" : ["c0", "c1"],
    "compare_channels" : ["c0", "c1"],

    # Predict
    "segmentation"     : "semantic",
    
    # Process
    "parallel"         : True,
    
    "c0" : {
        "obj_thresh_0" : 0.5,
        "obj_thresh_1" : None,
        "obj_min_size" : 16,
        "clt_max_dist" : 5,
        "grd_sigma"    : None,
        "clt_min_grd"  : None,
        },
    
    "c1" : {
        "obj_thresh_0" : 0.5,
        "obj_thresh_1" : None,
        "obj_min_size" : 16,
        "clt_max_dist" : 5,
        "grd_sigma"    : None,
        "clt_min_grd"  : None,
        },
    
    # Analyse
    "conditions"        : ["s8n13_O5_12", "s9n28_O5_12", "s9n28_O5_wzyB"],
    "categories"        : None,
    "min_clt_obj_num"   : 1,
    "min_clt_area"      : 128,
    "conds_color"       : ["gray", "red", "blue"],
    "shade_color"       : [20, 40, 60],
    "chns_color"        : ["green", "red"],
    
    }
    
#%% Execute -------------------------------------------------------------------

if __name__ == "__main__":
    main = Main(procedure=procedure, parameters=parameters)
    display = Display(procedure=procedure, parameters=parameters)