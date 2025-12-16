#%% Imports -------------------------------------------------------------------

import pickle
import napari
import numpy as np
from skimage import io

# Qt
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QGroupBox, QVBoxLayout,
    QRadioButton, QButtonGroup, 
    QWidget, QLabel,
    )

#%% Class(Display) ------------------------------------------------------------

class Display:
    
    def __init__(self, procedure=None, parameters=None):
        
        # Fetch
        self.procedure  = procedure
        self.parameters = parameters
        self.root_path  = parameters["root_path" ]
        self.data_path  = parameters["data_path" ] 
        self.conditions = parameters["conditions"] 
        self.prepare_channels = parameters["prepare_channels"]
        self.process_channels = parameters["process_channels"]
        self.compare_channels = parameters["compare_channels"]
        
        # Run
        if self.procedure["display"]: 
            self.initialize()
            self.init_viewer()
                
#%% Class(Display) : initialize() ---------------------------------------------

    def initialize(self):
        
        self.idx = 0
        if self.parameters[self.process_channels[0]]["grd_sigma"]:
            self.tags = ["none", "prd", "obj", "clt", "grd"]
        else:
            self.tags = ["none", "prd", "obj", "clt"]
        
        with open(self.data_path / "stems.pkl", "rb") as f:
            self.stems = pickle.load(f)
        for chn in self.prepare_channels:
            self.load_images(self.stems, chn=chn, tag="img")
        for chn in self.process_channels:
            for tag in self.tags:
                if tag != "none":
                    self.load_images(self.stems, chn=chn, tag=tag)
                
#%% Class(Display) : function(s) ----------------------------------------------
           
    # Logic & updates ---------------------------------------------------------
        
    def load_images(self, stems, chn="c0", tag="img"):
        name = f"{chn}_{tag}"
        setattr(self, name, [])
        for stem in self.stems:
            out_path = self.data_path / stem
            getattr(self, name).append(io.imread(out_path / (name + ".tif"))) 
        setattr(self, name, np.stack(getattr(self, name)))
    
    def sync_step(self, event):
        current_step = self.vwr.dims.current_step[0]
        if self.idx != current_step:
            self.idx = int(current_step)
            self.info.setText(self.get_info())

    # Buttons -----------------------------------------------------------------
    
    def select_layers(self, checked):
        
        if not checked:
            return
        
        self.active_chn = self.chn_group.checkedButton().text()
        self.active_tag = self.tag_group.checkedButton().text()
        if self.active_tag == "none":
            self.active_layers = {f"{self.active_chn}_img"}
        elif self.active_tag == "grd":
            self.active_layers = {f"{self.active_chn}_grd"}
        else:
            self.active_layers = {
                f"{self.active_chn}_img",
                f"{self.active_chn}_{self.active_tag}",
                }
        
        for layer in self.vwr.layers:
            layer.visible = (layer.name in self.active_layers)
                
    # Info --------------------------------------------------------------------
        
    def get_info(self):
        stem = self.stems[self.idx]
        return (
            f"{self.idx:02d} - {stem}\n"
            "press 'delete' to hide output layer(s)"
            )
                
#%% Class(Display) : init_viewer() --------------------------------------------                

    def init_viewer(self):
                
        # Viewer --------------------------------------------------------------
        
        self.vwr = napari.Viewer()
       
        # Create "channel" menu
        self.chn_group = QButtonGroup()
        self.chn_group_box = QGroupBox("Select channel")
        self.chn_group_layout = QVBoxLayout()
        for chn in self.prepare_channels:
            setattr(self, f"rad_{chn}", QRadioButton(f"{chn}"))
            if chn == self.prepare_channels[0]:
                getattr(self, f"rad_{chn}").setChecked(True)
            self.chn_group.addButton(getattr(self, f"rad_{chn}"))
            self.chn_group_layout.addWidget(getattr(self, f"rad_{chn}"))
            getattr(self, f"rad_{chn}").toggled.connect(self.select_layers)
        self.chn_group_box.setLayout(self.chn_group_layout)
        
        # Create "output" menu
        self.tag_group = QButtonGroup()
        self.tag_group_box = QGroupBox("Select output")
        self.tag_group_layout = QVBoxLayout()
        for tag in self.tags:
            setattr(self, f"rad_{tag}", QRadioButton(f"{tag}"))
            if tag == "none":
                getattr(self, f"rad_{tag}").setChecked(True)
            self.tag_group.addButton(getattr(self, f"rad_{tag}"))
            self.tag_group_layout.addWidget(getattr(self, f"rad_{tag}"))
            getattr(self, f"rad_{tag}").toggled.connect(self.select_layers)
        self.tag_group_box.setLayout(self.tag_group_layout)
        
        # Create texts
        self.info = QLabel()
        self.info.setFont(QFont("Consolas"))
        self.info.setText(self.get_info())
                
        # Create layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.chn_group_box)
        self.layout.addWidget(self.tag_group_box)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.info)

        # Create widget
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.vwr.window.add_dock_widget(
            self.widget, area="right", name="Painter") 
        
        # Initialize
        self.init_layers()   
        self.select_layers(True)   
        self.vwr.dims.events.current_step.connect(self.sync_step)
        
        # Shortcuts -----------------------------------------------------------
                                
        @self.vwr.bind_key("Delete", overwrite=True)
        def hide_output_layers_key(viewer):
            layers_to_hide = [
                layer for layer in self.vwr.layers
                if "img" not in layer.name and layer.visible
                ]
            for layer in layers_to_hide:
                layer.visible = False
            yield
            for layer in layers_to_hide:
                layer.visible = True
            
#%% Class(Display) : init_layers() --------------------------------------------

    def init_layers(self):  
                
        for chn in reversed(self.prepare_channels): 
        
            # Channel
            self.vwr.add_image(
                getattr(self, f"{chn}_img"), name=f"{chn}_img", visible=0,
                colormap="gray", blending="additive", 
                gamma=1.0, opacity=0.66,
                )        
            
        for chn in reversed(self.process_channels):
            
            # Prediction
            self.vwr.add_image(
                getattr(self, f"{chn}_prd"), name=f"{chn}_prd", visible=0,
                colormap="inferno", blending="additive", 
                gamma=1.0, opacity=0.33,
                )
            
            # Label
            for tag in ["obj", "clt"]:
                
                self.vwr.add_labels(
                    getattr(self, f"{chn}_{tag}"), name=f"{chn}_{tag}", visible=0,
                    blending="additive", 
                    opacity=0.33,
                    )
                
            # Gradient
            if self.parameters[chn]["grd_sigma"]:
                
                self.vwr.add_image(
                    getattr(self, f"{chn}_grd"), name=f"{chn}_grd", visible=0,
                    colormap="gray", blending="additive", 
                    gamma=1.0, opacity=1.00,
                    )