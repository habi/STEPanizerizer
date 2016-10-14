# STEPanizerizer

You have a tomographic dataset with *lots* of reconstructed slices, with isometric voxel size.
You want to perform [http://enwp.org/stereology](stereological analysis) on this dataset with the [STEPanizer](http://stepanizer.com/).
Exporting and renaming an uniform random sample of (thousands of) slices is annoying manual work.

STEPanizerizer [1] to the rescue!
You give the Python script a dataset folder as input and tell it how many slices you'd like to have ready for counting.
After a bit of waiting, you have the requested number of files as correctly numbered JPG images waiting in another folder, ready for your counting pleasure.

[1]: I know, the name could be spiffier :)
