/// Parameters -----------------------------------------------------------------

min_size = 100;

/// Initialize -----------------------------------------------------------------

setBatchMode(true);

setForegroundColor(255, 255, 255);
run("Set Measurements...", "integrated redirect=None decimal=3");

// get paths info
name = getTitle();
stem = File.nameWithoutExtension;
dir = File.directory;

/// Process --------------------------------------------------------------------

// Get mask
run("Duplicate...", "title=mask");
run("32-bit");
run("Subtract Background...", "rolling=10 light");
run("Invert");
run("Gaussian Blur...", "sigma=2");
setAutoThreshold("Otsu dark");
setOption("BlackBackground", true);
run("Convert to Mask");

// Remove small objects
run("Analyze Particles...", "size="+min_size+"-Infinity show=Masks");
close("mask"); rename("mask");
run("Invert LUT");

/// Measure --------------------------------------------------------------------

run("Analyze Particles...", "add");
run("Divide...", "value=255");
roiManager("Measure");

/// Label ----------------------------------------------------------------------

label = 1;
nROIs = roiManager("count");
for (i=0; i<nROIs; i++){
	roiManager("Select", i);
	run("Multiply...", "value="+label);
	label = label + 1;
}

run("glasbey on dark");

/// Terminate ------------------------------------------------------------------

setBatchMode("exit and display")
Table.deleteColumn("RawIntDen");
Table.renameColumn("IntDen", "nPixels");

waitForUser( "Pause","Click Ok when finished");

macro "Close All Windows" {
    while (nImages > 0) {
        selectImage(nImages);
        close();
    }

    if (isOpen("Log")) {selectWindow("Log"); run("Close");}
    if (isOpen("Summary")) {selectWindow("Summary"); run("Close");}
    if (isOpen("Results")) {selectWindow("Results"); run("Close");}
    if (isOpen("ROI Manager")) {selectWindow("ROI Manager"); run("Close");}
    
}
