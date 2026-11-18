"""Identificación de ejecuciones y PDF de capturas con ReportLab."""
import hashlib
import json
import shutil
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor

ALGORITMOS = ('dijkstra', 'bellman_ford', 'warshall_floyd', 'a_estrella')
RAIZ_INFORMES = Path(__file__).resolve().parents[1] / 'informes'


def crear_carpetas(raiz=RAIZ_INFORMES):
    for algoritmo in ALGORITMOS:
        (Path(raiz) / algoritmo).mkdir(parents=True, exist_ok=True)


def clave_informe(algoritmo, grafo, parametros):
    datos = {'version': 1, 'algoritmo': algoritmo, 'dirigido': grafo.is_directed(),
             'nodos': sorted((repr(n), repr(d.get('valor')), repr(d.get('pixel')))
                             for n, d in grafo.nodes(data=True)),
             'aristas': sorted((repr(u), repr(v), repr(k), repr(d['weight']))
                               for u, v, k, d in grafo.edges(keys=True, data=True)),
             'parametros': sorted((k, repr(v)) for k, v in parametros.items())}
    return hashlib.sha256(json.dumps(datos, sort_keys=True).encode()).hexdigest()[:20]


def pdf_completo(ruta):
    try:
        with Path(ruta).open('rb') as archivo:
            if archivo.read(5) != b'%PDF-':
                return False
            archivo.seek(max(0, Path(ruta).stat().st_size - 1024))
            return archivo.read().rstrip().endswith(b'%%EOF')
    except OSError:
        return False


class EscritorPDF:
    """Canvas acotado por bloques; qpdf lee imágenes desde disco al unir."""
    PAGINAS_BLOQUE = 64

    def __init__(self, destino, titulo):
        self.destino = Path(destino)
        self.temporal = self.destino.with_suffix('.tmp.pdf')
        self.bloques_dir = self.destino.with_suffix('.bloques')
        self.bloques_dir.mkdir(parents=True, exist_ok=True)
        self.bloques = []
        self.canvas = None
        self.paginas_bloque = 0
        self.titulo = titulo

    def _abrir_bloque(self):
        ruta = self.bloques_dir / f'bloque_{len(self.bloques):06d}.pdf'
        self.bloques.append(ruta)
        self.canvas = Canvas(str(ruta), pagesize=(1000, 720), pageCompression=1)
        self.canvas.setTitle(self.titulo)
        self.canvas.setAuthor('Visualizador de rutas')
        self.paginas_bloque = 0

    def _cerrar_bloque(self):
        if self.canvas is not None:
            self.canvas.save()
            self.canvas = None
            self.paginas_bloque = 0

    def agregar(self, captura, numero, total):
        if self.canvas is None:
            self._abrir_bloque()
        c = self.canvas
        c.setFillColor(HexColor('#1e2421'))
        c.rect(0, 0, 1000, 720, fill=1, stroke=0)
        c.setFillColor(HexColor('#69ff99'))
        c.setFont('Helvetica', 12)
        c.drawString(18, 696, self.titulo)
        c.drawRightString(982, 696, f'Paso {numero} / {total}')
        c.drawImage(str(captura), 12, 28, width=976, height=650,
                    preserveAspectRatio=True, anchor='c')
        c.showPage()
        self.paginas_bloque += 1
        if self.paginas_bloque >= self.PAGINAS_BLOQUE:
            self._cerrar_bloque()

    def finalizar(self):
        self._cerrar_bloque()
        if len(self.bloques) == 1:
            self.bloques[0].replace(self.temporal)
        elif self.bloques:
            from pikepdf import Job, PikepdfError
            # QPDF conserva referencias a los streams del archivo de entrada,
            # sin cargar los bytes de todas las imágenes en objetos Python.
            argumentos = ['pikepdf', str(self.bloques[0]), '--keep-files-open=n',
                          '--object-streams=disable', '--pages']
            argumentos.extend(str(bloque) for bloque in self.bloques)
            argumentos.extend(['--', str(self.temporal)])
            try:
                Job(argumentos).run()
            except PikepdfError as error:
                raise RuntimeError(f'No se pudieron unir los bloques: {error}') from error
        else:
            raise ValueError('El informe no contiene capturas.')
        self.temporal.replace(self.destino)
        shutil.rmtree(self.bloques_dir)

    def cancelar(self):
        self.canvas = None
        self.temporal.unlink(missing_ok=True)
        shutil.rmtree(self.bloques_dir, ignore_errors=True)
