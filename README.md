# iiif_downloader

Given the URL to a public JSON document in an [International Image Interoperability Framework (IIIF)](https://iiif.io/) image server, this script will download the images specified in the document as well as part of the metadata associated with each image.

This software was created while working at the [Visual Geometry Group](http://www.robots.ox.ac.uk/~vgg/) at the University of Oxford, and it is incorporated into the [VGG Face Finder (VFF)](http://www.robots.ox.ac.uk/~vgg/software/vff/) and [VGG Image Classification (VIC) Engine](http://www.robots.ox.ac.uk/~vgg/software/vic/) projects.

## Usage

```
python iiif_downloader.py iif_document_url images_base_path [-m metadata_file_path] [-w image_max_width] [-c]
```
where

- **iif_document_url**: URL to IIIF document. The document can be of type *Collection*, *Manifest*, *Sequence* or *Canvas*. The script will work down this hierarchy of types, i.e., if the specified URL points to a *Collection* making reference to several *Manifest* documents, then the images referenced on each *Manifest* will be downloaded. For each *Manifest*, each *Sequence* will be inspected, as well as each *Canvas* referenced on each *Sequence*. However, a *Collection* document referencing other *Collection* documents **IS NOT SUPPORTED**. The same applies to *Manifest* documents referencing other *Manifest* documents, this **IS NOT SUPPORTED**.
- **images_base_path**: Base folder to store downloaded images. The folder will be created if it does not exists. The downloaded images will be stored in subfolders within the *images_base_path*. A new subfolder will be created per *Manifest* in the source IIIF document. Once the script has finished its job, a text file called "downloaded_images.txt" inside *images_base_path* will contain the full list of downloaded images. The images will have numbers as filenames, not the names referred to in the source IIIF document. The images will always be stored in JPEG format.
- **metadata_file_path (optional)**: Path to a CSV file where to store the downloaded metadata. The folder containing the file will be created if it does not exist. The CSV file follows the format of the metadata used by the [vgg_frontend](https://gitlab.com/vgg/vgg_frontend/tree/master#metadata-structure). If the *metadata_file_path* is not specified, no metadata will be downloaded.
- **image_max_width (optional)**: Maximum image width of downloaded files. The width of the images is restricted by *image_max_width* and the height is adjusted to keep the original image aspect-ratio. If the *image_max_width* is not specified, the default value specified in the script is used.
- **c**: Boolean flag that enables SSL certificate verification when accessing the manifest and images. If it is not used, the default behaviour is to not perform certificate verification.

If you want to suppress the "InsecurePlatformWarning" messages, use the "-c" command-line option to enable SSL certificate verification, or use "-W ignore" as shown below
```
python -W ignore iiif_downloader.py iif_document_url images_base_path [-m metadata_file_path] [-w image_max_width]
```

## Requirements

This software runs over Python 2.7 (at least 2.7.12) and should work as well with Python 3. It is advised to create a python virtual environment. Use the following to install the dependencies:

```
pip install -r requirements.txt
```
## License

MIT License, see LICENSE.md
