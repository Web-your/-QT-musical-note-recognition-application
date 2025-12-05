import io
import sqlite3
import sys
from PyQt6 import uic, QtCore, QtWidgets # Импортируем uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QWidget, QFileDialog, QDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QAbstractItemView
from PyQt6.QtCore import QDir
from ScanLib import scan_note
from TransNote import MidiNote, MidiMp3, MidiWav
import tempfile
import csv
import os

def render_note(coordinates):
    s_res = ""
    for item in coordinates:
        x, y, w, h = item
        s_res += (f'\n<a class="box" style="left: {x}px; top: {y}px; width: {w}px; height: {h}px;'
                  f' background-color: red; z-index: 1;"></a>')
    return s_res


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Ui_PyQTapp.ui", self)
        self.setWindowIcon(QIcon("MyNotesOpen.svg"))
        self.name_project = "Untitled"
        self.setWindowTitle(f"MyNotesOpen - {self.name_project}")

        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        req = "SELECT * FROM projects"
        self.actionNew = []
        self.adressHolder = []
        n = cur.execute(req).fetchall()
        for i in range(len(n)):
            id, key, value = n[i]
            self.actionNew.append(QAction(key, self))
            self.adressHolder.append(value)
            self.actionNew[i].setStatusTip(value)
            self.menuOpen.addAction(self.actionNew[i])
            def make_handler(index):
                return lambda: self.pr_trig(index)
            self.actionNew[i].triggered.connect(make_handler(i))

        self.comboBox.addItem("classic")
        self.comboBox.addItem("clipping")
        self.algo_dict = {}
        cur = self.con.cursor()
        req = "SELECT * FROM algorithms"
        n = cur.execute(req).fetchall()
        for id, name, *info in n:
            self.algo_dict[name] = info
            self.comboBox.addItem(name)

        self.buttonDetected.setEnabled(False)
        self.buttonOriginal.setEnabled(False)
        self.buttonDetect.clicked.connect(self.detect)
        self.buttonOriginal.clicked.connect(self.img_orig)
        self.buttonDetected.clicked.connect(self.img_detect)
        self.actionDetected_options.triggered.connect(self.options_trig_detect)
        self.actionFile_save_options.triggered.connect(self.options_trig)
        self.actionOther.triggered.connect(self.options_trig)
        self.actionImage.triggered.connect(self.open_image)
        self.actionSave_as.triggered.connect(self.save_as_pr)
        self.actionSave.triggered.connect(self.save_pr)
        self.actionImport_in.triggered.connect(self.import_pr)
        self.options_window = None
        self.import_in_window = None
        self.notes = []
        self.file_location = None

    def detect(self):
        try:
            self.buttonOriginal.setEnabled(True)
            if self.comboBox.currentText() in self.algo_dict.keys():
                item = self.algo_dict[self.comboBox.currentText()]
                p = scan_note(self.lineFileOpen.text(), self.comboBox.currentText(),
                              item[3], binar=item[0], blur_s=item[1], axis=item[2])
            else:
                p = scan_note(self.lineFileOpen.text(), self.comboBox.currentText(), 5)
            self.notes = p
            html_content = f"""
                        <html>
                          <head></head>
                          <body>
                            <img src="{self.lineFileOpen.text()}" style="height: 100%; width: auto; z-index: 0;">
                          </body>
                        </html>
                        """
            self.textBrowser.setHtml(html_content)
        except Exception:
            self.statusbar.showMessage("!Error openfile")


    def img_orig(self):
        self.buttonDetected.setEnabled(True)
        self.buttonOriginal.setEnabled(False)

    def img_detect(self):
        self.buttonOriginal.setEnabled(True)
        self.buttonDetected.setEnabled(False)

    def open_image(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '',
            'Картинка (*.jpg);;Картинка (*.png);;Все файлы (*)')[0]
        self.image_paths = fname
        self.lineFileOpen.setText(fname)

    def pr_trig(self, num):
        self.buttonOriginal.setEnabled(True)
        self.name_project = self.sender().text()
        self.file_location
        self.setWindowTitle(f"MyNotesOpen - {self.name_project}")
        try:
            with open(self.adressHolder[num], "r", encoding="utf8") as file:
                reader = csv.reader(file)
                rows = []
                for row in reader:
                    rows.append(row)
                self.lineFileOpen.setText(str(rows[0][0]))
                self.file_location = rows[0][0]
                html_content = f"""
                            <html>
                              <head></head>
                              <body>
                                <img src="{rows[0][0]}" style="height: 100%; width: auto; z-index: 0;">
                              </body>
                            </html>
                            """
                notes_d = {}
                notes = []
                for i in range(1, len(rows)):
                    key = int(rows[i][0])
                    value = rows[i][1]
                    numbers = list(map(int, rows[i][2:]))
                    if key in notes_d:
                        notes_d[key].append((value, numbers))
                    else:
                        notes_d[key] = [(value, numbers)]
                for _, item in notes_d.items():
                    notes.append(item)
                self.notes = notes
                self.textBrowser.setHtml(html_content)
        except Exception:
            self.statusbar.showMessage("!Error openfile. The file has been moved")



    def save_as_pr(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл",
            self.name_project,  # Начальная директория
            "Текстовые файлы (*.csv);;Все файлы (*)"
        )
        self.file_location = file_path
        if self.file_location:
            self.name_project = os.path.basename(file_path)
            self.con = sqlite3.connect(r"Open_projects.db")
            self.con.execute(
                f"INSERT INTO projects ( name, location) VALUES ( '{self.name_project}', '{self.file_location}')")
            self.con.commit()
        if self.notes and self.file_location:
            with open(self.file_location, "w", encoding="utf8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([self.image_paths])
                data = []
                for i in range(len(self.notes)):
                    for j in range(len(self.notes[i])):
                        s = [i, self.notes[i][j][0], self.notes[i][j][1][0],
                             self.notes[i][j][1][1], self.notes[i][j][1][2], self.notes[i][j][1][3]]
                        data.append(s)
                writer.writerows(data)
            self.save = True

    def save_pr(self):
        if (not self.file_location):
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Сохранить файл",
                self.name_project,  # Начальная директория
                "Текстовые файлы (*.csv);;Все файлы (*)"
            )
            self.file_location = file_path
            if self.file_location:
                self.name_project = os.path.basename(file_path)
                self.con = sqlite3.connect(r"Open_projects.db")
                self.con.execute(
                    f"INSERT INTO projects ( name, location) VALUES ( '{self.name_project}', '{self.file_location}')")
                self.con.commit()
        if self.notes and self.file_location:
            with open(self.file_location, "w", encoding="utf8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([self.image_paths])
                data = []
                for i in range(len(self.notes)):
                    for j in range(len(self.notes[i])):
                        s = [i, self.notes[i][j][0], self.notes[i][j][1][0],
                             self.notes[i][j][1][1], self.notes[i][j][1][2], self.notes[i][j][1][3]]
                        data.append(s)
                writer.writerows(data)
            self.save = True

    def options_trig_detect(self):
        self.options_window = WidgetOptions(1)
        self.options_window.show()
        self.options_window.activateWindow()

    def options_trig(self):
        self.options_window = WidgetOptions(2)
        self.options_window.show()
        self.options_window.activateWindow()

    def import_pr(self):
        if self.notes:
            if self.import_in_window is None:
                self.import_in_window = WidgetImport(self.notes, self.name_project)

            self.import_in_window.show()
            self.import_in_window.activateWindow()
        else:
            self.statusbar.showMessage("!There is no open file or uploaded notes")



class WidgetOptions(QMainWindow):
    def __init__(self, sr):
        super().__init__()
        if sr == 1:
            uic.loadUi("Ui_optionsDetect.ui", self)
            self.setWindowIcon(QIcon("MyNotesOpen.svg"))
            self.horizontalSlider.setValue(100)
            self.horizontalSlider_2.setValue(3)
            self.horizontalSlider_3.setValue(5)
            self.comboBox.addItem("xys")
            self.comboBox.addItem("ys")
            self.comboBox.addItem("xs")
            self.comboBox.addItem("xy")
            self.comboBox.addItem("y")
            self.comboBox.addItem("x")
            self.pushButton.clicked.connect(self.butt_save_preset)
        else:
            uic.loadUi("Ui_options.ui", self)
            self.setWindowIcon(QIcon("MyNotesOpen.svg"))
            self.con = sqlite3.connect(r"Open_projects.db")
            cur = self.con.cursor()
            req = "SELECT * FROM projects"
            n = cur.execute(req).fetchall()
            self.tableWidget.setColumnCount(2)
            self.tableWidget.setRowCount(len(n))
            self.tableWidget.setHorizontalHeaderLabels(["Name", "File path"])
            for row_idx, row_data in enumerate(n):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.tableWidget.setItem(row_idx , col_idx - 1, item)
            self.tableWidget.resizeColumnsToContents()
            cur = self.con.cursor()
            req = "SELECT * FROM algorithms"
            n = cur.execute(req).fetchall()
            self.tableWidget_2.setColumnCount(5)
            self.tableWidget_2.setRowCount(len(n))
            self.tableWidget_2.setHorizontalHeaderLabels(["Name", "Binarization", "Blur", "Axis", "Algorithm depth size"])
            for row_idx, row_data in enumerate(n):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.tableWidget_2.setItem(row_idx, col_idx - 1, item)
            self.tableWidget_2.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.tableWidget_2.resizeColumnsToContents()
            self.pushButton_4.clicked.connect(self.delete_selected_row)
            self.pushButton_3.clicked.connect(self.delete_selected_row1)
            self.pushButton.clicked.connect(self.search_tb)
            self.pushButton_2.clicked.connect(self.search_tb1)
            self.pushButton_5.clicked.connect(self.save_info_in_db)

    def delete_selected_row(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()
        for index in sorted(selected_rows, reverse=True):
            self.tableWidget.removeRow(index.row())

    def delete_selected_row1(self):
        selected_rows = self.tableWidget_2.selectionModel().selectedRows()
        for index in sorted(selected_rows, reverse=True):
            self.tableWidget_2.removeRow(index.row())

    def search_tb(self):
        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        req = f"SELECT * FROM projects WHERE name LIKE '%{self.lineEdit.text()}%'"
        n = cur.execute(req).fetchall()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(n))
        self.tableWidget.setHorizontalHeaderLabels(["Name", "File path"])
        for row_idx, row_data in enumerate(n):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.tableWidget.setItem(row_idx, col_idx - 1, item)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.viewport().update()

    def search_tb1(self):
        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        req = f"SELECT * FROM algorithms WHERE name LIKE '%{self.lineEdit_2.text()}%'"
        n = cur.execute(req).fetchall()
        self.tableWidget_2.setColumnCount(5)
        self.tableWidget_2.setRowCounёt(len(n))
        self.tableWidget_2.setHorizontalHeaderLabels(["Name", "Binarization", "Blur", "Axis", "Algorithm depth size"])
        for row_idx, row_data in enumerate(n):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.tableWidget_2.setItem(row_idx, col_idx - 1, item)
        self.tableWidget_2.resizeColumnsToContents()
        self.tableWidget_2.viewport().update()

    def save_info_in_db(self):
        data = []
        for row in range(self.tableWidget.rowCount()):
            row_data = []
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")  # или None
            data.append(row_data)
        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        cur.execute(f"DELETE FROM projects")
        for item in data:
            self.con.execute(
                f"INSERT INTO projects ( name, location) VALUES ( '{item[0]}', '{item[1]}')")
        self.con.commit()

        data = []
        for row in range(self.tableWidget_2.rowCount()):
            row_data = []
            for col in range(self.tableWidget_2.columnCount()):
                item = self.tableWidget_2.item(row, col)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append("")  # или None
            data.append(row_data)
        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        cur.execute(f"DELETE FROM algorithms")
        for item in data:
            self.con.execute(
                f"INSERT INTO algorithms ( name, binar, blur, axis, size) VALUES ( '{item[0]}', {item[1]}, {item[2]}, '{item[3]}', {item[4]})")
        self.con.commit()
        self.statusbar.showMessage("The data is saved")

    def butt_save_preset(self):
        name_inp = self.lineEdit.text()
        binar = self.horizontalSlider.value()
        blur = self.horizontalSlider_2.value()
        size = self.horizontalSlider_3.value()
        axis = self.comboBox.currentText()
        if name_inp == "":
            self.statusbar.showMessage("!Empty name field")
        self.con = sqlite3.connect(r"Open_projects.db")
        cur = self.con.cursor()
        req = "SELECT * FROM algorithms"
        n = cur.execute(req).fetchall()
        for id, name, *_ in n:
            if name == name_inp:
                self.statusbar.showMessage("!Empty name field")
                return
        self.con.execute(
            f"INSERT INTO algorithms ( name, binar, blur, axis, size) VALUES ( '{name_inp}', {binar}, {blur}, '{axis}', {size})")
        self.con.commit()
        self.statusbar.showMessage(f"Preset {name_inp} saved, reopen app")


class WidgetImport(QDialog):
    def __init__(self, notes, name_project):
        super().__init__()
        uic.loadUi("Ui_import.ui", self)
        self.setWindowIcon(QIcon("MyNotesOpen.svg"))
        self.comboBox.addItem("Wav")
        self.comboBox.addItem("Mp3")
        self.comboBox.addItem("Midi")
        self.comboBox_2.addItem("Desktop")
        self.comboBox_2.addItem("Your")
        self.pushButton.clicked.connect(self.button_safe)
        self.pushButton_2.clicked.connect(self.button_inst)
        self.pushButton_3.clicked.connect(self.render)
        self.lineEdit_3.setText(f"{name_project}_audio")
        self.notes = notes

    def button_safe(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для сохранения",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        self.lineEdit.setText(folder)

    def button_inst(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Выбрать звуковой пресет', '',
            'Sound font (*.sf2);;Все файлы (*)')[0]
        self.lineEdit_2.setText(fname)

    def render(self):
        inp1 = []
        notes_coordinates = []
        for i in self.notes:
            for j in i:
                inp1.append(j[0])
                notes_coordinates.append(j[1])
        print(inp1, len(inp1))
        try:
            if self.comboBox.currentText() == "Midi":
                midi_file_path = f"{self.lineEdit.text()}/" + self.lineEdit_3.text() + ".mid"
                MidiNote(inp1, midi_file_path)
            elif self.comboBox.currentText() == "Wav":
                temp_dir = tempfile.gettempdir()
                midi_path = os.path.join(temp_dir, "sistem.mid")
                print(midi_path)
                MidiNote(inp1, midi_path)
                wave_file_path = f"{self.lineEdit.text()}/" + self.lineEdit_3.text() + ".wav"
                MidiWav(midi_path, wav_file_path=wave_file_path)
                os.remove(midi_path)
            elif self.comboBox.currentText() == "Mp3":
                temp_dir = tempfile.gettempdir()
                midi_path = os.path.join(temp_dir, "sistem.mid")
                wav_path = os.path.join(temp_dir, "sistem.wav")
                print(midi_path)
                MidiNote(inp1, midi_path)
                wave_file_path = f"{self.lineEdit.text()}/" + self.lineEdit_3.text() + ".mp3"
                if self.comboBox_2.currentText() == "Desktop":
                    MidiMp3(midi_path, mp3_file_path=wave_file_path, wav_path=wav_path)
                elif self.comboBox_2.currentText() == "Your":
                    MidiMp3(midi_path, mp3_file_path=wave_file_path, wav_path=wav_path,
                            soundfont_path=self.lineEdit_2.text())
                os.remove(midi_path)
                os.remove(wav_path)
        except Exception:
            ...



def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    sys.excepthook = except_hook
    ex = MainApp()
    ex.show()
    sys.exit(app.exec())