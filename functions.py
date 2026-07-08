#%% Imports -------------------------------------------------------------------

import nd2
import shutil
import warnings
import numpy as np
import pandas as pd
from skimage import io
from pathlib import Path

# bdtools
from bdtools.norm import norm_pct
from bdtools.patch import extract_patches

# skimage
from skimage.filters import gaussian, sato
from skimage.measure import label, regionprops
from skimage.morphology import disk, binary_closing, remove_small_objects
from skimage.segmentation import watershed, expand_labels, relabel_sequential

# matplotlib
import matplotlib.pyplot as plt

# colors
from colors import fcolors

#%% Function(s) ---------------------------------------------------------------

def clear_data(data_path, procedure=None):
    
    def remove_folders():
        for sub in data_path.iterdir():
            if sub.is_dir():
                shutil.rmtree(sub)
       
    def remove_glob_files():
        for file in data_path.glob("*.csv"):
            file.unlink()
        for file in data_path.glob("*.png"):
            file.unlink()
    
    def remove_rglob_files():
        for file in data_path.rglob("*.csv"):
            file.unlink()
        for file in data_path.rglob("*.pkl"):
            if file.name != "stems.pkl":
                file.unlink()
            
    def remove_images(tags=None):
        for tag in tags:
            for file in data_path.rglob(f"*{tag}.tif"):
                file.unlink()
        
    if procedure == "prepare":
        remove_glob_files()
        remove_folders()
        
    if procedure == "predict":
        remove_rglob_files()
        remove_images(tags=["prd", "obj", "clt", "grd"])
    
    if procedure == "process":
        remove_rglob_files()
        remove_images(tags=["obj", "clt", "grd"])
    
    if procedure == "analyse":
        remove_glob_files()

#%% Function(s) : extract() ---------------------------------------------------

def load_data(data_path):
    
    data = []
    nd2_paths = list(data_path.rglob("*.nd2"))
    for path in nd2_paths:
        arr = nd2.imread(path) 
        nC = arr.shape[-3]
        stm = path.stem
        if arr.ndim == 3:
            data.append(
                tuple([stm] + [arr[c] for c in range(nC)]))
        elif arr.ndim == 4:
            for i in range(arr.shape[0]):
                data.append(
                    tuple([f"{stm}_{i:02d}"] + [arr[i, c] for c in range(nC)]))
                
    if not data:
        print("no .nd2 files found.")
        return [], [], [], []
                
    return tuple(zip(*data))

def normalize_data(arr, low_qtl=0.25):
    
    # low val. norm.
    nrm = np.zeros_like(arr, dtype=float)
    for i, img in enumerate(arr):
        if low_qtl is not None:
            low_val = np.quantile(img, low_qtl)
            nrm[i, ...] = img / low_val
        else:
            nrm[i, ...] = img
    
    # 0 to 1 norm.
    nrm = norm_pct(nrm, pct_low=0.001, pct_high=99.999)
    
    return (nrm * 255).astype("uint8")

def save_patches(arr, stems, chn="c1", patch_num=10, patch_size=256):
    for i, img in enumerate(arr): 
        patches = extract_patches(img, patch_size, 0)
        p_idxs = np.random.choice(
            np.arange(0, len(patches)), size=patch_num, replace=False)
        for idx in p_idxs:
            patch = patches[idx]
            save_path = Path.cwd() / "data" / f"{chn}_train" 
            save_name = f"{stems[i]}_{chn}_{idx:02d}.tif"
            io.imsave(save_path / save_name, patch, check_contrast=False)

#%% Function(s) : predict() ---------------------------------------------------

def get_model_path(root_path, tags=["normal", "c0"]):
    
    if isinstance(tags, str):
        tags = [tags]
    
    model_paths = [
        item for item in root_path.iterdir()
        if item.is_dir() and all(t in item.name for t in tags)
        ]
    
    return model_paths[0]
    
def merge_predictions(
        prd_edt, prd_interfaces, prd_skeletons, prd_coeff=3, prd_sigma=1):
    prd_edt = prd_edt.astype(float)
    prd_interfaces = prd_interfaces.astype(float) * prd_coeff
    prd_skeletons = prd_skeletons.astype(float) * prd_coeff
    prd_merge = (prd_edt - prd_interfaces + prd_skeletons)
    prd_merge = gaussian(
        prd_merge, sigma=prd_sigma, preserve_range=True)
    prd_merge[prd_merge < 0] = 0
    return norm_pct(prd_merge)

#%% Function(s) : process() - images ------------------------------------------

def get_objects(prd, thresh_0=0.5, thresh_1=None, min_size=32):
    msk_0 = prd > thresh_0
    if thresh_1 is not None:
        msk_1 = prd > thresh_1
        for prop in regionprops(label(msk_0), intensity_image=msk_1):
            coords = prop.coords
            if prop.intensity_max == 0:
                msk_1[tuple(coords.T)] = 1
        obj = watershed(-prd, markers=label(msk_1), mask=msk_0)
    else:
        obj = label(msk_0)
    if np.max(obj) < 2:
        obj = remove_small_objects(obj > 0, min_size=min_size)
    else:
        obj = remove_small_objects(obj, min_size=min_size)
    return obj.astype("uint16")
    
def get_clusters(obj, max_dist=5):
    clt = label(binary_closing(obj > 0, footprint=disk(max_dist)))
    clt[obj == 0] = 0   
    return clt.astype("uint16")

def get_gradient(img, sigma=1):
    return sato(gaussian(
        img, sigma=sigma, preserve_range=True),
        sigmas=[sigma]).astype("float32")

def filter_acc2_gradient(img, obj, clt, grd, min_grd=None):
    if min_grd is not None:
        clt_exp = expand_labels(clt, distance=3) # parameter
        clt_grd = np.zeros_like(grd)
        for prop in regionprops(clt_exp):
            coords = tuple(prop.coords.T)
            clt_grd[coords] = np.mean(grd[coords]) / np.mean(img[coords])
        obj[clt_grd < min_grd] = 0
        clt[clt_grd < min_grd] = 0
        obj = relabel_sequential(obj)[0].astype("uint16")
        clt = relabel_sequential(clt)[0].astype("uint16")   
    return obj, clt

#%% Function(s) : process() - results -----------------------------------------
        
def get_mix_ratio(results, lbl_0, lbl_1, tag="c1"):
    mix_ratio = []
    lbl_1 = lbl_1 > 0
    for idx in results["index"]:
        msk = (lbl_0 == idx)
        mix_ratio.append(np.mean(lbl_1[msk]))
    results[f"{tag}_mix_ratio"] = mix_ratio
            
def get_obj_results(stem, img, obj, clt, grd=None):

    obj_results = {
        "stem"      : [],
        "index"     : [],
        "clt_index" : [],
        "ctrd_y"    : [],
        "ctrd_x"    : [],
        "area"      : [],
        "intensity" : [],
        }
 
    if grd is not None:
        obj_results["gradient"] = []
        
    for prop in regionprops(obj, intensity_image=clt):
        index = prop.label
        coords = prop.coords
        obj_results["stem"     ].append(stem)
        obj_results["index"    ].append(index)
        obj_results["clt_index"].append(prop.intensity_max)
        obj_results["ctrd_y"   ].append(prop.centroid[1])
        obj_results["ctrd_x"   ].append(prop.centroid[0])
        obj_results["area"     ].append(prop.area)
        obj_results["intensity"].append(np.mean(img[tuple(coords.T)]))
        
        if grd is not None:
            obj_results["gradient"].append(np.std(grd[tuple(coords.T)]))

    return obj_results

def get_clt_results(stem, img, obj, clt, grd=None):
    
    clt_results = {
        "stem"         : [],
        "index"        : [],
        "obj_num"      : [],
        "ctrd_y"       : [],
        "ctrd_x"       : [],
        "area"         : [],
        "intensity"    : [],
        "circularity"  : [],
        "solidity"     : [],
        "eccentricity" : [],
        }
    
    if grd is not None:
        clt_results["gradient"] = []
    
    for prop in regionprops(clt):
        index = prop.label
        coords = prop.coords
        obj_num = len(np.unique(obj[tuple(coords.T)]))
        circularity = (4 * np.pi * prop.area) / prop.perimeter**2
        clt_results["stem"        ].append(stem)
        clt_results["index"       ].append(index)
        clt_results["obj_num"     ].append(obj_num)
        clt_results["ctrd_y"      ].append(prop.centroid[1])
        clt_results["ctrd_x"      ].append(prop.centroid[0])
        clt_results["area"        ].append(prop.area)
        clt_results["intensity"   ].append(np.mean(img[tuple(coords.T)]))
        clt_results["circularity" ].append(circularity)
        clt_results["solidity"    ].append(prop.solidity)
        clt_results["eccentricity"].append(prop.eccentricity)
        
        if grd is not None:
            clt_results["gradient"].append(np.std(grd[tuple(coords.T)]))
    
    return clt_results   

#%% Function(s) : analyse() - results -----------------------------------------
    
def filter_clusters(df_all, min_clt_obj_num, min_clt_area):
    clt_obj_num = np.array(df_all["obj_num"])
    clt_area = np.array(df_all["area"])
    idx = (clt_obj_num >= min_clt_obj_num) & (clt_area >= min_clt_area)
    return df_all[idx]
    
def get_clt_obj_num_dist(df_all, conditions):

    max_obj_num = np.max(df_all["obj_num"]) + 1
    
    clt_obj_num_dist = pd.DataFrame()
    for cond in conditions:
        df = df_all[df_all["stem"].str.contains(cond, case=False, na=False)]
        
        # val = np.array(df["obj_num"]) 
        # /////////////////////////////////////////////////////////////////////
        
        val = pd.to_numeric(df["obj_num"], errors="coerce").fillna(0).astype(int).to_numpy()
        
        # /////////////////////////////////////////////////////////////////////
        
        count = np.bincount(val, minlength=max_obj_num)
        
        # count = count / count.sum()
        # /////////////////////////////////////////////////////////////////////
        
        count_sum = count.sum()
        if count_sum > 0:
            count = count / count_sum
        else:
            count = count.astype(float)
        
        # /////////////////////////////////////////////////////////////////////
        
        clt_obj_num_dist[f"{cond}"] = count
        clt_obj_num_dist.index.name = "clt_obj_num"
    
    return clt_obj_num_dist

def get_clt_obj_num_cat(df_all, conditions, categories):
    
    clt_obj_num_cat = pd.DataFrame()
    for cond in conditions:
        df = df_all[df_all["stem"].str.contains(cond, case=False, na=False)]
        val = np.array(df["obj_num"])
        for c, cat in enumerate(categories):
            if c == 0:
                cat_name = f"1-{cat - 1}"
                count = np.sum(val < cat)
                clt_obj_num_cat.loc[cat_name, f"{cond}"] = count
            elif c < len(categories) - 1:
                cat_name = f"{categories[c - 1]}-{cat}"
                count = np.sum((val >= categories[c - 1]) & (val <= cat))
                clt_obj_num_cat.loc[cat_name, f"{cond}"] = count
            else:
                cat_name_0 = f"{categories[c - 1]}-{cat}"
                count_0 = np.sum((val >= categories[c - 1]) & (val <= cat))
                clt_obj_num_cat.loc[cat_name_0, f"{cond}"] = count_0
                cat_name_1 = f">{cat}"
                count_1 = np.sum(val > cat)
                clt_obj_num_cat.loc[cat_name_1, f"{cond}"] = count_1
    
        clt_obj_num_cat[f"{cond}"] = (
            clt_obj_num_cat[f"{cond}"] / clt_obj_num_cat[f"{cond}"].sum())
        clt_obj_num_cat.index.name = "clt_obj_num"
    
    return clt_obj_num_cat
    
def avg_results_stem(results, stems):
    
    def avg_stem(
            df_stm_avg, results=results,
            tag="obj", measure="area", 
            ):
        
        warnings.filterwarnings(
            "ignore", category=RuntimeWarning, 
            message="Mean of empty slice"
            )
        
        f = "_f" if tag == "clt" else ""
        df_stm = results[f"{tag}_results_stm{f}"]           
        df_stm_avg[f"{tag}_{measure}_avg"] = [
            np.nanmean(df[measure]) for df in df_stm]

    df_stm_avg = pd.DataFrame()  
    obj_stm   = results["obj_results_stm"  ]
    clt_stm   = results["clt_results_stm"  ]
    clt_stm_f = results["clt_results_stm_f"]
    obj_num   = [len(df) for df in obj_stm  ]
    clt_num   = [len(df) for df in clt_stm  ]
    clt_num_f = [len(df) for df in clt_stm_f]
    df_stm_avg["stem"     ] = stems
    df_stm_avg["obj_num"  ] = obj_num
    df_stm_avg["clt_num"  ] = clt_num_f
    
    # df_stm_avg["clt_ratio"] = np.array(clt_num_f) / np.array(clt_num)
    # /////////////////////////////////////////////////////////////////////////
    
    num_f = np.array(clt_num_f)
    num_all = np.array(clt_num)
    df_stm_avg["clt_ratio"] = np.divide(
        num_f, num_all, 
        out=np.zeros_like(num_f, dtype=float), 
        where=num_all > 0
        )
    
    # /////////////////////////////////////////////////////////////////////////
    
    for tag in ["obj", "clt"]:
        avg_stem(df_stm_avg, tag=tag, measure="area")
        avg_stem(df_stm_avg, tag=tag, measure="intensity")
        if "gradient" in obj_stm[0]:
            avg_stem(df_stm_avg, tag=tag, measure="gradient")
        mix_ratios = [key for key in obj_stm[0] if "mix_ratio" in key] 
        for mix_ratio in mix_ratios:
            avg_stem(df_stm_avg, tag=tag, measure=mix_ratio)
        if tag == "clt":
            avg_stem(df_stm_avg, tag=tag, measure="obj_num")
            avg_stem(df_stm_avg, tag=tag, measure="circularity")
            avg_stem(df_stm_avg, tag=tag, measure="solidity")
            avg_stem(df_stm_avg, tag=tag, measure="eccentricity")
    
    return df_stm_avg

def avg_results_cond(results, conditions):
    df_stm_avg = results["results_stm_avg"]
    df_cnd_avg = pd.DataFrame()
    for cond in conditions:
        df_sub = df_stm_avg[df_stm_avg["stem"].str.contains(
            cond, case=False, na=False)]
        df_cnd_avg[f"{cond}_avg"] = df_sub.mean(numeric_only=True)
        df_cnd_avg[f"{cond}_std"] = df_sub.std (numeric_only=True)
        df_cnd_avg[f"{cond}_sem"] = df_sub.sem (numeric_only=True)
    return df_cnd_avg.T

def process_results(
        data_path, stems, conditions, categories,
        segmentation, min_clt_obj_num, min_clt_area,
        chn="c0",
        ):
            
    results = {}
            
    for tag in ["obj", "clt"]:
    
        # Load & concatenate
        
        df_stm = []
        for stem in stems:
            out_path = data_path / stem
            df = pd.read_csv(out_path / f"{chn}_{tag}_results.csv")
            df_stm.append(df)
        results[f"{tag}_results_stm"] = df_stm
        
        valid_dfs = [d for d in df_stm if not d.empty]
        if valid_dfs:
            df_all = pd.concat(
                valid_dfs, ignore_index=False).reset_index(drop=True)
        else:
            df_all = pd.DataFrame(columns=df.columns)
        results[f"{tag}_results_all"] = df_all
        
        if tag == "clt":

            df_stm_f = []
            for stem in stems:
                out_path = data_path / stem
                df = pd.read_csv(out_path / f"{chn}_{tag}_results.csv")
                df_f = filter_clusters(
                    df, min_clt_obj_num, min_clt_area)
                df_stm_f.append(df_f)
            results[f"{tag}_results_stm_f"] = df_stm_f
            
            valid_dfs_f = [d for d in df_stm_f if len(d) > 0]
            if valid_dfs_f:
                df_all_f = pd.concat(valid_dfs_f, ignore_index=False)
                df_all_f = df_all_f.reset_index(drop=True)
            else:
                df_all_f = pd.DataFrame(columns=df.columns)
                
            results[f"{tag}_results_all_f"] = df_all_f
        
            # Cluster distribution & categories
            if segmentation == "instance":
                results["clt_obj_num_dist"] = get_clt_obj_num_dist(
                    df_all, conditions)
                results["clt_obj_num_cat" ] = get_clt_obj_num_cat(
                    df_all, conditions, categories)

    # Average stem
    results["results_stm_avg"] = avg_results_stem(results, stems)
    
    # Average cond
    results["results_cnd_avg"] = avg_results_cond(results, conditions)
    
    return results

#%% Function(s) : analyse() - plot_clusters() ---------------------------------

def plot_clusters(
        results, data_path, stems, conditions, conds_color, shade_color, 
        segmentation, min_clt_obj_num, min_clt_area, 
        chn="c0",
        ):

    tags_0 = [
        "obj_num", "clt_num", "clt_ratio", "clt_obj_num_avg",
        "clt_area_avg", "clt_intensity_avg",
        "clt_circularity_avg", "clt_solidity_avg", "clt_eccentricity_avg",
        ]
    tags_1 = ["clt_obj_num_dist"]
    tags_2 = ["clt_obj_num_cat"]
    tags = tags_0 + tags_1 + tags_2
        
    # Initialize plot
    fig = plt.figure(figsize=(12, 12))
    fig.suptitle(
        f"results clusters ({chn}) - {segmentation}",
        fontsize=20, x=0.05, ha="left"
        )
    
    if segmentation == "instance":
        gs = fig.add_gridspec(3, 5)
    else:
        gs = fig.add_gridspec(2, 5)
        
    axes = [
        fig.add_subplot(gs[0, 0 ]),
        fig.add_subplot(gs[0, 1 ]),
        fig.add_subplot(gs[0, 2 ]),
        fig.add_subplot(gs[0, 3 ]),
        fig.add_subplot(gs[-1, 0]),
        fig.add_subplot(gs[-1, 1]),
        fig.add_subplot(gs[-1, 2]),
        fig.add_subplot(gs[-1, 3]),
        fig.add_subplot(gs[-1, 4]),
        ]
    
    if segmentation == "instance":
        axes.append(fig.add_subplot(gs[1, :2 ]))
        axes.append(fig.add_subplot(gs[1, 2:4]))
    
    for i, (ax, tag) in enumerate(zip(axes, tags)):
        for c, cond in enumerate(conditions):    
            
            if tag in tags_0:
                
                # Data
                avg, sem = (
                    results[chn]["results_cnd_avg"].loc[f"{cond}_avg", tag],
                    results[chn]["results_cnd_avg"].loc[f"{cond}_sem", tag],
                    )
                
                # Plot
                ax.bar(
                    c, avg, yerr=sem, capsize=5, alpha=1, width=0.8,
                    color=fcolors[f"{conds_color[c]}_40"],
                    )
                
                # Formatting
                ax.set_xticks(np.arange(len(conditions)))
                ax.set_xticklabels(conditions, rotation=45)
                ax.set_ylabel(tag)
                if tag == "obj_num":
                    ax.set_title(tag)
                else:
                    ax.set_title(
                        f"{tag}\n"
                        f"params. ({min_clt_obj_num}, {min_clt_area})"
                        )
                    
            if tag in tags_1 and segmentation == "instance":
                
                width = 0.25
                max_dist = 12
                
                # data
                dist = results[chn]["clt_obj_num_dist"][cond][:max_dist + 1]
                
                # Plot
                ax.bar(
                    np.arange(max_dist + 1) - width + (width * c), dist, 
                    alpha=1, width=width, 
                    color=fcolors[f"{conds_color[c]}_40"],
                    )
                
                # Formatting         
                ax.set_xlim(0, max_dist + 1)
                ax.set_xticks(np.arange(1, max_dist + 1, 1))
                ax.set_xlabel("clt_obj_num")
                ax.set_ylabel("count")
                ax.set_title("clt_obj_num_dist")
                
            if tag in tags_2 and segmentation == "instance":
                
                df = results[chn]["clt_obj_num_cat"]
                cat_names = " ".join(f"[{s}]" for s in df.index.tolist())
                vals = df[cond].to_numpy()
                
                # Plot
                left = 0
                for i, val in enumerate(vals):
                    color = fcolors[f"{conds_color[c]}_{shade_color[i]}"],
                    ax.barh(c, val, left=left, color=color)
                    left += val
                    
                # Formatting 
                ax.set_xlim(0, 1.0)
                ax.set_xticks(np.arange(0, 1.1, 0.1))
                ax.set_xlabel("count")
                ax.invert_yaxis()
                ax.set_yticks(np.arange(len(conditions)))
                ax.set_yticklabels(conditions)
                ax.set_title(
                    f"clt_obj_num_cat {cat_names}"
                    )

    plt.tight_layout() 
    
    return fig

#%% Function(s) : analyse() - plot_compare() ----------------------------------

def plot_compare(
        results, data_path, conditions, chns_color,
        segmentation, min_clt_obj_num, min_clt_area, 
        chns=["c0", "c1"]
        ):
    
    tags = [
        "obj_num", "clt_num", "clt_ratio", "clt_obj_num_avg",
        "mix_ratio_avg", "clt_area_avg", "clt_intensity_avg",
        "clt_circularity_avg", "clt_solidity_avg", "clt_eccentricity_avg",
        ]
    
    # Initialize plot
    fig = plt.figure(figsize=(12, 12))
    fig.suptitle(
        f"results mix ({chns}) - {segmentation}",
        fontsize=20, x=0.05, ha="left"
        )
    
    gs = fig.add_gridspec(3, 4)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[0, 3]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[1, 2]),
        fig.add_subplot(gs[2, 0]),
        fig.add_subplot(gs[2, 1]),
        fig.add_subplot(gs[2, 2]),
        ]
    
    for i, (ax, tag) in enumerate(zip(axes, tags)):
        for co, cond in enumerate(conditions):
                
            width = 0.4
            
            for ch, chn in enumerate(chns):
                
                # Data
                
                if tag == "mix_ratio_avg":
                    
                    avg, sem = (
                        results[chn]["results_cnd_avg"].loc[
                            f"{cond}_avg", f"clt_{chns[1 - ch]}_{tag}"],
                        results[chn]["results_cnd_avg"].loc[
                            f"{cond}_sem", f"clt_{chns[1 - ch]}_{tag}"],
                        )  
                    
                else:
                
                    avg, sem = (
                        results[chn]["results_cnd_avg"].loc[
                            f"{cond}_avg", tag],
                        results[chn]["results_cnd_avg"].loc[
                            f"{cond}_sem", tag],
                        )
                
                # Plot
                ax.bar(
                    co - width / 2 + (width * ch), 
                    avg, yerr=sem, capsize=5, alpha=1, width=width,
                    color=fcolors[f"{chns_color[ch]}_40"],
                    )
                
            # Formatting
            ax.set_xticks(np.arange(len(conditions)))
            ax.set_xticklabels(conditions, rotation=45)
            ax.set_ylabel(tag)
            if tag == "obj_num":
                ax.set_title(tag)
            else:
                ax.set_title(
                    f"{tag}\n"
                    f"params. ({min_clt_obj_num}, {min_clt_area})"
                    )

    plt.tight_layout() 

    return fig