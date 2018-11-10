import argparse
import zipfile
import time
import shutil
import ntpath
import numpy as np
import cv2
import os



def reduce_dataset(input_folder, output_folder, num_images):
    # folders = os.listdir(input_folder)
    replicate_folder_structure(input_folder, output_folder)

    folders = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]

    for folder in folders:
        print(folder)
        folder_path = os.path.join(input_folder, folder)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        selected_files = files[:num_images]

        for file in selected_files:
            shutil.copy2(os.path.join(input_folder, folder, file), os.path.join(output_folder, folder))


def replicate_folder_structure(input_folder, output_folder):
    print("Replicating folder structure...")

    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    for dirpath, dirnames, filenames in os.walk(input_folder):
        for dir in dirnames:
            path = os.path.join(output_folder, dir)
            if not os.path.isdir(path):
                os.mkdir(path)
            else:
                print("Folder already exists, skipping...")
