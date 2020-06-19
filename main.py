#!/usr/bin/env python3
"""
Filename: Mainpy
License: GPL V3
Creator:ginobvhc
"""


import os
import subprocess
import sys
import yaml
import pexpect

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QStatusBar,
    QPushButton,
    QSystemTrayIcon,
    QWidget,
)

ICON = "Icon.png"
HOME = os.path.expanduser("~")
CONFIG_PATH = HOME + "/.config"
CONFIG_FILE = "crypsys.yaml"
CONFIG_ABS_FILE = CONFIG_PATH + "/" + CONFIG_FILE
CRYP_MOUNT_METHOD = "cryfs"
CRYP_UNMOUNT_METHOD = "cryfs-unmount"

DIRNAME = os.path.dirname(__file__)
ABSOLUTE_ICON_PATH = os.path.join(DIRNAME, ICON)
print(ABSOLUTE_ICON_PATH)


class LoadNewEnc(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self):
        title = "Load New Enc"
        self.setWindowTitle(title)
        win = QWidget()
        enc_name = QLabel("Load Encrypted Folder")
        enc_mount_name = QLabel("Mount Point")
        self.enc_name = QLineEdit()
        self.enc_mount_name = QLineEdit()
        self.bu_open_enc_name = QPushButton("Select Folder")
        self.bu_open_enc_mount_name = QPushButton("Select Folder")
        self.bu_save = QPushButton("Save")
        self.bu_save.clicked.connect(self.save_config)
        self.bu_open_enc_name.clicked.connect(self.chg_enc_name)
        self.bu_open_enc_mount_name.clicked.connect(self.chg_enc_mount_name)
        grid = QGridLayout()
        grid.addWidget(enc_name, 1, 0)
        grid.addWidget(self.enc_name, 1, 1)
        grid.addWidget(self.bu_open_enc_name, 1, 2)
        grid.addWidget(enc_mount_name, 2, 0)
        grid.addWidget(self.enc_mount_name, 2, 1)
        grid.addWidget(self.bu_open_enc_mount_name, 2, 2)
        grid.addWidget(self.bu_save, 3, 0)
        win.setLayout(grid)
        self.setCentralWidget(win)

    def chg_enc_name(self):
        self.enc_name.setText(select_dir())

    def chg_enc_mount_name(self):
        self.enc_mount_name.setText(select_dir())

    def save_config(self):
        config = load_config()
        enc_name_dir = self.enc_name.text()
        enc_mount_name_dir = self.enc_mount_name.text()
        name = enc_name_dir.split("/")[-1]
        config[name] = [enc_name_dir, enc_mount_name_dir]
        print(config)
        save_config(config)
        self.close()


class MountsWin(QMainWindow):
    def __init__(self, dict_encs, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        self.dict_encs = dict_encs
        self.initUI()

    def initUI(self):
        title = "Mounts"
        self.setWindowTitle(title)
        win = QWidget()
        self.statusBar().showMessage("Ready")
        enc_name = QLabel("Enc Name")
        self.enc_name = QComboBox()
        self.enc_name.addItems(self.dict_encs.keys())
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.bu_mount = QPushButton("Mount")
        self.bu_mount.clicked.connect(self.mount_enc)
        self.bu_unmount = QPushButton("UnMount")
        self.bu_unmount.clicked.connect(self.unmount_enc)
        grid = QGridLayout()
        grid.addWidget(enc_name, 1, 0)
        grid.addWidget(self.enc_name, 1, 1)
        grid.addWidget(self.password, 2, 0)
        grid.addWidget(self.bu_mount, 3, 0)
        grid.addWidget(self.bu_unmount, 3, 1)
        win.setLayout(grid)
        self.setCentralWidget(win)

    def mount_enc(self):
        print("trigger mount")
        key_enc_name = self.enc_name.currentText()
        enc_folder, mount_point = self.dict_encs[key_enc_name]
        command = f"{CRYP_MOUNT_METHOD} {enc_folder} {mount_point}"
        password = self.password.text()
        child = pexpect.spawn(command)
        child.expect("Password:")
        child.sendline(password)
        print(child.before)
        loading = child.expect("Deriving .*")
        error = child.expect("Error 11: .*")
        print(error)
        print(loading)
        if error == 0:
            print("Wrong password")
            self.statusBar().showMessage("Wrong Password")
        else:
            print("Password ok mounted")
            self.statusBar().showMessage("Mounted {key_enc_name}")
        print(command)

    def unmount_enc(self):
        print("trigger unmount")
        key_enc_name = self.enc_name.currentText()
        mount_point = self.dict_encs[key_enc_name][-1]
        command = f"{CRYP_UNMOUNT_METHOD} {mount_point}"
        child = pexpect.spawn(command)
        self.statusBar().showMessage(f"Unmounted {mount_point}")
        print(command)


class MainWin(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QMainWindow, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.new_enc_win = LoadNewEnc()
        self.config = load_config()
        self.keys = self.config.keys()
        print(self.keys)
        self.mounts = MountsWin(self.config)
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        # Create the icon
        icon = QIcon(ABSOLUTE_ICON_PATH)
        # Create the tray
        tray = QSystemTrayIcon()
        tray.setIcon(icon)
        tray.setVisible(True)
        # Create the menu
        menu = QMenu()
        action = QAction("New", self)
        menu.addAction(action)
        action.triggered.connect(self.show_new_enc_win)
        # Add enc Actions
        action = QAction("Select", self)
        menu.addAction(action)
        action.triggered.connect(self.show_mounts)
        # Add a Quit option to the menu.
        quit = QAction("Quit")
        quit.triggered.connect(app.quit)
        menu.addAction(quit)
        # Add the menu to the tray
        tray.setContextMenu(menu)
        app.exec_()

    def show_new_enc_win(self):
        self.new_enc_win.show()

    def show_mounts(self):
        self.mounts.show()


def save_yaml(filename, data):
    with open(filename, "w") as fileyaml:
        data = yaml.dump(data, fileyaml)


def save_config(date):
    save_yaml(CONFIG_ABS_FILE, date)


def load_yaml(filename):
    with open(filename) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data


def load_config():
    if os.path.exists(CONFIG_ABS_FILE):
        data = load_yaml(CONFIG_ABS_FILE)
    else:
        data = dict()
    return data


def select_dir():
    # filt = "Json(*.json)"
    file = str(QFileDialog.getExistingDirectory(None, "Select Directory"))
    # filename, _ = QFileDialog.getOpenFileName(None, "Select JSON", PATH, filt)
    # return filename
    return file


def mount(enc_dires, mount_dir):
    subprocess()


def main():
    app = QApplication(sys.argv)
    ex = MainWin()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
