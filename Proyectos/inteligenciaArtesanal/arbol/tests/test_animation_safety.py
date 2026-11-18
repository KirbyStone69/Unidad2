"""Scene lifecycle regressions. Native Qt failures are additionally subprocess-tested."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor
from laboratorio.engine import Node
from laboratorio.window import MainWindow
from laboratorio.tree_view import TreeView
app=QApplication.instance() or QApplication([])


def test_repair_obeys_budget_even_with_only_binary_functions():
    w=MainWindow()
    try:
        w.educational.setChecked(False)
        for checkbox,_ in w.function_groups: checkbox.setChecked(False)
        w.inputs['max_nodes'].setValue(15)
        for _ in range(8):
            w.operate('repair')
            assert w.demo.size<=15
            assert w.demo.height<=w.config().max_depth
    finally: w.close()


def test_educational_specimen_is_bounded_at_maximum_height():
    w=MainWindow()
    try:
        for checkbox,_ in w.function_groups: checkbox.setChecked(False)
        w.inputs['max_depth'].setValue(10);w.inputs['max_nodes'].setValue(15)
        w.operate('repair')
        assert w.tree.tree.height>w.config().max_depth
        assert len(w.tree.nodes)<=15+2*10+5
        assert w.demo.size<=15
    finally: w.close()


def test_cancelled_animation_cannot_recolor_a_replacement_tree():
    view=TreeView()
    try:
        view.show_tree(Node('+',(Node('x'),Node('1'))),True)
        stale=view.animation.animationAt(0)
        view.show_tree(Node('cos',(Node('x'),)))
        before=QColor(view.nodes[()].pen().color());width=view.nodes[()].pen().widthF()
        stale.valueChanged.emit(.5)
        assert view.nodes[()].pen().color()==before
        assert view.nodes[()].pen().widthF()==width
    finally:view.stop();view.close()


def test_clear_scene_invalidates_frames_and_completion():
    view=TreeView();completed=[]
    before=Node('+',(Node('x'),Node('1')))
    try:
        view.educational(before,Node('x'),(), '#FF5577',lambda:completed.append(True))
        outgoing=view.animation
        view.clear_tree()
        outgoing.finished.emit()
        assert view.tree is None and not view.nodes and not view.scene().items()
        assert not completed
    finally:view.stop();view.close()


def test_loading_csv_cancels_repair_and_old_completion(monkeypatch):
    from pathlib import Path
    from laboratorio.window import QFileDialog
    w=MainWindow()
    try:
        w.operate('repair');outgoing=w.tree.animation
        fixture=Path(__file__).resolve().parent/'fixtures'/'scientific.csv'
        monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args:(str(fixture),''))
        w.load_csv()
        outgoing.finished.emit()
        assert w.tree.tree is None
        assert w.tree.animation is None
        assert 'Datos nuevos' in w.fit_status.text()
        assert w.best is None and w.pending is None
        assert all(label.text()=='—' for label in w.metric_labels.values())
    finally:w.close()


def test_incoming_completion_ignored_after_new_random_data():
    w=MainWindow()
    try:
        w.operate('repair')
        outgoing=w.tree.animation;outgoing.setCurrentTime(outgoing.duration())
        incoming=w.tree.animation
        w.generate_random_data()
        incoming.finished.emit()
        assert w.tree.tree is None
        assert 'aleatoria lista' in w.fit_status.text()
        assert not w.tree.scene().items()
    finally:w.close()
