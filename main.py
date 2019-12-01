import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap
import numpy as np
import csv
import pandas as pd
import shutil

# ======================================================================

# folder with images we want to label (don't forget "/" at the end)
input_folder = './data/images1/'

# labels we want to use
labels = ["label1", "label2", "label3", "label4"]

# select one of the following modes: copy, move, none
# 1. copy: Creates folder for each label. Labeled images are copied to these folders
# 2. move: Creates folder for each label. Labeled images are moved to these folders
# 3. none: Images in input_folder are just labeled and then csv file with assigned labels is generated
mode = 'move'  # 'copy', 'move', 'none'

# output csv file
output_file = 'output.csv'

# allowed file extensions
file_extensions = ('.jpg', '.png', '.jpeg')


# ======================================================================
def get_img_paths(dir, extensions=''):
    '''
    :param dir: folder with files
    :param extensions: tuple with file endings. e.g. ('.jpg', '.png')
    :return: list of all filenames
    '''

    img_paths = []

    for filename in os.listdir(dir):
        if filename.lower().endswith(extensions):
            img_paths.append(dir + filename)

    return img_paths


def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


class App(QWidget):
    def __init__(self, labels, img_paths):
        super().__init__()

        # init UI state
        self.title = 'PyQt5 - Annotation tool'
        self.left = 200
        self.top = 200
        self.width = 1000
        self.height = 600

        # state variables
        self.counter = 0
        self.img_paths = img_paths
        self.labels = labels
        self.num_labels = len(labels)
        self.num_images = len(img_paths)

        self.label_buttons = []
        self.appended_labels = {}

        # Initialize image variables
        self.image_box = QLabel(self)
        self.img_name_label = QLabel(self)
        self.img_name_label.setGeometry(20, 0, 300, 20)

        self.progress_bar = QLabel(self)
        self.progress_bar.setGeometry(20, 20, 100, 20)

        # init UI
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.initButtons()

        # show image
        self.set_image(self.img_paths[0])
        self.image_box.move(20, 50)

        # image name
        self.img_name_label.setText(img_paths[self.counter])

        # progress bar
        self.progress_bar.setText(f'1 of {self.num_images}')

        # apply styles
        sshFile = "./styles/button.qss"
        with open(sshFile, "r") as fh:
            self.setStyleSheet(fh.read())

    def initButtons(self):

        # Add "Prev Image" and "Next Image" buttons
        prev_im_btn = QtWidgets.QPushButton(self)
        prev_im_btn.setText("Prev")
        prev_im_btn.move(self.width - 190, 80)
        prev_im_btn.clicked.connect(self.show_prev_image)
        prev_im_btn.setObjectName("setImageButton")

        next_im_btn = QtWidgets.QPushButton(self)
        next_im_btn.setText("Next")
        next_im_btn.move(self.width - 100, 80)
        next_im_btn.clicked.connect(self.show_next_image)
        next_im_btn.setObjectName("setImageButton")

        # Add "generate csv file" button
        next_im_btn = QtWidgets.QPushButton(self)
        next_im_btn.setText("Generate csv")
        next_im_btn.move(self.width - 190, 20)
        next_im_btn.clicked.connect(self.generate_csv)
        next_im_btn.setObjectName("generateCsvButton")

        # Create label button
        for i, label in enumerate(self.labels):
            self.label_buttons.append(QtWidgets.QPushButton(self))
            button = self.label_buttons[i]
            button.setText(label)
            # 80 is button width, 10 is spacing between buttons
            # button.move((80 + 10) * i + 300, 20)
            button.move(self.width - 190, (45 + 10) * i + 150)

            # https://stackoverflow.com/questions/35819538/using-lambda-expression-to-connect-slots-in-pyqt
            button.clicked.connect(lambda state, x=label: self.set_label(x))

    def set_label(self, label):
        # get image filename from path (./data/images/img1.jpg → img1.jpg)
        filename = os.path.split(self.img_paths[self.counter])[-1]

        # set new label
        self.appended_labels[filename] = label

        # copy/move the image into appropriate label folder
        if mode == 'copy':
            self._copy_image(label, self.img_paths[self.counter])
        elif mode == 'move':
            self._move_image(label, self.img_paths[self.counter])

        # load next image
        self.show_next_image()

    def show_next_image(self):

        if self.counter < self.num_images - 1:
            self.counter += 1

            path = self.img_paths[self.counter]

            self.set_image(path)
            self.img_name_label.setText(path)
            self.progress_bar.setText(f'{self.counter + 1} of {self.num_images}')
        # else:
        #     # not sure if to close app by itself when all images are labeled. Probably not, it's confusing.
        #     QCoreApplication.quit()

    def show_prev_image(self):
        if self.counter > 0:
            self.counter -= 1

            if self.counter < self.num_images:
                path = self.img_paths[self.counter]

                self.set_image(path)
                self.img_name_label.setText(path)
                self.progress_bar.setText(f'{self.counter + 1} of {self.num_images}')

            # else:
            #     QCoreApplication.quit()

    def set_image(self, path):
        pixmap = QPixmap(path).scaled(700, 700, Qt.KeepAspectRatio, Qt.FastTransformation)
        self.image_box.setPixmap(pixmap)

    def generate_csv(self):
        filename = 'output.csv'

        with open(filename, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            # write header
            writer.writerow(['img'] + self.labels)

            # write one-hot labels
            for img_name, label in self.appended_labels.items():
                label_one_hot = self.__number_to_one_hot(self.labels.index(label), self.num_labels)
                writer.writerow([img_name] + list(label_one_hot))

    @staticmethod
    def __number_to_one_hot(number, num_classes):
        one_hot_arr = np.zeros([num_classes], dtype=int)
        one_hot_arr[number] = 1
        return one_hot_arr

    @staticmethod
    def _copy_image(label, file_path):
        """
        Copies a file to a new label folder using the shutil library. The file will be copied into a
        subdirectory called label in the input folder.
        :param label: The label
        :param file_path: Path of the original image
        """

        path_and_name = os.path.split(file_path)
        img_filename = path_and_name[-1]
        folder_path = path_and_name[0]

        output_path = os.path.join(folder_path, label, img_filename)
        shutil.copy(file_path, output_path)

    @staticmethod
    def _move_image(label, file_path):
        """
        Moves a file to a new label folder using the shutil library. The file will be moved into a
        subdirectory called label in the input folder.
        :param label: The label
        :param file_path: Path of the original image
        """

        path_and_name = os.path.split(file_path)
        img_filename = path_and_name[-1]
        folder_path = path_and_name[0]

        output_path = os.path.join(folder_path, label, img_filename)
        shutil.move(file_path, output_path)


if __name__ == '__main__':
    # get paths to images in input_folder
    img_paths = get_img_paths(input_folder, file_extensions)

    # create folders for each label if 'copy' or 'move' modes are selected
    if mode == 'copy' or 'move':
        for label in labels:
            make_folder(os.path.join(input_folder, label))

    app = QApplication(sys.argv)
    ex = App(labels, img_paths)
    ex.show()
    sys.exit(app.exec_())
