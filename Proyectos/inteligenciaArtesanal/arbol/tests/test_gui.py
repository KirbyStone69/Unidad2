import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import time
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEventLoop
from laboratorio.window import MainWindow
from laboratorio.worker import EvolutionWorker
from laboratorio.engine import Config,Node

app=QApplication.instance() or QApplication([])

def wait_until(predicate,timeout=10):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents,20)
        if predicate(): return
        time.sleep(.005)
    raise AssertionError('Tiempo de espera agotado')

def test_worker_step_resume_stop():
    worker=EvolutionWorker(np.arange(10.),np.arange(10.)**2,Config(generations=100,target_nmse=0),True)
    results=[]; worker.updated.connect(results.append); worker.start()
    try:
        wait_until(lambda:len(results)==1)
        worker.single_step(); wait_until(lambda:len(results)==2)
        assert results[-1].generation==1
        for _ in range(10): app.processEvents(); time.sleep(.005)
        assert len(results)==2
        worker.resume(); wait_until(lambda:len(results)>2)
    finally:
        worker.stop(); assert worker.wait(10000)

def test_window_operators_and_close():
    window=MainWindow(); window.show(); app.processEvents()
    window.tree.speed=20
    for op in ['cross','mutate','repair']:
        window.operate(op)
        wait_until(lambda:window.tree.tree==window.demo)
        wait_until(lambda:window.tree.animation is None or window.tree.animation.state()==window.tree.animation.State.Stopped)
    window.start(paused=True)
    wait_until(lambda:window.best is not None)
    window.step(); wait_until(lambda:window.best.generation==1)
    window.close()
    assert not window.worker.isRunning()

def test_completed_run():
    window=MainWindow(); window.inputs['generations'].setValue(3); window.target_selector.setCurrentIndex(3)
    window.start()
    wait_until(lambda:window.start_button.isEnabled())
    assert window.best.generation==3
    assert window.tree.tree==window.best.tree
    assert window.metric_labels['Generación'].text()=='3'
    window.close()

def test_load_scientific_csv_selects_x_and_y(monkeypatch):
    from pathlib import Path
    from laboratorio.window import QFileDialog
    path=Path(__file__).resolve().parent/'fixtures'/'scientific.csv'
    expected=np.loadtxt(path,delimiter=',',skiprows=1)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(path),''))
    window=MainWindow(); errors=[]; window.error=errors.append
    try:
        window.load_csv()
        assert not errors
        assert window.column_x.currentIndex()==0
        assert window.column_y.currentIndex()==1
        np.testing.assert_array_equal(window.x,expected[:,0])
        np.testing.assert_array_equal(window.y,expected[:,1])
        assert len(window.plot.scatter.get_offsets())==50
    finally: window.close()


def test_csv_missing_column_keeps_previous_data():
    window=MainWindow(); errors=[]; window.error=errors.append
    try:
        original=window.x.copy()
        window.csv_data=[['0','10'],['1','20']]
        window.column_x.addItems(['x','y']); window.column_y.addItems(['x','y'])
        window.column_x.setCurrentIndex(-1); window.column_y.setCurrentIndex(1)
        window.apply_csv()
        assert errors and 'Selecciona' in errors[0]
        np.testing.assert_array_equal(window.x,original)
    finally: window.close()

def test_unary_scene_and_function_selection():
    from laboratorio.engine import Node
    window=MainWindow()
    try:
        window.tree.show_tree(Node('cos',(Node('cube',(Node('x'),)),)))
        assert len(window.tree.nodes)==3
        assert len(window.tree.edges)==2
        for checkbox,operators in window.function_groups:
            if 'sin' in operators: checkbox.setChecked(False)
        config=window.config()
        assert 'sin' not in config.operators and 'cos' not in config.operators
        assert 'square' in config.operators
        assert config.max_depth==6 and config.local_search>0
    finally: window.close()


def test_fit_quality_does_not_call_poor_fit_a_solution():
    from laboratorio.engine import Snapshot,Node
    window=MainWindow()
    try:
        window.receive(Snapshot(1,Node('x'),10,1.,0.,2.,train_count=40,validation_count=10))
        window.flush()
        assert 'insuficiente' in window.fit_status.text().lower()
        assert 'validación' in window.validation_label.text().lower()
        window.receive(Snapshot(2,Node('x'),1e-12,1e-12,1.,1.,train_count=40,validation_count=10))
        window.flush()
        assert 'validación' in window.fit_status.text().lower()
    finally: window.close()


def test_worker_cancels_inside_numerical_optimization():
    worker=EvolutionWorker(np.linspace(0,1,100),np.cos(np.linspace(0,1,100)**3),
                           Config(generations=10000,population=100,local_search=12))
    worker.start()
    time.sleep(.02)
    worker.stop()
    assert worker.wait(3000)


def test_worker_stops_on_target():
    worker=EvolutionWorker(np.linspace(-1,1,20),np.full(20,2.37),Config(generations=100))
    results=[]; states=[]; worker.updated.connect(results.append); worker.state.connect(states.append)
    worker.start(); wait_until(lambda:not worker.isRunning()); app.processEvents()
    assert results[-1].generation==0
    assert any('Objetivo' in state for state in states)


def test_formula_copy_and_educational_label():
    window=MainWindow()
    try:
        window.educational.setChecked(False)
        window.tree.show_tree(Node('cos',(Node('x'),)))
        window.copy_formula()
        assert 'np.cos' in app.clipboard().text()
        window.operate('mutate')
        assert 'educativa' in window.fit_status.text().lower()
    finally: window.close()


def test_ui_event_loop_remains_responsive_during_search():
    from PyQt6.QtCore import QTimer
    window=MainWindow(); window.show(); app.processEvents()
    window.x=np.linspace(0,1,50); window.y=6.67+11*np.cos(7.23*window.x**3)
    ticks=[]; timer=QTimer(); timer.setInterval(10); timer.timeout.connect(lambda:ticks.append(time.monotonic()))
    timer.start()
    try:
        window.start()
        wait_until(lambda:window.start_button.isEnabled(),timeout=15)
        assert window.best.nmse<1e-6
        assert len(ticks)>3
        assert max(np.diff(ticks))<1.5
    finally:
        timer.stop(); window.close()


def test_live_predictions_do_not_redraw_static_axes(monkeypatch):
    window=MainWindow(); window.show(); app.processEvents()
    draws=[]; original=window.plot.draw
    monkeypatch.setattr(window.plot,'draw',lambda *a,**k:(draws.append(1),original(*a,**k))[1])
    try:
        assert window.plot.background is not None
        for _ in range(10): window.plot.prediction(Node('cos',(Node('x'),)),window.x)
        assert not draws
        window.plot.resize(window.plot.width()+20,window.plot.height()+10)
        app.processEvents()
        assert window.plot.background is not None
    finally: window.close()


def test_random_button_generates_fresh_searchable_data_and_clears_results():
    window=MainWindow()
    try:
        from laboratorio.engine import Snapshot
        window.data_rng.seed(27)
        window.receive(Snapshot(3,Node('x'),1,1,0))
        window.flush(); window.random_button.click()
        first=window.y.copy()
        assert window.random_button.text()=='Random'
        assert len(window.x)==len(window.y)==80
        assert np.isfinite(window.y).all() and np.ptp(window.y)>.1
        assert window.best is None and window.pending is None and window.demo is None
        assert window.population_panel.table.rowCount()==0
        assert all(label.text()=='—' for label in window.metric_labels.values())
        assert 'aleatoria' in window.source.text().lower()
        np.testing.assert_allclose(window.plot.scatter.get_offsets()[:,1],window.y)
        window.random_button.click()
        assert not np.array_equal(first,window.y)
        window.update_buttons(True); assert not window.random_button.isEnabled()
        window.update_buttons(False); assert window.random_button.isEnabled()
    finally: window.close()


def test_extra_functions_are_opt_in_and_supported_by_random():
    window=MainWindow()
    try:
        assert 'atan' not in window.config().operators
        for checkbox,operators in window.function_groups:
            if 'atan' in operators: checkbox.setChecked(True)
        assert {'atan','sigmoid','neg'}<=set(window.config().operators)
        window.data_rng.seed(49)
        window.generate_random_data()
        assert np.isfinite(window.y).all()
        window.tree.show_tree(Node('sigmoid',(Node('x'),)))
        window.demo=None;window.educational.setChecked(False);window.operate('repair')
        assert window.demo.size<=window.config().max_nodes
    finally:window.close()


def test_mutation_probability_preserves_thousandths_in_engine_config():
    window=MainWindow()
    try:
        control=window.inputs['mutation']
        control.setValue(.001)
        assert control.value()==.001
        assert window.config().mutation==.001
        control.stepUp()
        assert control.value()==.002
        control.setValue(.0001)
        assert window.config().mutation==.0001
        control.setValue(1.)
        assert window.config().mutation==1.
    finally: window.close()


def test_panel_04_shows_only_champion_per_generation_despite_multiple_elites():
    from laboratorio.engine import Evolution
    window=MainWindow()
    try:
        window.inputs['elite_count'].setValue(4)
        engine=Evolution(window.x,window.y,window.config())
        snapshot=engine.snapshot()
        window.receive(snapshot);window.flush()
        panel=window.population_panel
        assert panel.table.rowCount()==1
        assert panel.table.item(0,0).text()=='0'
        assert panel.table.item(0,4).text()==str(snapshot.tree)
        assert len(window.plot.generation_lines.get_segments())==1
        window.receive(engine.step());window.flush()
        assert panel.table.rowCount()==2
        assert len(window.plot.generation_lines.get_segments())==2
        window.generate_random_data()
        assert panel.table.rowCount()==0
        assert len(window.plot.generation_lines.get_segments())==0
    finally:window.close()


def test_population_size_limits_elite_control_and_comparison_worker_payload():
    window=MainWindow()
    try:
        window.inputs['elite_count'].setValue(8)
        window.inputs['population'].setValue(5)
        assert window.inputs['elite_count'].maximum()==5
        assert window.config().elite_count==5
        window.inputs['elite_count'].setValue(2)
        window.start(paused=True)
        wait_until(lambda:window.best is not None)
        window.flush()
        assert len(window.best.elites)==2
        assert window.best.population_size==5
        assert window.population_panel.table.rowCount()==1
    finally:window.close()


def test_population_comparison_includes_outliers_and_copies_selected_expression():
    from laboratorio.engine import Candidate,Snapshot
    window=MainWindow()
    try:
        candidate=Candidate(Node('100'),10000.,100.,-99.)
        snapshot=Snapshot(1,candidate.tree,10000.,100.,-99.,elites=(candidate,),population_sample=(candidate,),population_size=2)
        window.receive(snapshot);window.flush()
        panel=window.population_panel
        panel.table.setCurrentCell(0,4);panel.copy_button.click()
        assert app.clipboard().text()=='y = 100.0'
        window.focus_data.setChecked(False)
        low,high=window.plot.ax.get_ylim()
        assert low<=100<=high
        assert np.all(window.plot.generation_lines.get_segments()[0][:,1]==100)
    finally:window.close()


def test_shared_plot_preserves_prior_generation_curves_in_full_range_mode():
    from laboratorio.engine import Candidate,Snapshot
    window=MainWindow()
    try:
        window.focus_data.setChecked(False)
        bad=Candidate(Node('1000'),1e6,1000,-999)
        good=Candidate(Node('x'),1.,.1,.9)
        window.receive(Snapshot(1,bad.tree,1e6,1000,-999,elites=(bad,),population_size=2));window.flush()
        assert window.plot.ax.get_ylim()[1]>=1000
        window.receive(Snapshot(2,good.tree,1.,.1,.9,elites=(good,),population_size=2));window.flush()
        window.plot.finish_comparison()
        assert window.plot.ax.get_ylim()[1]>=1000
        assert window.population_panel.table.rowCount()==2
    finally:window.close()


def test_generation_champions_share_the_single_plot_in_panel_03():
    from laboratorio.engine import Evolution
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    window=MainWindow();window.show();app.processEvents()
    try:
        assert not hasattr(window.population_panel,'plot')
        assert not hasattr(window.population_panel,'tabs')
        assert window.findChildren(FigureCanvasQTAgg)==[window.plot]
        window.inputs['elite_count'].setValue(3)
        engine=Evolution(window.x,window.y,window.config())
        window.receive(engine.snapshot());window.receive(engine.step());window.flush()
        assert len(window.plot.generation_lines.get_segments())==2
        assert len(window.plot.line.get_xdata())==300
        assert window.population_panel.table.rowCount()==2
        assert not hasattr(window,'show_population')
        assert not hasattr(window.plot,'population_points')
        window.show_generations.setChecked(False)
        assert not window.plot.generation_lines.get_visible()
        window.generate_random_data()
        assert len(window.plot.generation_lines.get_segments())==0
    finally:window.close()


def test_best_per_generation_is_retained_even_between_display_refreshes():
    from laboratorio.engine import Snapshot
    window=MainWindow()
    try:
        snapshots=[Snapshot(g,Node(str(g+1)),10-g,1-g*.1,g*.1) for g in range(4)]
        for snapshot in snapshots:window.receive(snapshot)
        window.flush()
        panel=window.population_panel
        assert panel.table.rowCount()==4
        assert [panel.table.item(i,0).text() for i in range(4)]==['0','1','2','3']
        assert [panel.table.item(i,4).text() for i in range(4)]==['1','2','3','4']
        assert len(window.plot.generation_lines.get_segments())==4
        window.receive(snapshots[-1]);window.flush()
        assert panel.table.rowCount()==4
        panel.table.setCurrentCell(1,4);panel.copy_button.click()
        assert app.clipboard().text()=='y = 2.0'
        assert not hasattr(window.plot,'population_points')
        window.generate_random_data()
        assert not panel.history and panel.table.rowCount()==0
        assert len(window.plot.generation_lines.get_segments())==0
    finally:window.close()


def test_unlimited_search_can_step_pause_resume_and_stop():
    # Zero means unlimited, rather than an exhausted generation budget.
    from unittest.mock import patch
    class Engine:
        def __init__(self,*args,**kwargs):
            self.generation=0; self.converged=False
        def snapshot(self): return self.generation
        def step(self):
            self.generation+=1
            time.sleep(.001)
            return self.generation
    config=Config(generations=0)
    config.validate()
    worker=EvolutionWorker(np.arange(10.),np.arange(10.),config,True)
    results=[]; worker.updated.connect(results.append)
    with patch('laboratorio.worker.Evolution',Engine):
        worker.start()
        try:
            wait_until(lambda:results==[0])
            worker.single_step(); wait_until(lambda:len(results)==2)
            assert results[-1]==1 and worker.isRunning()
            worker.resume(); wait_until(lambda:len(results)>5)
            worker.pause(); time.sleep(.03); app.processEvents()
            count=len(results); time.sleep(.03); app.processEvents()
            assert len(results)==count and worker.isRunning()
        finally:
            worker.stop(); assert worker.wait(10000)


def test_winner_is_dark_red_and_default_search_has_no_progress_bar():
    from PyQt6.QtWidgets import QProgressBar
    window=MainWindow()
    try:
        assert window.config().generations==0
        assert not window.findChildren(QProgressBar)
        assert window.plot.line.get_color()=='#B83240'
        legend=window.plot.ax.get_legend()
        winner=next(h for h,t in zip(legend.legend_handles,legend.get_texts()) if t.get_text()=='Mejor predicción')
        assert winner.get_color()=='#B83240'
    finally: window.close()
