import argparse
import zipfile
import time
import shutil
import ntpath
import numpy as np
import cv2
import os

def split_image(image_path, output_path, num_splits, labels=None):
    img = cv2.imread(image_path)
    head, tail = os.path.split(image_path)

    (height, width, depth) = img.shape
    width_split = int(width / num_splits)
    print(img.shape, img.dtype)

    for i in range(num_splits):
        img_split = img[:, i * width_split: (i + 1) * width_split, :]
        if not labels:
            filename = str(tail.split('.')[0]) + str(i) + '.jpg'
        else:
            filename = str(tail.split('.')[0]) + '_' + labels[i] + '.jpg'

        cv2.imwrite(os.path.join(output_path, filename), img_split)


# stargan running script:
"""
python main.py --mode test --dataset CelebA --image_size 256 --c_dim 5 \
                 --selected_attrs Wearing_Hat Wearing_Lipstick Wearing_Necklace Wearing_Necktie Pointy_Nose \
                 --model_save_dir='stargan_celeba_256/models' \
                 --result_dir='stargan_celeba_256/results'

"""
