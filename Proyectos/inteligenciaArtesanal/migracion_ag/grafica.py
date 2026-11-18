import time
import sys
import numpy as np
import matplotlib.pyplot as plt
import compatibilidad as cpp
import maximizacion
import minimizacion


# Solo se limita lo dibujado; el TXT conserva todas las muestras reales únicas.
LIMITE_PUNTOS = 10000


class GraficaEnVivo:
    def __init__(self, args, minimizar=False):
        self.minimizar = minimizar
        self.nombre = 'minimización' if minimizar else 'maximización'
        self.inicio = time.perf_counter()
        self.ultimo_refresco = -float('inf')
        self._ultimo_evento = -float('inf')
        self._intervalo = 0.05
        self.historial = []
        self.total = args.num_gen
        self.muestras = {}
        self.x = np.array([])
        self.y = np.array([])
        self._version = 0
        self._version_datos = -1
        self._minimo = self._maximo = None
        self._limites_y = None
        self._fondo = None
        self._cerrada = False
        self._finalizada = False
        self.refrescos = 0

        # Evitar que cada setter programe un dibujo automático adicional.
        # La aplicación controla explícitamente cuándo atender y dibujar la GUI.
        plt.ioff()
        self.figura, self.curva = plt.subplots(figsize=(10, 5))
        self.interactiva = self.figura.canvas.required_interactive_framework is not None
        self._usar_blit = bool(self.interactiva and self.figura.canvas.supports_blit)
        self.evaluados = self.curva.scatter([], [], color='royalblue', s=9, alpha=0.35,
                                           label='Evaluaciones acumuladas (puntos únicos)')
        self.curva.set_xlim(args.x_min, args.x_max)
        self.puntos = self.curva.scatter([], [], color='dimgray', s=25, alpha=0.7,
                                        label='Población actual', zorder=3)
        self.marcador = self.curva.scatter([], [], color='red', s=60, zorder=4,
                                          label='Mejor individuo actual')
        self.curva.set_xlabel('x (fenotipo)')
        self.curva.set_ylabel('f(x)')
        self.leyenda = self.curva.legend(loc='upper center', bbox_to_anchor=(0.5, -0.20),
                                         ncol=3, fontsize=8)
        self.curva.grid(True, alpha=0.3)
        self.figura.suptitle(f'Algoritmo genético de {self.nombre}')
        self.figura.tight_layout(rect=(0, 0.08, 1, 0.89))
        self.figura.text(0.98, 0.93, f'Semilla: {cpp.SEMILLA_USADA}', ha='right', fontsize=8)
        self.cromosoma = self.figura.text(0.5, 0.025, '', ha='center', family='monospace')
        self._artistas = (self.evaluados, self.puntos, self.marcador,
                          self.curva.title, self.cromosoma)
        for artista in self._artistas:
            artista.set_animated(self._usar_blit)
        canvas = self.figura.canvas
        canvas.mpl_connect('draw_event', self._al_dibujar)
        canvas.mpl_connect('resize_event', self._al_redimensionar)
        canvas.mpl_connect('close_event', self._al_cerrar)
        if self.interactiva:
            plt.show(block=False)
            canvas.draw()
            canvas.flush_events()

    def registrar_evaluacion(self, x, f):
        """Recibe la función realmente calculada, incluso de hijos descartados."""
        if x not in self.muestras or self.muestras[x] != f:
            self.muestras[x] = f
            self._version += 1
            self._minimo = f if self._minimo is None else min(self._minimo, f)
            self._maximo = f if self._maximo is None else max(self._maximo, f)

    def _ventana_abierta(self):
        if self._cerrada:
            return False
        # El número puede ser reutilizado por otra figura: verificar identidad.
        if not plt.fignum_exists(self.figura.number) or plt.figure(self.figura.number) is not self.figura:
            self._cerrada = True
            return False
        return True

    def _al_cerrar(self, evento):
        self._cerrada = True
        self._fondo = None

    def _al_redimensionar(self, evento):
        self._fondo = None

    def _al_dibujar(self, evento):
        if self._usar_blit and not self._cerrada and not self._finalizada:
            self._fondo = self.figura.canvas.copy_from_bbox(self.figura.bbox)
            for artista in self._artistas:
                self.figura.draw_artist(artista)

    def _datos_completos(self):
        if self._version_datos != self._version:
            self.x = np.fromiter(self.muestras.keys(), dtype=float)
            self.y = np.fromiter(self.muestras.values(), dtype=float)
            self._version_datos = self._version
        return np.column_stack((self.x, self.y))

    def _expandir_limites(self):
        if self._minimo is None:
            return
        if self._limites_y is not None:
            inferior, superior = self._limites_y
            if inferior <= self._minimo and self._maximo <= superior:
                return
        margen = max((self._maximo-self._minimo)*0.08, abs(self._maximo)*0.02, 0.01)
        inferior, superior = self._minimo-margen, self._maximo+margen
        if self._limites_y is not None:
            inferior = min(inferior, self._limites_y[0])
            superior = max(superior, self._limites_y[1])
        self._limites_y = (inferior, superior)
        self.curva.set_ylim(*self._limites_y)
        self._fondo = None

    def _dibujar(self):
        canvas = self.figura.canvas
        # La alternativa sin blit usa los mismos datos/artistas.
        for artista in self._artistas:
            if artista.get_animated() != self._usar_blit:
                artista.set_animated(self._usar_blit)
                self._fondo = None
        if self._usar_blit:
            if self._fondo is None:
                canvas.draw()  # draw_event guarda el fondo actualizado.
            else:
                canvas.restore_region(self._fondo)
                for artista in self._artistas:
                    self.figura.draw_artist(artista)
            canvas.blit(self.figura.bbox)
        else:
            canvas.draw_idle()
        canvas.flush_events()

    def actualizar(self, generacion, fase, poblacion, pos_mejor, guardar=True, forzar=False):
        transcurrido = time.perf_counter() - self.inicio
        aptitud = (lambda ind: ind.aptitud_bruta) if self.minimizar else (lambda ind: ind.aptitud)
        elegir = min if self.minimizar else max
        mejor = (poblacion[pos_mejor] if pos_mejor is not None else elegir(poblacion, key=aptitud))
        valor = aptitud(mejor)
        for ind in poblacion:
            self.registrar_evaluacion(ind.x, aptitud(ind))
        if guardar:
            self.historial.append((transcurrido, generacion, fase, mejor.x, valor))
        if not self._ventana_abierta():
            return  # El cálculo y la captura continúan sin trabajar en una GUI cerrada.
        if not forzar and (not self.interactiva or transcurrido-self.ultimo_refresco < self._intervalo):
            # Atender eventos también entre redibujos; no añadir esperas.
            if self.interactiva and transcurrido-self._ultimo_evento >= 0.03:
                self.figura.canvas.flush_events()
                self._ultimo_evento = time.perf_counter()-self.inicio
            return

        inicio_dibujo = time.perf_counter()
        datos = self._datos_completos()
        if len(datos) > LIMITE_PUNTOS:
            indices = np.linspace(0, len(datos)-1, LIMITE_PUNTOS, dtype=int)
            visibles = datos[indices]  # Sólo coordenadas existentes, nunca interpolaciones.
        else:
            visibles = datos
        self.evaluados.set_offsets(visibles)
        self._expandir_limites()
        self.puntos.set_offsets([(ind.x, aptitud(ind)) for ind in poblacion])
        self.marcador.set_offsets([(mejor.x, valor)])
        bits = ''.join(str(int(bit)) for bit in mejor.genes)
        self.cromosoma.set_text(f'Cromosoma del mejor individuo actual (LSB primero): {bits}')
        self.curva.set_title(f'{fase} · Generación {generacion}/{self.total} · {transcurrido:.1f} s\n'
                             f'x={mejor.x:.5f}; f(x)={valor:.5f} · '
                             f'{len(datos)} puntos únicos ({len(visibles)} visibles)', fontsize=10)
        if self.interactiva:
            self._dibujar()
        fin_dibujo = time.perf_counter()
        self.refrescos += 1
        # Medir desde el FINAL para impedir una cadena de redibujos saturada.
        self.ultimo_refresco = fin_dibujo-self.inicio
        self._ultimo_evento = self.ultimo_refresco
        self._intervalo = max(0.05, (fin_dibujo-inicio_dibujo)*4)

    def guardar(self, mejor):
        sufijo = '_minimizacion' if self.minimizar else ''
        curva = f'datos_grafica{sufijo}.txt'
        evolucion = f'datos_evolucion{sufijo}.txt'
        valor = mejor.aptitud_bruta if self.minimizar else mejor.aptitud
        np.savetxt(curva, self._datos_completos(), fmt='%.17g',
                   header=f'Todas las evaluaciones reales (pares únicos); sin interpolar\nSemilla: {cpp.SEMILLA_USADA}\n'
                          f'Mejor individuo final: x={mejor.x}, f(x)={valor}\nx f(x)')
        with open(evolucion, 'w', encoding='utf-8') as archivo:
            archivo.write('tiempo_s\tgeneracion\tfase\tx_mejor\taptitud\n')
            for tiempo, generacion, fase, x, aptitud in self.historial:
                archivo.write(f'{tiempo:.6f}\t{generacion}\t{fase}\t{x}\t{aptitud}\n')
        print(f'Datos guardados en {curva} y {evolucion}')

    def finalizar(self):
        self._finalizada = True
        for artista in self._artistas:
            artista.set_animated(False)
        if self.interactiva and self._ventana_abierta():
            self.figura.canvas.draw_idle()
            self.figura.canvas.flush_events()

def main(argv=None):
    entrada = list(sys.argv[1:] if argv is None else argv)
    if '-mini' in entrada and '-maxi' in entrada:
        raise SystemExit('Elige solo una bandera: -mini o -maxi.')
    minimizar = '-mini' in entrada
    entrada = [valor for valor in entrada if valor not in ('-mini', '-maxi')]
    programa = 'minimizacion' if minimizar else 'maximizacion'
    args = cpp.argumentos(argv=entrada, programa=programa)
    # Reutilizar exactamente la semilla automática y parámetros ya leídos.
    parametros = [str(args.x_min), str(args.x_max), str(args.TOL), str(args.tam_pob),
                  str(args.num_gen), str(args.prob_cruce), str(args.prob_mut),
                  '--semilla', str(cpp.SEMILLA_USADA), '--rand-max', str(args.rand_max)]
    if args.cruce_estricto:
        parametros.append('--cruce-estricto')
    visual = GraficaEnVivo(args, minimizar=minimizar)
    algoritmo = minimizacion if minimizar else maximizacion
    poblacion, pos_mejor, suma = algoritmo.main(parametros, observar=visual.actualizar,
                                                   observar_evaluacion=visual.registrar_evaluacion)
    visual.actualizar(args.num_gen, 'Finalizado', poblacion, pos_mejor, guardar=False, forzar=True)
    visual.guardar(poblacion[pos_mejor])
    visual.finalizar()
    if visual.interactiva and visual._ventana_abierta():
        plt.show()
    return visual


if __name__ == '__main__':
    main()
