## Comments

- Meeting 19/09/2025  
    - Add shape + density/porosity descriptors
    - Configurable categories for cluster object number (currently 2, 5, & 10)  
    - Horizontal bar plot (1 bar, 3 colors) to show these categories 
    - Add the phase-contrast image to the Napari display
    
- Meeting 24/11/2025
    
    - Short term goals:
    Finish chris analysis with simple segmentation, no object separation. 
    Run the same analysis on Suwannee data.
    The mixing measurment needs to be added in both cases. 
    Consider filter on cluster size to exclude isolated cells from the analysis.
    
    - Longer term goals:
    The idea will be to refactorize the code, extracting common parts to 
    facilitate curation. In some cases I would need object separation while in
    other cases I will go for simple segmentation. There is cases where only 
    one channel is available and other cases where two channels need to be 
    segmented and mixing between those channels needs to be measured. Also, 
    I need to come with a strategy regarding what is considered a cluster in
    the merged csv and plots. I can filter clusters acc. to object number and/
    or area (especially interesting when no object separation). The ultimate 
    goal would be to control the procedure from Napari GUI. 