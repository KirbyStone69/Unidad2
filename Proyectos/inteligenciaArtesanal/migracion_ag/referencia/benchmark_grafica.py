"""Benchmark reproducible, sin sleeps ni archivos de resultados en el proyecto.

../entorno/bin/python referencia/benchmark_grafica.py
../entorno/bin/python referencia/benchmark_grafica.py --gui

Agg compara captura y render forzado por fase; Qt offscreen prueba el refresco
cooperativo normal. No equivale a una prueba de interacción humana en escritorio.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def worker(options):
    os.environ['MPLBACKEND'] = 'QtAgg' if options.mode == 'gui' else 'Agg'
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    sys.path.insert(0, str(ROOT))
    import dataclasses
    import matplotlib.pyplot as plt
    import compatibilidad as cpp
    import grafica
    import maximizacion
    import minimizacion

    algoritmo = minimizacion if options.algorithm == 'mini' else maximizacion
    params = ['-10', '10', '0.0001', str(options.population),
              str(options.generations), '0.4', str(options.mutation), '--semilla', str(options.seed)]
    elapsed, signatures, frames, sample_counts, timer_gaps = [], [], [], [], []
    event_counts, refresh_counts = [], []
    for _ in range(options.repetitions):
        with tempfile.TemporaryDirectory(prefix='benchmark_grafica_') as directory:
            old_cwd = os.getcwd()
            os.chdir(directory)
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    args = cpp.argumentos(argv=params, programa='minimizacion' if options.algorithm == 'mini' else 'maximizacion')
                    visual = None if options.mode == 'baseline' else grafica.GraficaEnVivo(args, minimizar=options.algorithm == 'mini')
                    counts = {'draw': 0, 'blit': 0}
                    ticks = []
                    timer = None
                    if visual:
                        if options.mode == 'capture':
                            visual.interactiva = False
                        if options.mode in ('blit', 'full'):
                            visual.interactiva = True
                        if options.mode == 'blit':
                            visual._usar_blit = bool(visual.figura.canvas.supports_blit)
                        if options.mode == 'full':
                            visual._usar_blit = False
                            for artist in visual.figura.findobj():
                                if artist.get_animated():
                                    artist.set_animated(False)
                        canvas = visual.figura.canvas
                        original_draw, original_blit = canvas.draw, canvas.blit
                        def draw(*a, **kw):
                            counts['draw'] += 1
                            return original_draw(*a, **kw)
                        def blit(*a, **kw):
                            counts['blit'] += 1
                            return original_blit(*a, **kw)
                        canvas.draw, canvas.blit = draw, blit
                        if options.mode == 'gui':
                            from matplotlib.backends.qt_compat import QtCore
                            timer = QtCore.QTimer()
                            timer.setInterval(10)
                            timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
                            timer.start()
                    def observe(*a):
                        visual.actualizar(*a, forzar=options.mode in ('blit', 'full'))
                    start = time.perf_counter()
                    result = algoritmo.main(params, observar=observe if visual else None,
                                            observar_evaluacion=visual.registrar_evaluacion if visual else None)
                    if options.mode == 'gui':
                        visual.actualizar(options.generations, 'Finalizado', result[0], result[1], guardar=False, forzar=True)
                    elapsed.append(time.perf_counter() - start)
                    population, best, total = result
                    signature = ([dataclasses.asdict(ind) for ind in population], best, total, cpp._azar.getstate())
                    signatures.append(hashlib.sha256(pickle.dumps(signature)).hexdigest())
                    frames.append(dict(counts))
                    sample_counts.append(len(visual.muestras) if visual else None)
                    timer_gaps.append(max((b-a for a,b in zip(ticks,ticks[1:])), default=0))
                    event_counts.append(len(ticks))
                    refresh_counts.append(visual.refrescos if visual else 0)
                    if timer:
                        timer.stop()
                    if visual:
                        plt.close(visual.figura)
            finally:
                os.chdir(old_cwd)
    return {'median_s': statistics.median(elapsed), 'runs_s': elapsed,
            'signatures': signatures, 'frames': frames, 'samples': sample_counts,
            'max_timer_gap_s': timer_gaps, 'timer_events': event_counts, 'refreshes': refresh_counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--population', type=int, default=50)
    parser.add_argument('--generations', type=int, default=30)
    parser.add_argument('--seed', type=int, default=12345)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--mutation', type=float, default=0.01)
    parser.add_argument('--modes', nargs='+', choices=['baseline', 'capture', 'blit', 'full', 'gui'])
    parser.add_argument('--mode', choices=['baseline', 'capture', 'blit', 'full', 'gui'], help=argparse.SUPPRESS)
    parser.add_argument('--algorithm', choices=['maxi', 'mini'], help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.mode:
        print(json.dumps(worker(args)))
        return
    results = {'parameters': {'population': args.population, 'generations': args.generations,
                             'seed': args.seed, 'repetitions': args.repetitions, 'mutation': args.mutation},
               'notes': 'Times exclude figure setup; each worker writes outputs only in TemporaryDirectory. GUI uses Qt offscreen, not desktop.'}
    modes = args.modes or (['baseline', 'capture', 'blit', 'full'] + (['gui'] if args.gui else []))
    for algorithm in ['maxi', 'mini']:
        results[algorithm] = {}
        baseline = None
        for mode in modes:
            cmd = [sys.executable, str(Path(__file__).resolve()), '--mode', mode,
                   '--algorithm', algorithm, '--repetitions', str(args.repetitions),
                   '--population', str(args.population), '--generations', str(args.generations), '--seed', str(args.seed), '--mutation', str(args.mutation)]
            process = subprocess.run(cmd, cwd=tempfile.gettempdir(), capture_output=True, text=True, timeout=180)
            if process.returncode:
                raise RuntimeError(f'{algorithm}/{mode}: {process.stderr}')
            row = json.loads(process.stdout)
            if baseline is None:
                baseline = row['signatures'][0]
            row['same_population_and_rng'] = all(signature == baseline for signature in row.pop('signatures'))
            if not row['same_population_and_rng']:
                raise AssertionError(f'Algorithm changed: {algorithm}/{mode}')
            results[algorithm][mode] = row
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
