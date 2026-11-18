import csv
import random
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,QFormLayout,
    QLabel,QPushButton,QSpinBox,QDoubleSpinBox,QSplitter,QFileDialog,QMessageBox,
    QComboBox,QCheckBox,QScrollArea,QGraphicsDropShadowEffect,QApplication)
from .engine import Config, Node, random_tree, repair
from .expressions import constant
from .worker import EvolutionWorker
from .tree_view import TreeView
from .population_panel import PopulationPanel,ComparisonPlot
from .theme import STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ARBOL · Laboratorio de programación genética'); self.resize(1500,940)
        self.setMinimumSize(1050,700); self.setStyleSheet(STYLE)
        self.worker=None; self.best=None; self.pending=None; self.demo=None; self.rng=random.Random(17)
        self.data_rng=random.Random()
        self.x=np.linspace(-3,3,70); self.y=self.x**2+self.x+1
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(20,16,20,16); outer.setSpacing(12)
        header=QHBoxLayout(); titles=QVBoxLayout(); titles.addWidget(self.label('ARBOL / GENETIC LAB','title'))
        titles.addWidget(self.label('REGRESIÓN SIMBÓLICA  ·  EXPLORAR / EVOLUCIONAR / COMPRENDER','subtitle'))
        header.addLayout(titles); header.addStretch(); self.status=self.label('Listo · datos de ejemplo','section'); self.status.setFixedWidth(360); self.status.setWordWrap(True); header.addWidget(self.status); outer.addLayout(header)
        vertical=QSplitter(Qt.Orientation.Vertical); horizontal=QSplitter(Qt.Orientation.Horizontal)
        horizontal.addWidget(self.configuration()); horizontal.addWidget(self.tree_panel()); horizontal.addWidget(self.plot_panel())
        horizontal.setSizes([300,630,480]); vertical.addWidget(horizontal); vertical.addWidget(self.bottom_panel()); vertical.setSizes([560,300])
        outer.addWidget(vertical)
        self.plot.data(self.x,self.y)
        self.tree.show_tree(Node('+',(Node('*',(Node('x'),Node('x'))),Node('1'))),True)
        self.refresh=QTimer(self); self.refresh.setInterval(120); self.refresh.timeout.connect(self.flush); self.refresh.start()
        self.update_buttons(False)

    @staticmethod
    def label(text,name=''):
        label=QLabel(text); label.setObjectName(name); return label

    def card(self,title):
        frame=QFrame(); frame.setObjectName('card')
        shadow=QGraphicsDropShadowEffect(frame); shadow.setBlurRadius(14); shadow.setOffset(0,3); shadow.setColor(QColor(0,0,0,65)); frame.setGraphicsEffect(shadow)
        layout=QVBoxLayout(frame); layout.setContentsMargins(15,15,15,15)
        layout.addWidget(self.label(title,'section')); return frame,layout

    def button(self,text,callback,layout,primary=False):
        b=QPushButton(text); b.clicked.connect(callback)
        if primary: b.setObjectName('primary')
        layout.addWidget(b); return b

    def configuration(self):
        card,box=self.card('01 / CONFIGURACIÓN')
        scroll=QScrollArea(); scroll.setWidgetResizable(True); content=QWidget(); layout=QVBoxLayout(content)
        self.csv_button=self.button('Cargar CSV…',self.load_csv,layout)
        self.source=self.label('Ejemplo: y = x² + x + 1\n70 observaciones','subtitle'); self.source.setWordWrap(True); layout.addWidget(self.source)
        form=QFormLayout(); self.inputs={}
        for key,title,minimum,maximum,value in [('population','Población',2,1000,100),('generations','Generaciones',0,10000,0),('max_depth','Altura máxima',1,10,6),('seed','Semilla',0,999999,42),('elite_count','Elitismo',1,100,2),('max_nodes','Máx. nodos',3,511,127),('local_search','Ajustes / gen.',0,12,4),('optimizer_evaluations','Eval. / ajuste',10,1000,100)]:
            spin=QSpinBox(); spin.setRange(minimum,maximum); spin.setValue(value); self.inputs[key]=spin; form.addRow(title,spin)
        for key,title,value in [('crossover','Prob. cruce',.8),('mutation','Prob. mutación',.35),('validation_fraction','Validación',.2)]:
            spin=QDoubleSpinBox()
            spin.setDecimals(4 if key=='mutation' else 2)
            spin.setRange(0,.4 if key=='validation_fraction' else 1)
            spin.setSingleStep(.001 if key=='mutation' else .05)
            spin.setValue(value); self.inputs[key]=spin; form.addRow(title,spin)
        self.inputs['generations'].setSpecialValueText('Sin límite')
        self.inputs['generations'].setToolTip('0: sin límite de generaciones ni tiempo. Finaliza al alcanzar el objetivo de error o pulsar Detener.')
        self.inputs['population'].valueChanged.connect(self.inputs['elite_count'].setMaximum)
        self.inputs['elite_count'].setToolTip('Individuos conservados sin modificación. Si toda la población es élite, no hay variación ni ajuste local.')
        self.target_selector=QComboBox()
        self.target_selector.addItems(['NMSE ≤ 1e-4','NMSE ≤ 1e-6','NMSE ≤ 1e-8','Desactivado'])
        self.target_selector.setCurrentIndex(2); self.target_selector.setToolTip('Detiene la búsqueda al alcanzar el NMSE objetivo en entrenamiento. Consulta por separado el error de validación.'); form.addRow('Objetivo NMSE',self.target_selector)
        self.complexity_selector=QComboBox(); self.complexity_selector.addItems(['1e-6 · baja','1e-5 · normal','1e-3 · alta'])
        self.complexity_selector.setCurrentIndex(1); self.complexity_selector.setToolTip('Penalización por nodo en la selección: NMSE + penalización × nodos. Se conserva la mejor candidata por error.'); form.addRow('Complejidad',self.complexity_selector)
        layout.addLayout(form)
        layout.addWidget(self.label('BIBLIOTECA DE FUNCIONES','section'))
        self.function_groups=[]
        for text,operators in [('Trigonométricas · sin, cos',('sin','cos')),('Potencias · cuadrado, cubo',('square','cube')),('Exp / log / raíz',('exp','log','sqrt')),('tanh / absoluto',('tanh','abs')),('Extras · atan / sigmoid / neg',('atan','sigmoid','neg'))]:
            checkbox=QCheckBox(text); checkbox.setChecked('atan' not in operators)
            self.function_groups.append((checkbox,operators)); layout.addWidget(checkbox)
        layout.addWidget(self.label('Siempre: + − × ÷ · decimales ajustables','subtitle'))
        self.inputs['validation_fraction'].setToolTip('Fracción reservada que nunca se usa para entrenar ni seleccionar. Se desactiva con menos de 10 filas.'); self.inputs['optimizer_evaluations'].setToolTip('Límite de evaluaciones por ajuste, incluyendo diferencias finitas.'); self.inputs['local_search'].setToolTip('Cantidad máxima de ajustes numéricos por generación; 0 desactiva el ajuste local.')
        layout.addSpacing(15)
        self.column_x=QComboBox(); self.column_y=QComboBox(); self.column_x.setPlaceholderText('Columna x'); self.column_y.setPlaceholderText('Columna y')
        layout.addWidget(self.column_x); layout.addWidget(self.column_y)
        self.apply_button=self.button('Aplicar columnas',self.apply_csv,layout); self.apply_button.setEnabled(False)
        layout.addSpacing(12); self.educational=QCheckBox('Modo educativo'); self.educational.setChecked(True); layout.addWidget(self.educational)
        note=self.label('La búsqueda actualiza métricas.\nLos operadores animan copias\ndel mejor árbol.','subtitle'); note.setWordWrap(True); layout.addWidget(note)
        layout.addStretch(); scroll.setWidget(content); box.addWidget(scroll); return card

    def tree_panel(self):
        card,box=self.card('02 / ÁRBOL DE EXPRESIÓN')
        self.tree=TreeView(); box.addWidget(self.tree,1)
        self.expression=self.label('Arrastra para desplazar · rueda para zoom','subtitle'); self.expression.setWordWrap(True); self.expression.setMaximumHeight(62); self.expression.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); box.addWidget(self.expression)
        row=QHBoxLayout(); self.button('Ajustar',self.tree.fit_tree,row); self.button('Ver mejor árbol',self.show_solution,row); self.button('Copiar fórmula',self.copy_formula,row); box.addLayout(row)
        row=QHBoxLayout(); self.operation_buttons=[]
        for text,op in [('Cruce','cross'),('Mutación','mutate'),('Reparación','repair')]:
            self.operation_buttons.append(self.button(text,lambda checked=False,op=op:self.operate(op),row))
        box.addLayout(row)
        self.operation_note=self.label('Selecciona un operador para inspeccionar su efecto.','subtitle'); self.operation_note.setWordWrap(True); self.operation_note.setMinimumHeight(40); box.addWidget(self.operation_note)
        return card

    def plot_panel(self):
        card,box=self.card('03 / DATOS Y PREDICCIÓN')
        title=box.takeAt(0).widget(); row=QHBoxLayout(); row.addWidget(title); row.addStretch()
        self.random_button=self.button('Random',self.generate_random_data,row)
        self.random_button.setToolTip('Generar datos de una función aleatoria con las funciones habilitadas')
        box.addLayout(row)
        self.fit_status=self.label('Sin evaluar · carga datos o inicia la búsqueda','subtitle'); self.fit_status.setWordWrap(True); box.addWidget(self.fit_status)
        self.plot=ComparisonPlot()
        layers=QHBoxLayout()
        self.show_generations=QCheckBox('Mejores por generación');self.focus_data=QCheckBox('Rango de datos')
        self.focus_data.setToolTip('Mantiene el rango de los datos para ver el ajuste. Desmarca para incluir también predicciones alejadas.')
        for checkbox in (self.show_generations,self.focus_data):
            checkbox.setChecked(True);checkbox.toggled.connect(self.update_plot_layers);layers.addWidget(checkbox)
        layers.addStretch();box.addLayout(layers)
        box.addWidget(self.plot); return card

    def update_plot_layers(self):
        self.plot.set_layers(self.show_generations.isChecked(),self.focus_data.isChecked())

    def bottom_panel(self):
        card,box=self.card('04 / MEJOR SOLUCIÓN POR GENERACIÓN')
        split=QSplitter(Qt.Orientation.Horizontal); self.population_panel=PopulationPanel(); split.addWidget(self.population_panel)
        right=QWidget(); layout=QVBoxLayout(right); metrics=QHBoxLayout(); self.metric_labels={}
        for name in ['MSE','NMSE','R²','Generación']:
            column=QVBoxLayout(); column.addWidget(self.label(name,'subtitle')); label=self.label('—','section'); column.addWidget(label); self.metric_labels[name]=label; metrics.addLayout(column)
        layout.addLayout(metrics)
        self.validation_label=self.label('Entrenamiento / validación: —','subtitle'); self.validation_label.setWordWrap(True); layout.addWidget(self.validation_label)
        self.search_details=self.label('Nodos: — · diversidad: — · sin mejora: —','subtitle'); self.search_details.setWordWrap(True); layout.addWidget(self.search_details)
        row=QHBoxLayout(); self.start_button=self.button('Iniciar',self.start,row,True); self.pause_button=self.button('Pausar',self.pause,row); self.resume_button=self.button('Continuar',self.resume,row); self.stop_button=self.button('Detener',self.stop,row); layout.addLayout(row)
        row=QHBoxLayout(); self.step_button=self.button('Una generación',self.step,row); self.button('Evaluar árbol',self.evaluate_tree,row); self.button('⏯ Animación',self.tree.toggle_animation,row); layout.addLayout(row)
        speed=QHBoxLayout(); speed.addWidget(self.label('Velocidad educativa','subtitle')); selector=QComboBox(); selector.addItems(['0.5×','1×','2×']); selector.setCurrentIndex(1); selector.currentIndexChanged.connect(lambda i:setattr(self.tree,'speed',[.5,1.,2.][i])); speed.addWidget(selector); layout.addLayout(speed)
        split.addWidget(right); split.setSizes([720,650]); box.addWidget(split); return card

    def config(self):
        operators=['+','-','*','/']
        for checkbox,group in self.function_groups:
            if checkbox.isChecked(): operators.extend(group)
        return Config(**{key:widget.value() for key,widget in self.inputs.items()},
                      operators=tuple(operators),population_samples=0,target_nmse=[1e-4,1e-6,1e-8,0][self.target_selector.currentIndex()],
                      complexity=[1e-6,1e-5,1e-3][self.complexity_selector.currentIndex()])

    def update_buttons(self,running):
        self.start_button.setEnabled(not running)
        for b in [self.pause_button,self.resume_button,self.stop_button]: b.setEnabled(running)
        for widget in [*self.inputs.values(),self.target_selector,self.complexity_selector,*[c for c,_ in self.function_groups]]: widget.setEnabled(not running)
        self.random_button.setEnabled(not running)
        self.csv_button.setEnabled(not running); self.apply_button.setEnabled(not running and hasattr(self,'csv_data'))

    def start(self,checked=False,paused=False):
        if self.worker and self.worker.isRunning(): return
        self.tree.stop(); self.plot.data(self.x,self.y); self.population_panel.reset(); self.pending=None; self.best=None; self.demo=None
        self.fit_status.setText('Buscando · la curva es la mejor candidata disponible')
        self.worker=EvolutionWorker(self.x,self.y,self.config(),paused)
        self.worker.updated.connect(self.receive); self.worker.failed.connect(self.error); self.worker.state.connect(self.status.setText)
        self.worker.finished.connect(self.finished); self.update_buttons(True)
        self.centralWidget().layout().activate(); self.plot.draw()
        self.worker.start()

    def receive(self,snapshot):
        self.best=snapshot; self.pending=snapshot
        self.population_panel.record(snapshot)

    def flush(self):
        if self.pending is None: return
        s=self.pending; self.pending=None
        for key,value in [('MSE',s.mse),('NMSE',s.nmse),('R²',s.r2),('Generación',s.generation)]:
            self.metric_labels[key].setText(str(value) if key=='Generación' else f'{value:.5g}')
        self.plot.compare(self.population_panel.records,self.x)
        self.population_panel.set_snapshot(s)
        target=self.config().target_nmse or 1e-8
        if s.nmse<=target:
            if s.validation_nmse is not None and s.validation_nmse>max(target*10,1e-4):
                text='Buen entrenamiento; error alto en validación · posible sobreajuste'; color='#FFB84D'
            else:
                text='Objetivo de entrenamiento alcanzado · comprueba la validación' if s.validation_nmse is not None else 'Objetivo de entrenamiento alcanzado · sin validación disponible'; color='#00FF99'
        elif s.nmse<.01:
            text='Buen ajuste aproximado · aún no alcanza el objetivo'; color='#39FF88'
        elif s.nmse<.1:
            text='Ajuste parcial · sigue explorando'; color='#FFB84D'
        else:
            text='Ajuste insuficiente · la mejor candidata aún tiene error alto'; color='#FFB84D'
        self.fit_status.setText(text); self.fit_status.setStyleSheet(f'color:{color};background:transparent;')
        validation='No disponible' if s.validation_nmse is None else f'{s.validation_nmse:.5g}'
        self.validation_label.setText(f'Métricas: entrenamiento ({s.train_count}) · NMSE validación ({s.validation_count}): {validation}')
        self.search_details.setText(f'Nodos: {s.nodes} · altura: {s.tree.height} · diversidad: {s.diversity:.0%} · sin mejora: {s.stalled} gen. · evaluaciones: {s.evaluations}')

    def finished(self):
        self.flush(); self.plot.finish_comparison(); self.update_buttons(False)
        # Only render the solution once, after automatic evolution ends.
        if self.best: self.show_solution()

    def pause(self):
        if self.worker: self.worker.pause()

    def resume(self):
        if self.worker and self.worker.isRunning(): self.worker.resume()

    def stop(self):
        if self.worker: self.worker.stop()

    def step(self):
        if not self.worker or not self.worker.isRunning(): self.start(paused=True)
        self.worker.single_step()

    def show_solution(self):
        if not self.best: return
        self.demo=self.best.tree; self.tree.show_tree(self.demo,self.educational.isChecked())
        self.expression.setText(str(self.demo)); self.expression.setToolTip(str(self.demo)); self.plot.prediction(self.demo,self.x)
        self.pending=self.best; self.flush()
        self.operation_note.setText('Mejor candidata encontrada · métricas de entrenamiento y validación en el panel inferior.')

    def operate(self,op):
        before=self.demo or (self.best.tree if self.best else self.tree.tree)
        if before is None: return
        config=self.config()
        before=repair(before,config.max_depth,config.max_nodes)
        paths=list(before.paths()); path=self.rng.choice(paths[1:] or paths); affected=None
        if op=='cross':
            donor=random_tree(self.rng,2,True,self.config().operators); replacement=donor.at(self.rng.choice(list(donor.paths())))
            after=repair(before.replace(path,replacement),config.max_depth,config.max_nodes); color='#FF5577'
            note=f'Cruce · sale {before.at(path)} → entra {replacement} (rama donante)'
        elif op=='mutate':
            old=before.at(path); replacement=Node(self.rng.choice(['x','1','2','-1','0.5']))
            while replacement==old: replacement=Node(self.rng.choice(['x','1','2','-1']))
            after=repair(before.replace(path,replacement),config.max_depth,config.max_nodes); color='#FFB84D'; note=f'Mutación · {old} → {replacement}'
        else:
            depth=self.config().max_depth
            # A narrow chain demonstrates excess height without an exponential scene.
            excess=Node('x')
            for _ in range(depth+1): excess=Node('+',(excess,Node('x')))
            before=Node('+',(before,excess))
            after=repair(before,depth,config.max_nodes); path=(1,); color='#FFB84D'
            cuts=[p for p in after.paths() if not after.at(p).children and before.at(p).children]
            affected=[p for p in before.paths() if any(p[:len(root)]==root for root in cuts)]
            note=f'Reparación · altura {before.height} → {after.height}; nodos {before.size} → {after.size}; exceso sustituido por terminales x'
        self.operation_note.setText(note); self.expression.setText(str(after)); self.demo=after
        def done():
            self.plot.prediction(after,self.x)
            self.fit_status.setText('Vista educativa · las métricas inferiores corresponden a la búsqueda')
            self.fit_status.setStyleSheet('color:#FFB84D;background:transparent;')
        if self.educational.isChecked(): self.tree.educational(before,after,path,color,done,affected)
        else: self.tree.show_tree(after); done()

    def copy_formula(self):
        if self.tree.tree is None: return
        QApplication.clipboard().setText('y = '+self.tree.tree.to_python())
        self.operation_note.setText('Fórmula NumPy copiada con precisión completa y protecciones numéricas; requiere import numpy as np y la variable x.')

    def evaluate_tree(self):
        if self.tree.tree is None: return
        sample=float(self.x[0])
        for path,item in self.tree.nodes.items():
            subtree=self.tree.tree.at(path)
            value=float(subtree.evaluate(np.array([sample]))[0])
            item.setToolTip(f"{subtree}\nx = {sample:.4g} → {value:.5g}")
        result=float(self.tree.tree.evaluate(np.array([sample]))[0])
        self.operation_note.setText(f"Evaluación desde terminales a raíz · x = {sample:.4g} → y = {result:.5g}. Valores en cada nodo al pasar el cursor.")
        self.tree.evaluate_animation()

    def generate_random_data(self):
        if self.worker and self.worker.isRunning(): return
        rng=self.data_rng; config=self.config()
        x=np.linspace(-1,1,80); dense=np.linspace(-1,1,401)
        target=Node('x')
        for _ in range(100):
            shape=random_tree(rng,rng.randint(1,3),operators=config.operators)
            values=shape.evaluate(dense); spread=float(np.ptp(values)); deviation=float(np.std(values))
            # Avoid flat, saturated or discontinuous challenges from protected operations.
            if deviation<.05 or np.max(np.abs(values))>100 or np.max(np.abs(np.diff(values)))>.2*spread:
                continue
            scale=rng.choice((-1,1))*rng.uniform(.5,4)/deviation
            candidate=Node('+',(constant(rng.uniform(-5,5)),Node('*',(constant(scale),shape))))
            candidate=repair(candidate,config.max_depth,config.max_nodes)
            if np.ptp(candidate.evaluate(dense))>.1:
                target=candidate; break
        self.x=x; self.y=target.evaluate(x)
        self.best=None; self.pending=None; self.demo=None
        self.tree.clear_tree()
        self.population_panel.reset(); self.plot.data(self.x,self.y)
        for label in self.metric_labels.values(): label.setText('—')
        self.expression.setText('Nueva función aleatoria · pulsa Iniciar para buscar su expresión.')
        self.expression.setToolTip('')
        self.operation_note.setText('El motor recibirá únicamente los puntos de la gráfica.')
        self.source.setText('Función aleatoria\n80 observaciones · x entre −1 y 1')
        self.status.setText('Datos aleatorios · listo')
        self.fit_status.setText('Función aleatoria lista · pulsa Iniciar para buscarla')
        self.fit_status.setStyleSheet('color:#8BAF99;background:transparent;')
        self.validation_label.setText('Entrenamiento / validación: —')
        self.search_details.setText('Nodos: — · diversidad: — · sin mejora: —')

    def load_csv(self):
        path,_=QFileDialog.getOpenFileName(self,'Cargar datos','','CSV (*.csv);;Todos (*)')
        if not path: return
        try:
            with open(path,newline='',encoding='utf-8-sig') as stream:
                sample=stream.read(4096); stream.seek(0)
                dialect=csv.Sniffer().sniff(sample,delimiters=',;\t')
                rows=list(csv.reader(stream,dialect))
            if len(rows)<3 or len(rows[0])<2: raise ValueError('Se requiere encabezado y al menos dos filas.')
            headers=rows[0]
            if any(len(row)!=len(headers) for row in rows[1:]): raise ValueError('Las filas tienen distinta cantidad de columnas.')
            self.csv_data=rows[1:]; self.csv_path=path
            for combo in [self.column_x,self.column_y]: combo.clear(); combo.addItems(headers)
            self.column_x.setCurrentIndex(0); self.column_y.setCurrentIndex(1)
            self.apply_button.setEnabled(True); self.apply_csv()
        except Exception as exc: self.error(f'No se pudo cargar CSV: {exc}')

    def apply_csv(self):
        if not hasattr(self,'csv_data'): return
        try:
            ix=self.column_x.currentIndex(); iy=self.column_y.currentIndex()
            if ix<0 or iy<0: raise ValueError('Selecciona una columna para x y otra para y.')
            if ix==iy: raise ValueError('Selecciona columnas distintas para x e y.')
            x=np.array([float(row[ix]) for row in self.csv_data]); y=np.array([float(row[iy]) for row in self.csv_data])
            if len(x)<2 or not np.isfinite([x,y]).all(): raise ValueError('Se requieren al menos dos pares finitos, sin celdas vacías.')
            self.x=x; self.y=y; self.best=None; self.demo=None; self.pending=None
            self.tree.clear_tree()
            for label in self.metric_labels.values(): label.setText('—')
            self.expression.setText('Datos nuevos · pulsa Iniciar para buscar su expresión.')
            self.expression.setToolTip('')
            self.operation_note.setText('Selecciona un operador después de visualizar una candidata.')
            self.population_panel.reset(); self.plot.data(x,y); self.source.setText(f'{self.csv_path.split("/")[-1]}\n{len(x)} observaciones')
            self.status.setText('CSV cargado · listo')
            self.fit_status.setText('Datos nuevos · inicia una búsqueda para evaluar el ajuste')
            self.validation_label.setText('Entrenamiento / validación: —')
            self.search_details.setText('Nodos: — · diversidad: — · sin mejora: —')
        except Exception as exc: self.error(str(exc))

    def error(self,message):
        self.status.setText('Error'); QMessageBox.warning(self,'Datos o configuración',message)

    def closeEvent(self,event):
        self.tree.stop()
        if self.worker and self.worker.isRunning(): self.worker.stop(); self.worker.wait()
        event.accept()
