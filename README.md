# LHT_ImageAnalyzer

An image analyzer for sorting and pre-processing the microstructure images of high temperature ceramic coatings. The LHT_ImageAnalyzer is an application that follows a wizard-like layout to pre-process the microstructure images (can also be used on any other pictures) for better oxide/phase detection. 
Challenges addressed during Microstructure analysis:
1.	Automatically Read magnification based on OCR.
2.	Sort the images into different folders
3.	Crop the region of interest (individually or collectively)
4.	Apply the contrast and brightness enhancements
5.	An intuitive 'pick colour' based brightness control is applied across the whole image for better uniformity during pore detection
6.	Finally, the files are viewed on a clickable file tree to track the applied changes easily and view them across directories.
7.	We connected the application to the Fiji-ImageJ standalone package (not included) to do further complex processing and analysis, including pore percentage calculation.

Installation:
1.	Place the portable "Fiji.app" (https://imagej.net/software/fiji/downloads) and "Tesseract-OCR" (https://osdn.net/frs/g_redir.php?m=acc&f=tesseract-ocr-alt%2Ftesseract-ocr-3.02-win32-portable.zip) in ~\Application
2.	The source directory has some example images to try
3.	A detailed presentation of all the functions of the application (as ppt) is given here: https://www.slideshare.net/secret/3ffgmSchNwmutf (please contact me directly for a ppt with better image quality)


Report on latest bugs:
1.	There is a keyboard interrupt exception during sudden program termination (within the console or pycharm). This is most probably due to the lack of implementing a signal catching for the interrupt key combination: https://keyboardinterrupt.org/catching-a-keyboardinterrupt-signal/
2.	The support for xlsx file has been depreciated during the read operation using xlrd package. So, it had to be downgraded to 1.2.0 for the program to run. An alternative is to use openpyxl.
