import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"],
                     "include_files": ["common.py", "icons_ImageSort_rc.py", "Ui_ImageSort.py",
                                       "image_sort.py", "icons_ImageCrop_rc.py", "Ui_ImageCrop.py", "image_crop.py",
                                       "Ui_ImageROI.py", "image_roi.py", "Ui_ImageExposure.py",
                                       "Ui_ImagePixelSelection.py", "image_exposure.py", "Ui_ImageAnalyze.py",
                                       "image_analyzer.py"],
                     "includes": ["numpy.core._methods", "numpy.lib.format"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# if 'bdist_msi' in sys.argv:
#     sys.argv += ['--initial-target-dir', 'C:\\Users\\arjun\\Downloads\\Code\\']


setup(name="LHT_Image_Analyzer",
      version="1.0",
      description="Microstructure Image Analyzer Application!",
      options={"build_exe": build_exe_options},
      executables=[Executable(script="main.py", base=base,
                              targetName="ImageAnalyzer.exe")])
