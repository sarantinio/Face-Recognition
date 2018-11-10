import argparse
import io
import pickle
import zipfile
from zipfile import ZipFile
import shutil
import ntpath
import requests
import json
import math
import numpy as np
import cv2
import os

import time


def create_zip_from_dataset(input_folder, output_folder, num_images=3, bundle_size=16):
    if num_images * bundle_size > 50:
        print("You're using more than 50 images per bundle, API will probably reject this")
        return
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    # get all folders in input_folder
    print("Reading folders...")
    folders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]

    # iterate through bundles, assign name and folder
    for bundle_index in range(int(math.ceil(len(folders) / bundle_size))):

        bundle_name = 'bundle' + '_' + str(bundle_index)
        image_dump_folder = os.path.join(output_folder, bundle_name)
        os.mkdir(image_dump_folder)

        # for each folder belonging to this bundle
        for folder in folders[bundle_index * bundle_size:bundle_index * bundle_size + bundle_size]:
            print(folder)
            # get all files in each folder, take only a specified number of them
            folder_path = os.path.join(input_folder, folder)
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            selected_files = files[:num_images]

            # copy each file to the image_dump_folder and rename it to the form foldername_i.jpg
            for i, file in enumerate(selected_files):
                shutil.copy2(os.path.join(input_folder, folder, file), image_dump_folder)
                new_file_name = folder + '_' + str(i) + '.jpg'
                os.rename(os.path.join(image_dump_folder, file), os.path.join(image_dump_folder, new_file_name))

        # make archive from the images
        shutil.make_archive(os.path.join(output_folder, bundle_name), "zip", image_dump_folder)

        # delete the images, keep the zip only, then go to the next bundle
        shutil.rmtree(image_dump_folder)


def download_api_results(output_folder, bundle_dict_path, sleep_time):
    bundle_dict = pickle.load(open(bundle_dict_path, 'rb'))
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    # for bundle, response in bundle_dict.items():
    #     print(bundle, response, "<Response [200]>" not in str(response))

    for bundle, response in bundle_dict.items():
        if "<Response [200]>" not in str(response):
            continue

        bundle_folder = os.path.join(output_folder, bundle.split(".")[0])
        if os.path.isdir(bundle_folder):
            print("Already downloaded! Skipping " + bundle)
            continue

        print("Getting " + bundle)
        process_id = json.loads(response.text)['processId']

        # build the download link using processId
        url = "http://yourface.3duniversum.com/uploaded/" + process_id + "/batch_processed.zip"
        start_time = time.time()
        res = requests.get(url)
        if not res.ok:
            print("File not found! Skipping " + bundle)
            continue

        try:
            zip_file = zipfile.ZipFile(io.BytesIO(res.content))
        except Exception as e:
            print(str(e) + "skipping bundle " + bundle)
            continue

        zip_file.extractall(bundle_folder)
        zip_file.close()
        print("Download successful! Time: " + str(time.time() - start_time))
        time.sleep(sleep_time)


"""
ordering cancer:
0.0 -> 0
0.1 -> 1
0.2 -> 12
1.0 -> 17
1.1 -> 18
1.2 -> 19
2.0 -> 20
2.1 -> 21
2.2 -> 22
3.0 -> 23
3.1 -> 2
3.2 -> 3
4.0 -> 4
4.1 -> 5
4.2 -> 6
5.0 -> 7
5.1 -> 8
5.2 -> 9
6.0 -> 10
6.1 -> 11
6.2 -> 13
7.0 -> 14
7.1 -> 15
7.2 -> 16
"""


# def add_api_results(path_to_zip, path_to_dataset, num_images, num_augments):
def reorganize_results(bundle_folder, processed_bundle_folder, output_folder, augment_types):
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    # get all processed bundles(folders)
    processed_bundles = [f for f in os.listdir(processed_bundle_folder) if
                         os.path.isdir(os.path.join(processed_bundle_folder, f))]

    for bundle in processed_bundles:
        # open the original zip and get the list of file names
        zip = zipfile.ZipFile(os.path.join(bundle_folder, bundle + ".zip"))
        orig_file_names = zip.namelist()

        # I'm so titled I'm not even going to bother explaining why this is needed
        cancer = [0, 1, 12, 17, 18, 19, 20, 21, 22, 23, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16]

        for i, file_name in enumerate(orig_file_names):
            # the beginning of the file name is the name of the original folder = the identity of the person
            folder_name = file_name.split("_")[0]

            if not os.path.isdir(os.path.join(output_folder, folder_name)):
                os.mkdir(os.path.join(output_folder, folder_name))

            # copy all augmented files to that person's folder
            for augment in augment_types:
                # i represents the number of the folder inside the processed bundle, each containts multiple augments for 1 image
                shutil.copy2(os.path.join(processed_bundle_folder, bundle, str(cancer[i]), augment),
                             os.path.join(output_folder, folder_name))
                os.rename(os.path.join(output_folder, folder_name, augment),
                          os.path.join(output_folder, folder_name, file_name.split(".")[0] + "_" + augment))

        """
        for i, file_name in enumerate(orig_file_names):
            # the beginning of the file name is the name of the original folder = the identity of the person
            folder_name = file_name.split("_")[0]

            if not os.path.isdir(os.path.join(output_folder, folder_name)):
                os.mkdir(os.path.join(output_folder, folder_name))

            # copy all augmented files to that person's folder
            for augment in augment_types:
                # i represents the number of the folder inside the processed bundle, each containts multiple augments for 1 image
                shutil.copy2(os.path.join(processed_bundle_folder, bundle, str(i), augment),
                             os.path.join(output_folder, folder_name))
                os.rename(os.path.join(output_folder, folder_name, augment),
                          os.path.join(output_folder, folder_name, file_name.split(".")[0] + "_" + augment))
        """

def query_api(yaw, pitch, roll, bundle_path, email):
    url = 'http://yourface.3duniversum.com/api/faceGen/upload'
    file = open(bundle_path, 'rb')  # flat structure zip file

    files = {'images': (bundle_path, file)}
    payload = {
        "glasses": {
            "models": ["HazzBerry"],  # available glasses model
            "materials": [
                {
                    "name": "Obsidian Black",  # tag name
                    "frame": {"color": "rgb(0,0,0)"},  # frame color
                    "glass": {"color": "rgb(255, 255, 255)", "opacity": 0.3}  # glass may have shader issue
                }
            ]
        },
        "poses": [
            {
                "yaw": yaw,  # it can be range (min, max, interval)
                "pitch": pitch,
                "roll": roll  # or just a single value
            }
        ]
    }

    data = {
        "variants": json.dumps(payload),
        "email": email,
    }

    r = requests.post(url, files=files, data=data)
    file.close()

    # r_json = json.loads(r.text)
    # print(r)
    # print(type(r_json))
    # print(r_json['processId'])
    return r


def query_api_testing():
    import requests
    import json
    import os

    url = 'http://yourface.3duniversum.com/api/faceGen/upload'
    file = open('bundle_0.zip', 'rb')  # flat structure zip file

    files = {'images': ('bundle_0.zip', file)}
    payload = {
        "glasses": {
            #         "models": ["HazzBerry", "GerretLight", "Enzo", "M14", "M10"],                # available glasses model
            "models": ["HazzBerry"],  # available glasses model
            "materials": [
                {
                    "name": "Obsidian Black",  # tag name
                    "frame": {"color": "rgb(0,0,0)"},  # frame color
                    "glass": {"color": "rgb(255, 255, 255)", "opacity": 0.3}  # glass may have shader issue
                }
                #             {
                #                 "name": "Glamour Red",
                #                 "frame": { "color": "rgb(168, 32, 26)" },
                #                 "glass": { "color": "rgb(255, 255, 255)", "opacity": 0.3 }
                #             },
                #             {
                #                 "name": "Gold Potato",
                #                 "frame": { "color": "rgb(255, 242, 0)" },
                #                 "glass": { "color": "rgb(255, 255, 255)", "opacity": 0.3 }
                #             },
                #             {
                #                 "name": "Tornado Blue",
                #                 "frame": { "color": "rgb(66, 134, 244)" },
                #                 "glass": { "color": "rgb(255, 255, 255)", "opacity": 0.3 }
                #             },
                #             {
                #                 "name": "Lush Green",
                #                 "frame": { "color": "rgb(59, 173, 46)" },
                #                 "glass": { "color": "rgb(255, 255, 255)", "opacity": 0.3 }
                #             }
            ]
        },
        "poses": [
            {
                "yaw": [-30, 30, 30],  # it can be range (min, max, interval)
                #             "pitch": [-15, 15, 15],
                #             "yaw": 0,                     # it can be range (min, max, interval)
                "pitch": 0,
                #             "yaw": 0,
                #             "pitch": 0,
                "roll": 0  # or just a single value
            }
        ]
    }

    data = {
        "variants": json.dumps(payload),
        "email": "tomasfabry1@gmail.com",
    }

    r = requests.post(url, files=files, data=data)
    file.close()

    print(r)
