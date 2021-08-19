path = getArgument; 
lines=split(File.openAsString(path),"\n") 
folder = lines[0];
No_of_files = parseInt(lines[1]);
if (folder == "No")
{
	path = lines[2];
	scale_text = parseInt(lines[3]);
	scale_length = parseInt(lines[4]);
	open(path);
	if (scale_text == 0 || scale_length == 0)
	{
		print("No scale value detected");
		}
	run("Set Scale...", "distance=scale_length known=scale_text unit=microns");
}

if (folder == "Yes")
{
	path = lines[2];
	scale_text = parseInt(lines[3]);
	scale_length = parseInt(lines[4]);
	if (scale_text == 0 || scale_length == 0)
	{
		print("No scale value detected");
		}
	if (No_of_files >1)
	{
		run("Image Sequence...", "open=[path] sort use");
		}
	else
	{
		open(path);
		}
	run("Set Scale...", "distance=scale_length known=scale_text unit=microns");
}