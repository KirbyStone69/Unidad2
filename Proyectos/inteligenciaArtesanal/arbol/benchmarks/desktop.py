"""Offscreen desktop responsiveness and screenshot: python -m benchmarks.desktop."""
import json
import os
from pathlib import Path
import time
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from laboratorio.window import MainWindow


def main():
    root=Path(__file__).resolve().parents[1]
    app=QApplication([]); window=MainWindow(); window.show(); app.processEvents()
    with patch('laboratorio.window.QFileDialog.getOpenFileName',return_value=(str(root/'gr.csv'),'')):
        window.load_csv()
    app.processEvents()
    ticks=[]; timer=QTimer(); timer.setInterval(10)
    timer.timeout.connect(lambda:ticks.append(time.perf_counter()))
    start=time.perf_counter(); timer.start(); window.start()
    def finish():
        if not window.start_button.isEnabled(): QTimer.singleShot(50,finish); return
        timer.stop(); window.tree.stop(); window.tree.fit_tree(); app.processEvents()
        report={'seconds':time.perf_counter()-start,'qt_timer_ticks':len(ticks),
                'max_timer_gap_seconds':float(np.max(np.diff(ticks))) if len(ticks)>1 else None,
                'generation':window.best.generation,'train_nmse':window.best.nmse,
                'validation_nmse':window.best.validation_nmse,'expression':str(window.best.tree)}
        (root/'docs/responsiveness.json').write_text(json.dumps(report,indent=2)+'\n')
        window.grab().save(str(root/'docs/preview.png'))
        print(json.dumps(report),flush=True); window.close(); app.quit()
    QTimer.singleShot(50,finish); app.exec()

if __name__=='__main__': main()
