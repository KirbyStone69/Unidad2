"""Grabación incremental: renderiza TODOS los eventos en el hilo de Qt."""
import shutil
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from exportacion.informes import (
    RAIZ_INFORMES, EscritorPDF, clave_informe, crear_carpetas, pdf_completo,
)


class GrabadorInforme(QObject):
    cambiado = pyqtSignal(str, int, int)

    def __init__(self, interfaz, raiz=RAIZ_INFORMES):
        super().__init__(interfaz)
        self.interfaz = interfaz
        self.raiz = Path(raiz)
        crear_carpetas(self.raiz)
        self.habilitado = True
        self.activo = False
        self.estado = 'Capturas automáticas listas'
        self.indice = 0
        self.escritor = None
        self.renderizando = False
        interfaz.reproductor.paso_cambiado.connect(self.navegacion_manual)
        interfaz.reproductor.reproduciendo.connect(self.reproduccion_manual)
        self.ruta_pdf = None
        self.temporal_pdf = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.avanzar)

    def navegacion_manual(self, *_):
        if self.activo and not self.renderizando:
            self.cancelar()

    def reproduccion_manual(self, activo):
        if activo and self.activo:
            self.cancelar()

    def informar(self, texto, actual=0, total=0):
        self.estado = texto
        self.cambiado.emit(texto, actual, total)
        self.interfaz.mensaje.emit(texto)

    def preparar(self, grafo, parametros):
        self.cancelar()
        if not self.habilitado:
            return False
        algoritmo = self.interfaz.algoritmo.identificador
        clave = clave_informe(algoritmo, grafo, parametros)
        variante = 'negativo' if any(d['weight'] < 0 for *_, d in grafo.edges(data=True)) else 'positivo'
        carpeta = self.raiz / algoritmo
        nombre = f'{variante}_{clave}'
        self.ruta_pdf = carpeta / f'{nombre}.pdf'
        self.temporal_pdf = self.ruta_pdf.with_suffix('.tmp.pdf')
        self.carpeta_capturas = carpeta / nombre / 'pasos'
        if pdf_completo(self.ruta_pdf):
            self.informar(f'PDF existente: {self.ruta_pdf.name}. Se omite la búsqueda.')
            return True
        return False

    def iniciar(self, resultado):
        if not self.habilitado:
            return False
        try:
            # Solo reemplaza capturas parciales de esta misma ejecución.
            if self.carpeta_capturas.exists():
                shutil.rmtree(self.carpeta_capturas)
            self.carpeta_capturas.mkdir(parents=True)
            self.escritor = EscritorPDF(self.ruta_pdf, self.interfaz.algoritmo.nombre)
        except OSError as error:
            self.informar(f'No se pudo iniciar el informe: {error}')
            return False
        self.resultado = resultado
        self.indice = 0
        self.activo = True
        self.interfaz.reproductor.pausar()
        self.informar('Grabando todos los pasos…', 0, len(resultado.pasos))
        if hasattr(self.interfaz, 'matrices'):
            matrices = self.interfaz.matrices
            matrices.boton.setChecked(True)
            matrices.animacion.stop()
            matrices.contenido.setMaximumHeight(300)
        self.timer.start(0)
        return True

    def avanzar(self):
        if not self.activo:
            return
        v = self.interfaz
        try:
            self.renderizando = True
            v.reproductor.mostrar(self.indice)
            self.renderizando = False
            # Captura el centro de la animación, con partícula y cruz iluminadas.
            v.reproductor.progreso.emit(0.5)
            imagen = v.grab()
            ruta = self.carpeta_capturas / f'paso_{self.indice + 1:06d}.jpg'
            if not imagen.save(str(ruta), 'JPEG', 85):
                raise OSError('No se pudo guardar la captura.')
            total = len(self.resultado.pasos)
            self.escritor.agregar(ruta, self.indice + 1, total)
            self.indice += 1
            self.informar(f'Capturas: {self.indice}/{total}', self.indice, total)
            if self.indice == total:
                self.timer.stop()
                self.informar('Uniendo bloques del PDF…', total, total)
                self.escritor.finalizar()
                self.escritor = None
                self.activo = False
                self.informar(f'PDF guardado: {self.ruta_pdf.name}', total, total)
            else:
                # El PDF no espera la velocidad de reproducción: procesa el
                # siguiente paso en cuanto Qt atienda los eventos pendientes.
                self.timer.setInterval(0)
        except (OSError, ValueError, RuntimeError) as error:
            self.renderizando = False
            self.cancelar()
            self.informar(f'Error al crear informe: {error}')

    def cancelar(self):
        self.timer.stop()
        if self.escritor is not None:
            self.escritor.cancelar()
            self.escritor = None
        if self.activo:
            self.activo = False
            self.informar('Grabación cancelada. No se publicó un PDF incompleto.')
