"""Contrato mínimo: cada algoritmo decide cómo configurar y visualizar su búsqueda."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget


class InterfazAlgoritmo(QWidget):
    mensaje = pyqtSignal(str)
    informe = None

    def reutilizar_informe(self, parametros):
        return bool(self.informe and self.informe.preparar(self.grafo, parametros))

    def grabar_informe(self, resultado):
        return bool(self.informe and self.informe.iniciar(resultado))

    def cancelar_informe(self):
        if self.informe:
            self.informe.cancelar()

    def cargar_grafo(self, grafo):
        """Recibe el grafo seleccionado. Cada interfaz decide cómo representarlo."""
        raise NotImplementedError

    def detener(self):
        """Cancela sus animaciones al salir de la pestaña o cerrar la aplicación."""
        raise NotImplementedError
