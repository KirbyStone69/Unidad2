"""Standalone PNG charts with the laboratory palette, usable without a display."""
from pathlib import Path
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

BG='#07130D'; PANEL='#10241A'; TEXT='#E4FBEA'; SECONDARY='#8BAF99'
NEON='#39FF88'; WINNER='#B83240'
LABELS={'grid':'Grid exhaustivo','genetic-grid':'Grid genético','genetic-direct':'AG directo'}


def _figure():
    figure=Figure(figsize=(12,5.6),facecolor=BG,layout='constrained')
    FigureCanvasAgg(figure)
    return figure


def _style(ax,title,xlabel,ylabel):
    ax.set_facecolor(PANEL)
    ax.set_title(title,color=TEXT,pad=14)
    ax.set_xlabel(xlabel,color=TEXT);ax.set_ylabel(ylabel,color=TEXT)
    ax.tick_params(colors=SECONDARY)
    for spine in ax.spines.values():spine.set_color('#193528')
    ax.grid(color='#244633',alpha=.6)
    ax.set_axisbelow(True)


def export_plots(results,directory):
    if not results:
        raise ValueError('No hay resultados para graficar.')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    figure=_figure()
    axes=figure.subplots(1,len(results),squeeze=False)[0]
    for ax,result in zip(axes,results):
        if result.history:
            x=[row['generation'] for row in result.history]
            best=[row['best'] for row in result.history]
            mean=[row['mean'] for row in result.history]
            xlabel='Generación (0: población inicial)'
            ax.plot(x,mean,color=NEON,marker='.',label='Accuracy promedio')
        else:
            x=np.arange(1,len(result.evaluations)+1)
            accuracy=[row['accuracy'] for row in result.evaluations]
            best=np.maximum.accumulate(accuracy)
            xlabel='Configuraciones evaluadas'
            ax.scatter(x,accuracy,color=NEON,s=9,label='Accuracy de configuración')
        ax.plot(x,best,color=WINNER,lw=2.3,label='Mejor accuracy observada')
        ax.axhline(result.baseline['accuracy'],color=SECONDARY,ls='--',lw=1,label='AdaBoost por defecto')
        ax.set_ylim(0,1.02)
        _style(ax,LABELS[result.method],xlabel,'Accuracy CV')
        legend=ax.legend(facecolor=PANEL,edgecolor='#193528',fontsize=7,loc='lower right')
        for text in legend.get_texts():text.set_color(TEXT)
    figure.suptitle('01 / EVOLUCIÓN DEL AJUSTE · WINE + ADABOOST',color=TEXT,fontsize=14)
    evolution=directory/'evolution.png'
    figure.savefig(evolution,dpi=150)
    comparison=_figure()
    accuracy_ax,time_ax=comparison.subplots(1,2)
    labels=[LABELS[r.method] for r in results]
    accuracy_ax.bar(labels,[r.best_accuracy for r in results],color=NEON,width=.55)
    time_ax.bar(labels,[r.elapsed_seconds for r in results],color='#8BAF99',width=.55)
    accuracy_ax.set_ylim(0,1.08)
    for index,result in enumerate(results):
        accuracy_ax.text(index,result.best_accuracy+.02,f'{result.best_accuracy:.4f}',ha='center',color=TEXT)
        time_ax.annotate(f'{result.elapsed_seconds:.2f} s',(index,result.elapsed_seconds),
                         xytext=(0,5),textcoords='offset points',ha='center',color=TEXT)
    time_ax.margins(y=.2)
    _style(accuracy_ax,'Mejor resultado observado','Método','Accuracy CV')
    _style(time_ax,'Tiempo de búsqueda (sin baseline)','Método','Segundos')
    shared=len({r.cv['split_hash'] for r in results})==1
    comparison.suptitle('02 / COMPARACIÓN · '+('MISMAS PARTICIONES CV' if shared else 'PARTICIONES DIFERENTES'),color=TEXT if shared else '#FFB84D',fontsize=14)
    footer='\n'.join(f'{LABELS[r.method]}: n_estimators={r.best_params["n_estimators"]}, '
                     f'learning_rate={r.best_params["learning_rate"]:.6g}' for r in results)
    comparison.supxlabel(footer+'\nResultados de selección; no equivalen a accuracy de prueba independiente.',color=SECONDARY,fontsize=9)
    path=directory/'comparison.png';comparison.savefig(path,dpi=150)
    return [evolution,path]
