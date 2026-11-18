import threading
from PyQt6.QtCore import QThread, pyqtSignal
from .engine import Evolution
from .optimization import SearchCancelled

class EvolutionWorker(QThread):
    updated=pyqtSignal(object)
    failed=pyqtSignal(str)
    state=pyqtSignal(str)

    def __init__(self,x,y,config,paused=False):
        super().__init__()
        self.x=x; self.y=y; self.config=config
        self.condition=threading.Condition(); self.paused=paused; self.stopped=False; self.steps=0

    def pause(self):
        with self.condition: self.paused=True

    def resume(self):
        with self.condition:
            self.paused=False; self.steps=0; self.condition.notify_all()

    def single_step(self):
        with self.condition:
            self.paused=True; self.steps+=1; self.condition.notify_all()

    def stop(self):
        with self.condition:
            self.stopped=True; self.condition.notify_all()

    def run(self):
        try:
            self.state.emit('Inicializando población')
            engine=Evolution(self.x,self.y,self.config,cancel=lambda:self.stopped)
            self.updated.emit(engine.snapshot())
            while (self.config.generations==0 or engine.generation<self.config.generations) and not engine.converged:
                with self.condition:
                    if self.paused and not self.steps: self.state.emit('En pausa')
                    while self.paused and not self.steps and not self.stopped: self.condition.wait()
                    if self.stopped: break
                    if self.steps: self.steps-=1
                self.state.emit('Evolucionando')
                self.updated.emit(engine.step())
            self.state.emit('Detenido' if self.stopped else 'Objetivo de entrenamiento alcanzado' if engine.converged else 'Límite de generaciones alcanzado')
        except SearchCancelled:
            self.state.emit('Detenido')
        except Exception as exc: self.failed.emit(str(exc))
