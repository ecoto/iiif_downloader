__author__      = 'Ernesto Coto'
__copyright__   = 'May 2019'

import argparse
import json
import os
import requests
import string
import re
from PIL import Image
import csv

# Constants
IMAGE_MAX_WIDTH = 500

# Functions
def download_iiif_content(document_url, images_base_path, metadata_file_path, image_max_width):
    """
    Downloads the images and metadata from a public JSON IIIF document.
    Arguments:
        document_url: URL pointing to the document.
        images_base_path: Base path folder where to store the downloaded images.
        metadata_file_path: Path to a CSV file where to store the downloaded metadata.
        image_max_width: Max image width of downloaded files.
    """
    print '======='

    print 'Processing document at %s' % document_url
    pattern = re.compile('[^a-zA-Z0-9_]')
    string_accepted = pattern.sub('', string.printable)
    doc_label = doc_attribution = doc_description = None
    images_counter = 0
    images_metadata = []
    try:
        response = requests.get(document_url, allow_redirects=True, verify=False)
        document = response.json()

        if document['@type'] not in [ "sc:Manifest", "sc:Sequence", "sc:Canvas"]:
            raise Exception("Only documents of type sc:Manifest, sc:Sequence, sc:Canvas are supported")
        if 'label' in document:
            doc_label =  document['label']
        if 'attribution' in document:
            doc_attribution =  document['attribution']
        if 'description' in document:
            doc_description =  document['description']

        destination_folder_name = ''.join(filter(lambda afunc: afunc in string_accepted, document['@id']))
        destination_folder_path = os.path.join(images_base_path, destination_folder_name)
        if os.path.exists(destination_folder_path):
            raise Exception("An image folder for this document already exists. Aborting !")
        else:
           os.mkdir(destination_folder_path)

        iterable = {}
        if document['@type'] == "sc:Manifest":
            iterable = document
        if document['@type'] == "sc:Sequence":
            iterable['sequences'] = []
            iterable['sequences'].append( {'canvases': document['canvases'] } )
        if document['@type'] == "sc:Canvas":
            iterable['sequences'] = []
            iterable['sequences'].append( {'canvases': [] } )
            iterable['sequences'][0]['canvases'].append( {'images': document['images'] } )

        for sequence in iterable['sequences']:
            for canvas in sequence['canvases']:
                canvas_label = None
                if 'label' in canvas:
                    canvas_label =  canvas['label']
                for image in canvas['images']:
                    destination_file_path = None
                    image_url = None
                    try:
                        if 'resource' in image and ( ('format' in image['resource'] and 'image' in image['resource']['format']) or
                            ('@type' in image['resource'] and image['resource']['@type']=='dctypes:Image' ) )  :
                            scale_image = False
                            if 'service' in image['resource']:
                                # check the context for the API version
                                if '@context' in image['resource']['service'] and '/1/' in image['resource']['service']['@context']:
                                    # attempt to retrieve files named 'native' is API v1.1 is used
                                    image_url = image['resource']['service']['@id'] + '/full/' + str(image_max_width) + ',/0/native'
                                else:
                                    # attempt to retrieve files named 'default' otherwise
                                    image_url = image['resource']['service']['@id'] + '/full/' + str(image_max_width) + ',/0/default'
                                head_response = requests.head(image_url, allow_redirects=True, verify=False)
                                if head_response.status_code != 200:
                                    response = requests.get(image['resource']['service']['@id'] + '/info.json', allow_redirects=True, verify=False)
                                    service_document = response.json()
                                    if len(service_document['profile']) > 1:
                                        service_profiles = service_document['profile'][1:] # 0 is always a compliance URL
                                        if 'formats' in service_profiles[0]:
                                            image_format = service_profiles[0]['formats'][0] # just use the first format
                                            image_url = image_url + '.' + image_format
                                        else:
                                            image_url = image['resource']['@id']
                                            scale_image = True
                                    else:
                                        image_url = image['resource']['@id']
                                        scale_image = True
                            else:
                                image_url = image['resource']['@id']
                                scale_image = True

                            print 'Downloading %s' % image_url
                            destination_file_path = os.path.join(destination_folder_path, str(images_counter) )
                            r = requests.get(image_url, allow_redirects=True, verify=False)
                            with open(destination_file_path, 'wb') as newimg:
                                newimg.write(r.content)
                            if scale_image:
                                img = Image.open(destination_file_path)
                                imW, imH = img.size
                                if imW > image_max_width: # make sure we are downscaling
                                    scale = float(image_max_width)/imW
                                    img.thumbnail((int(imW*scale), int(imH*scale)), resample=Image.BICUBIC)
                                img.convert('RGB').save(destination_file_path  + '.jpg', 'JPEG') # always store jpg
                                os.remove(destination_file_path)
                            else:
                                img = Image.open(destination_file_path)
                                img.convert('RGB').save(destination_file_path  + '.jpg', 'JPEG') # always store jpg
                                os.remove(destination_file_path)

                            img_metadata = { 'filename': os.path.join(destination_folder_name, str(images_counter) + '.jpg') }
                            if metadata_file_path:
                                # save more metadata of current image
                                img_metadata['file_attributes'] = { }
                                if canvas_label:
                                   img_metadata['file_attributes']['caption'] = canvas_label
                                if doc_label:
                                   img_metadata['file_attributes']['document_label'] = doc_label
                                if doc_attribution:
                                   img_metadata['file_attributes']['document_attribution'] = doc_attribution
                                if doc_description:
                                   img_metadata['file_attributes']['document_description'] = doc_description

                            images_metadata.append(img_metadata)
                            images_counter = images_counter + 1

                    except Exception as e:
                        # remove the file if it was not successfully processed
                        if destination_file_path and os.path.exists(destination_file_path):
                            os.remove(destination_file_path)
                        print 'Exception while accessing image at url %s, skipping. Problem: %s' % (image_url, str(e))
                        pass

        # Save metadata to CSV, if required
        if metadata_file_path:
            print 'Saving metadata to %s' % metadata_file_path
            metadata_file_handler = None
            if os.path.exists(metadata_file_path):
                metadata_file_handler = open(metadata_file_path, 'a')
            else:
                metadata_file_handler = open(metadata_file_path, 'w')
                metadata_file_handler.write('#filename,file_attributes\n')

            csv_writer = csv.writer(metadata_file_handler, lineterminator='\n', delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for item in images_metadata:
                csv_writer.writerow( [item['filename'], json.dumps(item['file_attributes']) ] )

            metadata_file_handler.close()

        downloaded_images_file = os.path.join(images_base_path, 'downloaded_images.txt')
        print 'Saving list of downloaded files to %s' % downloaded_images_file
        with open(downloaded_images_file, 'a' ) as new_files_list:
            for item in images_metadata:
                new_files_list.write(item['filename'] + '\n')

    except Exception as e:
        print e
        pass

    print '======='

def main():
    """ Main method """
    # Parse arguments
    parser = argparse.ArgumentParser(description='IIIF Data Downloader')
    parser.add_argument('iif_document_url', metavar='iif_document_url', type=str, help='URL to IIIF document')
    parser.add_argument('images_base_path', metavar='images_base_path', type=str, help='Base folder to store downloaded images')
    parser.add_argument('-m', dest='metadata_file_path', type=str, default=None, help='Path to the CSV file where to store the downloaded metadata. If equal to "None" no metadata will be downloaded. Default: "None"')
    parser.add_argument('-w', dest='image_max_width', type=str, default=IMAGE_MAX_WIDTH, help='Maximum with (in pixels) of downloaded images. Default: %i' % IMAGE_MAX_WIDTH)
    args = parser.parse_args()

    if not os.path.exists(args.images_base_path):
        os.makedirs(args.images_base_path)

    if args.metadata_file_path and not os.path.exists(os.path.dirname(args.metadata_file_path)):
        os.makedirs(os.path.dirname(args.metadata_file_path))

    response = requests.get(args.iif_document_url, allow_redirects=True, verify=False)
    document = response.json()
    if document['@type'] in [ "sc:Collection" ]:
        for manifest in document['manifests']:
            download_iiif_content(manifest['@id'], args.images_base_path, args.metadata_file_path, args.image_max_width)
    elif document['@type'] in [ "sc:Manifest", "sc:Sequence", "sc:Canvas"]:
        download_iiif_content(args.iif_document_url, args.images_base_path, args.metadata_file_path, args.image_max_width)

if __name__== "__main__":
    main()
