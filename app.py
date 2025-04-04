from flask import Flask, request, redirect, render_template
import os
from datetime import datetime, timedelta
from collections import defaultdict
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CADENCIA = [1, 2, 3, 6, 10, 14, 20, 27, 37, 44, 54, 70, 85, 90, 120, 150, 180, 210, 250, 300, 360]
ADICIONALES = 5

def calcular_fechas_repaso(fecha_base):
    fechas = []

    # Cadencia inicial con ajuste a día hábil
    for dias in CADENCIA:
        fecha = fecha_base + timedelta(days=dias)
        while fecha.weekday() >= 5:  # sábado o domingo
            fecha += timedelta(days=1)
        fechas.append(fecha)

    # Cadencia extendida (cada 60 días después del día 360)
    dias_extra = 360
    fecha_actual = fecha_base + timedelta(days=dias_extra)
    limite = fecha_base + timedelta(days=365 * 5)

    while fecha_actual <= limite:
        fecha = fecha_actual
        while fecha.weekday() >= 5:
            fecha += timedelta(days=1)
        fechas.append(fecha)
        fecha_actual += timedelta(days=60)

    return [f.strftime('%Y-%m-%d') for f in fechas]

@app.route('/')
def index():
    materias = defaultdict(list)
    eventos = []
    temas_hoy = []
    hoy = datetime.now().date().isoformat()

    if os.path.exists('temas.txt'):
        with open('temas.txt', 'r', encoding='utf-8') as f:
            for i, linea in enumerate(f):
                partes = linea.strip().split(' | ')
                if len(partes) == 6:
                    tema, descripcion, materia, archivo, fecha_estudio, recordatorios = partes
                    recordatorios_lista = recordatorios.split(',')
                    tema_dict = {
                        'id': i,
                        'tema': tema,
                        'descripcion': descripcion,
                        'materia': materia,
                        'archivo': archivo,
                        'fecha': fecha_estudio,
                        'recordatorios': recordatorios_lista
                    }
                    materias[materia].append(tema_dict)

                    usadas = set()
                    for fecha in recordatorios_lista:
                        clave = (tema, fecha)
                        if clave not in usadas:
                            eventos.append({
                                'title': f'{tema} ({materia})',
                                'start': fecha,
                                'group': tema
                            })
                            usadas.add(clave)
                            if fecha == hoy:
                                temas_hoy.append(f"{tema} ({materia})")

    eventos_json = json.dumps(eventos)
    return render_template('index.html', materias=materias, eventos=eventos_json, temas_hoy=temas_hoy, hoy=hoy)

@app.route('/subir', methods=['POST'])
def subir():
    tema = request.form['tema']
    descripcion = request.form['descripcion']
    materia = request.form['materia']
    archivo = request.files['archivo']
    fecha_estudio = datetime.now().date()

    fechas_repaso = calcular_fechas_repaso(fecha_estudio)
    fechas_texto = ','.join(fechas_repaso)

    archivo_nombre = archivo.filename
    if archivo:
        archivo_path = os.path.join(UPLOAD_FOLDER, archivo_nombre)
        archivo.save(archivo_path)

    with open('temas.txt', 'a', encoding='utf-8') as f:
        f.write(f'{tema} | {descripcion} | {materia} | {archivo_nombre} | {fecha_estudio} | {fechas_texto}\n')

    return redirect('/')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    with open('temas.txt', 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    if request.method == 'POST':
        tema = request.form['tema']
        descripcion = request.form['descripcion']
        materia = request.form['materia']
        fecha_str = request.form['fecha']
        archivo = request.files['archivo']
        archivo_nombre = request.form['archivo_guardado']

        fecha_estudio = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        fechas_repaso = calcular_fechas_repaso(fecha_estudio)
        fechas_texto = ','.join(fechas_repaso)

        if archivo and archivo.filename:
            archivo_nombre = archivo.filename
            archivo_path = os.path.join(UPLOAD_FOLDER, archivo_nombre)
            archivo.save(archivo_path)

        nueva_linea = f'{tema} | {descripcion} | {materia} | {archivo_nombre} | {fecha_str} | {fechas_texto}\n'
        lineas[id] = nueva_linea

        with open('temas.txt', 'w', encoding='utf-8') as f:
            f.writelines(lineas)

        return redirect('/')

    tema, descripcion, materia, archivo, fecha, _ = lineas[id].strip().split(' | ')
    return render_template('editar.html', id=id, tema=tema, descripcion=descripcion, materia=materia, archivo=archivo, fecha=fecha)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    with open('temas.txt', 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    del lineas[id]
    with open('temas.txt', 'w', encoding='utf-8') as f:
        f.writelines(lineas)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
