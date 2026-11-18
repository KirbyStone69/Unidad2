import sys
from PyQt6.QtWidgets import QApplication
from laboratorio.window import MainWindow

def main():
    app=QApplication(sys.argv)
    app.setApplicationName('ARBOL Genetic Lab')
    window=MainWindow(); window.show()
    sys.exit(app.exec())

if __name__=='__main__': main()
