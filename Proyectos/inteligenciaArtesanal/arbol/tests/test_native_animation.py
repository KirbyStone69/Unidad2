"""Separate processes detect Qt aborts/segfaults without killing the pytest runner."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

CHILD = r'''
import sys,random,faulthandler
faulthandler.enable()
if sys.platform!='win32':
    import resource
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from laboratorio.window import MainWindow
from laboratorio.expressions import ARITY,Node
app=QApplication([]);app.setQuitOnLastWindowClosed(False);w=MainWindow();w.show();w.tree.speed=35
w.inputs['max_depth'].setValue(10);w.inputs['max_nodes'].setValue(31)
rng=random.Random(109); mode=sys.argv[1]; count=0
for checkbox,_ in w.function_groups: checkbox.setChecked(True)
ops=[op for op,arity in ARITY.items() if arity==1]
def finish():
    w.close();w.deleteLater();QTimer.singleShot(150,app.quit);print('NATIVE_OK',count,flush=True)
def tick():
    global count
    count+=1
    if mode=='close':
        w.operate('repair');QTimer.singleShot(20,finish);return
    if mode=='worker':
        w.operate('repair');w.start(paused=True);QTimer.singleShot(80,finish);return
    if mode=='families':
        op=ops[(count-1)%len(ops)]
        w.tree.show_tree(Node(op,(Node('x'),)));w.demo=None
        w.operate('repair')
        # Complete outgoing phase, then interrupt the incoming phase.
        old=w.tree.animation;old.setCurrentTime(old.duration())
        if w.tree.animation:w.tree.animation.setCurrentTime(w.tree.animation.duration()//2)
        w.tree.toggle_animation();w.tree.toggle_animation()
        w.evaluate_tree()
    else:
        action=rng.choice(['repair']*5+['cross','mutate','resize','evaluate','random'])
        if action=='random':
            w.generate_random_data();w.tree.show_tree(Node('cos',(Node('x'),)))
        elif action=='evaluate': w.evaluate_tree()
        elif action=='resize': w.resize(rng.randint(1050,1500),rng.randint(700,1000))
        else: w.operate(action)
    assert w.demo is None or (w.demo.height<=10 and w.demo.size<=31)
    if count>=80:finish();return
    QTimer.singleShot(rng.randint(3,25),tick)
QTimer.singleShot(0,tick)
QTimer.singleShot(18000,lambda:sys.exit('WATCHDOG_TIMEOUT'))
app.exec()
'''

@pytest.mark.parametrize('mode',['mixed','families','close','worker'])
def test_native_animation_lifecycle(mode):
    env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
    result=subprocess.run([sys.executable,'-c',CHILD,mode],cwd=Path(__file__).resolve().parents[1],
                          env=env,text=True,capture_output=True,timeout=25)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'NATIVE_OK' in result.stdout,result.stdout+'\n'+result.stderr
    assert 'Traceback' not in result.stderr
