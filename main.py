#%% Imports -------------------------------------------------------------------

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="h5py")

import time
import pickle
import pandas as pd
from skimage import io
from joblib import Parallel, delayed

# functions
from functions import (
    clear_data,
    get_model_path, merge_predictions, 
    get_objects, get_clusters, get_gradient, filter_acc2_gradient,
    get_obj_results, get_clt_results, get_mix_ratio,
    process_results, plot_clusters, plot_compare,
    )

# bdtools
from bdtools.models.unet import UNet

#%% Class(Main) ---------------------------------------------------------------

class Main:
    
    def __init__(self, procedure=None, parameters=None):
    
        # Fetch
        self.procedure  = procedure
        self.parameters = parameters
                        
        # Run
        self.initialize()
        if self.procedure["prepare"]: self.prepare()
        if self.procedure["predict"]: self.predict() 
        if self.procedure["process"]: self.process()
        if self.procedure["analyse"]: self.analyse()
        
#%% Class(Main) : initialize() ------------------------------------------------

    def initialize(self):
        
        for key, val in self.parameters.items():
            if not isinstance(val, dict):
                setattr(self, key, val)
        
        with open(self.data_path / "stems.pkl", "rb") as f:
            self.stems = pickle.load(f)
        
#%% Class(Main) : prepare() ---------------------------------------------------

    def prepare(self):
        
        def _prepare(i, stem):
            
            out_path = self.data_path / f"{stem}"
            out_path.mkdir(parents=True, exist_ok=True)
    
            # Save
            for chn in self.prepare_channels:
                io.imsave(
                    out_path / f"{chn}_img.tif", 
                    getattr(self, f"{chn}s")[i], 
                    check_contrast=False,
                    )
            
        # Execute -------------------------------------------------------------
    
        clear_data(self.data_path, procedure="prepare")    
    
        t0 = time.time()
        print("prepare()")
        print(" load : ", end="", flush=False)
        for chn in self.prepare_channels:
            path = list(self.data_path.glob(f"{chn}s.tif"))
            setattr(self, f"{chn}s", io.imread(path[0]))
        t1 = time.time()
        print(f"{t1 - t0:.3f}s")
        
        t0 = time.time()
        print(" save : ", end="", flush=False)
        for i, stem in enumerate(self.stems):
            _prepare(i, stem)
        t1 = time.time()
        print(f"{t1 - t0:.3f}s")
            
#%% Class(Main) : predict() ---------------------------------------------------

    def predict(self):
                
        def _predict(chn, i, stem):
            
            out_path = self.data_path / f"{stem}"
            
            # Initialize
            print(
                f"predict() " 
                f"- {self.segmentation}"
                f"- {chn}"
                f"- {out_path.stem}"
                )
            img = io.imread(out_path / f"{chn}_img.tif")
            img = img.astype("float32") / 255 

            if self.segmentation == "semantic":
                
                # Predict
                t0 = time.time()
                print(" predict : ", end="", flush=False)
                
                prd = unet_0.predict(img, verbose=0)
                
                t1 = time.time()
                print(f"{t1 - t0:.3f}s")

            elif self.segmentation == "instance":
            
                # Predict
                t0 = time.time()
                print(" predict : ", end="", flush=False)
                
                prd_0 = unet_0.predict(img, verbose=0)
                prd_1 = unet_1.predict(img, verbose=0)
                prd_2 = unet_2.predict(img, verbose=0)
                
                t1 = time.time()
                print(f"{t1 - t0:.3f}s")
                
                # Merge predictions
                prd = merge_predictions(prd_0, prd_1, prd_2)  

            # Save
            t0 = time.time()
            print(" save    : ", end="", flush=False)
            
            prd = (prd * 255).astype("uint8") 
            io.imsave(
                out_path / f"{chn}_prd.tif", 
                prd, check_contrast=False
                )
            
            t1 = time.time()
            print(f"{t1 - t0:.3f}s")
        
        # Execute -------------------------------------------------------------

        clear_data(self.data_path, procedure="predict")

        for chn in self.process_channels:
            
            if self.segmentation == "semantic":
                unet_0 = UNet(load_name=get_model_path(
                    self.root_path, tags=[chn, "normal"]))
            
            elif self.segmentation == "instance":
                unet_0 = UNet(load_name=get_model_path(
                    self.root_path, tags=[chn, "edt"]))
                unet_1 = UNet(load_name=get_model_path(
                    self.root_path, tags=[chn, "interfaces"]))
                unet_2 = UNet(load_name=get_model_path(
                    self.root_path, tags=[chn, "skeletons"]))
            
            for i, stem in enumerate(self.stems):
                _predict(chn, i, stem)  
                
#%% Class(Main) : process() ---------------------------------------------------

    def process(self):
        
        def _process(i, stem):
            
            out_path = self.data_path / f"{stem}"
            
            self.data = {chn: {} for chn in self.process_channels}
            
            t0 = time.time()
            print(f"process() - {out_path.stem}")
            print(" get images  : ", end="", flush=False)
            
            for chn in self.process_channels:
            
                # Initialize
                self.data[chn]["img"] = io.imread(out_path / f"{chn}_img.tif")  
                prd = io.imread(out_path / f"{chn}_prd.tif")  
                self.data[chn]["prd"] = prd.astype("float32") / 255 
                                
                # Get objects -------------------------------------------------

                self.data[chn]["obj"] = get_objects(self.data[chn]["prd"], 
                    thresh_0=self.parameters[chn]["obj_thresh_0"],
                    thresh_1=self.parameters[chn]["obj_thresh_1"],
                    min_size=self.parameters[chn]["obj_min_size"],
                    )

                # Get clusters ------------------------------------------------

                self.data[chn]["clt"] = get_clusters(self.data[chn]["obj"], 
                    max_dist=self.parameters[chn]["clt_max_dist"],
                    )

                # Get gradient ------------------------------------------------
                
                if self.parameters[chn]["grd_sigma"]:
                    self.data[chn]["grd"] = get_gradient(self.data[chn]["img"], 
                        sigma=self.parameters[chn]["grd_sigma"]
                        )
                    self.data[chn]["obj"], self.data[chn]["clt"] = filter_acc2_gradient(
                        self.data[chn]["img"], self.data[chn]["obj"], 
                        self.data[chn]["clt"], self.data[chn]["grd"], 
                        min_grd=self.parameters[chn]["clt_min_grd"]
                        )    
                else:
                    self.data[chn]["grd"] = None
                    
            t1 = time.time()
            print(f"{t1 - t0:.3f}s")
                    
            # Get results -----------------------------------------------------
                
            t0 = time.time()
            print(" get results : ", end="", flush=False)
                
            for chn in self.process_channels:
                
                self.data[chn]["obj_results"] = get_obj_results(
                    stem, 
                    self.data[chn]["img"], 
                    self.data[chn]["obj"], 
                    self.data[chn]["clt"], 
                    grd=self.data[chn]["grd"],
                    )
                
                self.data[chn]["clt_results"] = get_clt_results(
                    stem, 
                    self.data[chn]["img"], 
                    self.data[chn]["obj"], 
                    self.data[chn]["clt"], 
                    grd=self.data[chn]["grd"],
                    )
                
            if self.compare_channels is not None:
                
                for chn in self.process_channels:

                    for cmp_chn in self.compare_channels:
                        
                        if cmp_chn != chn:
                            
                            for tag in ["obj", "clt"]:

                                get_mix_ratio(
                                    self.data[chn][f"{tag}_results"], 
                                    self.data[chn][tag],
                                    self.data[cmp_chn][tag],
                                    tag=cmp_chn,
                                    )
                
            t1 = time.time()
            print(f"{t1 - t0:.3f}s")
                                        
            # Save ------------------------------------------------------------
            
            t0 = time.time()
            print(" save        : ", end="", flush=False)
            
            for chn in self.process_channels:
            
                # Images       
            
                for tag in ["obj", "clt"]:
                 
                    io.imsave(
                        out_path / f"{chn}_{tag}.tif", 
                        self.data[chn][tag], check_contrast=False
                        )

                if self.data[chn]["grd"] is not None:
                    self.data[chn]["grd"] = self.data[chn]["grd"].astype("uint8")
                    io.imsave(
                        out_path / f"{chn}_grd.tif", 
                        self.data[chn]["grd"], check_contrast=False
                        )
                    
                # Results
                
                def save_csv(results, tag="obj"):
                    df = pd.DataFrame(results)
                    df.to_csv(out_path / f"{chn}_{tag}_results.csv", index=False)
                
                for tag in ["obj", "clt"]:
                    
                    with open(out_path / f"{chn}_{tag}_results.pkl", "wb") as f:
                        pickle.dump(self.data[chn][f"{tag}_results"], f)

                    save_csv(self.data[chn][f"{tag}_results"], tag=tag)
                                        
            t1 = time.time()
            print(f"{t1 - t0:.3f}s")
        
        # Execute -------------------------------------------------------------
        
        clear_data(self.data_path, procedure="process")    
        
        if self.parallel:
                    
            t0 = time.time()
            print("process() - parallel : ", end="", flush=False)
            
            Parallel(n_jobs=-1)(
                delayed(_process)(i, stem) 
                for i, stem in enumerate(self.stems)
                )  
            
            t1 = time.time()
            print(f"{t1 - t0:.3f}s")
            
        else:

            for i, stem in enumerate(self.stems):
                _process(i, stem) 
                
#%% Class(Main) : analyse() ---------------------------------------------------

    def analyse(self):
        
        clear_data(self.data_path, procedure="analyse")
            
        t0 = time.time()
        print("analyse() : ", end="", flush=False)
        
        # Initialize
        self.results = {chn: {} for chn in self.process_channels}
        
        # Process results -----------------------------------------------------
        
        for chn in self.process_channels:
                            
            self.results[chn] = process_results(
                self.data_path, self.stems, 
                self.conditions, self.categories, 
                self.segmentation, self.min_clt_obj_num, self.min_clt_area,
                chn=chn,
                )
                
        # Plot ----------------------------------------------------------------
                
        for chn in self.process_channels:
            
            self.results[chn]["plot_cluster"] = plot_clusters(
                self.results, self.data_path, self.stems, self.conditions,
                self.conds_color, self.shade_color,
                self.segmentation, self.min_clt_obj_num, self.min_clt_area,
                chn=chn,
                )
        
        if self.compare_channels:
        
            self.results["plot_compare"] = plot_compare(
                self.results, self.data_path, self.conditions, self.chns_color,
                self.segmentation, self.min_clt_obj_num, self.min_clt_area,
                chns=self.compare_channels,
                )
        
        # Save ----------------------------------------------------------------
        
        for chn in self.process_channels:

            for tag in ["obj", "clt"]:
                
                self.results[chn][f"{tag}_results_all"].to_csv(
                    self.data_path / f"{tag}_{chn}_results_all.csv",
                    )
                
                if tag == "clt":
                    
                    self.results[chn]["clt_results_all_f"].to_csv(
                        self.data_path / f"clt_{chn}_results_all_f.csv",
                        )
                    
                    if self.segmentation == "instance":
                    
                        self.results[chn]["clt_obj_num_dist"].to_csv(
                            self.data_path / f"clt_{chn}_obj_num_dist.csv", 
                            )
                        self.results[chn]["clt_obj_num_cat" ].to_csv(
                            self.data_path / f"clt_{chn}_obj_num_cat.csv", 
                            )
                    
            self.results[chn]["results_stm_avg"].to_csv(
                self.data_path / f"results_{chn}_stm_avg.csv",
                )
            self.results[chn]["results_cnd_avg"].to_csv(
                self.data_path / f"results_{chn}_cnd_avg.csv",
                )
            
            # Plots
            self.results[chn]["plot_cluster"].savefig(
                self.data_path  / f"plot_{chn}_cluster.png", format="png")
            
        if self.compare_channels:
            
            self.results["plot_compare"].savefig(
                self.data_path  / "plot_mix.png", format="png")
        
        t1 = time.time()
        print(f"{t1 - t0:.3f}s")