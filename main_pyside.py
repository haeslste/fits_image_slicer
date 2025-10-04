
import sys
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from ui.main_window import MainWindow
from controller import Controller
from project import Project
from ui.project_wizard import ProjectWizard
from ui.new_project_dialog import NewProjectDialog
from ui.add_files_dialog import AddFilesDialog
from ui.confirm_add_files_dialog import ConfirmAddFilesDialog

def main():
    app = QApplication(sys.argv)
    
    # Apply a stylesheet for better UX
    app.setStyleSheet("""
        QPushButton {
            padding: 8px 16px;
            font-size: 14px;
        }
        QMainWindow, QDialog {
            font-size: 14px;
        }
    """)

    wizard = ProjectWizard()
    if not wizard.exec():
        sys.exit(0)

    project = Project()

    if wizard.choice == "new":
        new_project_dialog = NewProjectDialog()
        if not new_project_dialog.exec():
            sys.exit(0)
        details = new_project_dialog.get_project_details()
        project.create(details["name"], details["directory"], details["files"])
    
    elif wizard.choice == "open":
        path, _ = QFileDialog.getOpenFileName(None, "Open Project", "", "Project Files (*.json)")
        if not path:
            sys.exit(0)
        project.load(path)

        new_files = project.scan_for_new_files()
        if new_files:
            confirm_dialog = ConfirmAddFilesDialog(new_files)
            if confirm_dialog.exec():
                project.add_files(new_files)

    if not project.files:
        reply = QMessageBox.question(None, "Empty Project", "This project has no files. Would you like to add some?")
        if reply == QMessageBox.Yes:
            add_files_dialog = AddFilesDialog()
            if add_files_dialog.exec():
                new_files = add_files_dialog.get_files()
                if new_files:
                    project.add_files(new_files)

    if not project.files:
        QMessageBox.information(None, "Empty Project", "No files in project. Exiting.")
        sys.exit(0)

    main_window = MainWindow()
    controller = Controller(main_window, project)
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
