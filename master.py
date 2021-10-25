# LIBRERIAS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
import serial
import time
import threading
from google.cloud import storage
from datetime import datetime
import urllib.request
import random
import requests

# VARIABLES DE PATH

path_origin = os.path.join(os.path.dirname(__file__))
path_id_serial = os.path.join(path_origin,'id.json')
path_file = os.path.join(path_origin,'file.json')
path_cred = os.path.join(path_origin,'tesismlac-4b9075ea4ca4.json')
path_control = os.path.join(path_origin, 'control.txt')

#VARIABLES DE IDENTIFICACIÓN

file_id_serial = open(path_id_serial)
json_id_serial = json.load(file_id_serial)
id_serial = json_id_serial['id_number']

#VARIABLES DE CREDENCIALES DE GOOGLE

cred = credentials.Certificate(path_cred)
BucketName = 'tesismlac.appspot.com'

#INICIALIZACIÓN DE VARIABLES

CONTROL = False

fecha = datetime.now().strftime("%Y-%m-%d")

hora_in = ""
hora_fin = ""

humedad = []
temperatura = []
ruido = []
luz = []
emg = []
horas = []
hora = []
angx= []
angy = []

# FUNCIONES

def internet_available():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except:
        return False

def portIsUsable():
    try:
       ser = serial.Serial(port='COM5')
       return True
    except:
       return False

#---- MAIN

#VERIFICAR LA EXISTENCIA DEL ARCHIVO JSON A CREAR

if(os.path.isfile(path_file) == True):
    os.remove(path_file)

#VERIFICAR LA CONEXIÓN AL SERVIDOR DE GOOGLE E INICIAR LA CONEXIÓN A LA BASE DE DATOS


while(internet_available()==True and CONTROL == False):
    
    #CONEXIÓN A LA BASE DE DATOS
    
    """
    try:
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except:
        print("Error en la conexión a la Firestore")
    """

    try:
        if 'db' in locals():
            print("La base de datos ya esta conectada")
        else:
            firebase_admin.initialize_app(cred)
            db = firestore.client()
    except:
        print("Error en la conexión de la base de datos")

    #VERIFICACIÓN DEL ID DEL NODO DE CAPTURA

    try:
        serial_doc_ref = db.collection('seriales').document(id_serial)
        serial_doc = serial_doc_ref.get()
        serial_doc_id = serial_doc.id
    except:
        print("Error en la verificación del SERIAL")

    try:
        
        user_doc_ref = db.collection('usuarios')
        query_ref = user_doc_ref.where('serial', '==', ''+serial_doc_id).stream()
        COUNT = 0
        for doc in query_ref:
            COUNT = COUNT + 1
            if(COUNT == 1):
                identificacion = doc.to_dict()['identificacion']
                nombre = doc.to_dict()['nombre']
                tiempo = doc.to_dict()['tiempo']
                CONTROL = True

        tiempo = tiempo.split(":")
        tiempo_segundos = int(tiempo[0])*3600 + int(tiempo[1])*60

    except:
        print("Error en la obtención de las credenciales del evaluado")

    time.sleep(5)

#VERIFICAR LA EXISTENCIA DE UNA CONEXIÓN SERIAL

while(portIsUsable() == False):
    print("Waiting")
    time.sleep(5)

try:
    port_ref = serial.Serial('COM5', baudrate = 115200)
except serial.SerialException:
    print('port already open')

# HILOS DE EJECUCIÓN

def f1():
    to = time.time()
    if(id_serial == serial_doc_id):
        f = open(path_control, 'w')
        while (time.time() - to < tiempo_segundos):
            try:
                line = port_ref.readline()
                datos_bruto = line.decode('utf-8')
                datos_bruto = datos_bruto.split(",")
                
                hora_time = datetime.now()
                if(datos_bruto[0] == '0'):

                    humedad.append(float(datos_bruto[1]))
                    temperatura.append(float(datos_bruto[2]))
                    ruido.append(float(datos_bruto[3]))
                    luz.append(float(datos_bruto[4]))
                    hora.append(hora_time.strftime('%H:%M:%S'))
                else:
                    mic = str(int(hora_time.microsecond/1000))
                    if(len(mic) <3):
                        mic = "0"
                    else:
                        mic = mic[0]
                    hora_ref = str(hora_time.hour) + ":" + str(hora_time.minute) + ":" + str(hora_time.second) + ":" + mic
                    horas.append(hora_ref)  
                    if(datos_bruto[1] != '-'):
                        humedad.append(float(datos_bruto[1]))
                        hora.append(hora_time.strftime('%H:%M:%S'))
                    if(datos_bruto[2] != '-'):
                        temperatura.append(float(datos_bruto[2]))
                    if(datos_bruto[3] != '-'):
                        ruido.append(float(datos_bruto[3]))
                    if(datos_bruto[4] != '-'):
                        luz.append(float(datos_bruto[4]))
                    if(len(emg) == 0):
                        f.write('TRUE')
                        f.close()   
                    emg.append(float(datos_bruto[5]))
                    angx.append(float(datos_bruto[6]))
                    angy.append(float(datos_bruto[7]))
            except:
                print("Error al recoger datos")
        f = open(path_control, 'w')
        f.write('FALSE')
        f.close() 

def f2():
    while(hilo1.is_alive() == True):
        print("Measuring")
        time.sleep(10)

    hora_in = hora[0]
    hora_fin = hora[len(hora)-1]
    print(len(emg))
    categorias = ['nombre','identificacion','humedad','temperatura','ruido','luz','emg','fecha','horas','hora','angx','angy']
    data = {listname: globals()[listname] for listname in categorias}
    data["hora_in"] = hora_in
    data["hora_fin"] = hora_fin
    with open(globals()['path_file'], 'w', encoding='utf8') as outfile:
        json.dump(data, outfile, indent=4,ensure_ascii=False)

    CLOUD_CONTROL = False

    while(CLOUD_CONTROL == False and internet_available()==True):

        CloudFilename = globals()['identificacion']+"/" + str(identificacion) + ".json"
        CloudFilename = globals()['identificacion']+"/" +globals()['fecha']
        try:
            #Archivo de credenciales
            Credencial = storage.Client.from_service_account_json(json_credentials_path=globals()['path_cred'])
            #Nombre Bucket
            bucket = Credencial.get_bucket(globals()['BucketName'])
            #Nombre archivo en la nube
            CloudName = bucket.blob(CloudFilename)
            #Dirección archivo local
            CloudName.upload_from_filename(globals()['path_file'])
            print("enviado a la nube")
        except:
            print("Error en Enviado a Cloud Storage")

        try:
            user_doc_ref = db.collection('files')
            query_ref = user_doc_ref.where('filename', '==', CloudFilename).stream()
            count = 0
            for doc in query_ref:
                count = count + 1
                db.collection('files').document(str(doc.to_dict()['id'])).delete()

            if(len(data['emg'])>0):
                Random = random.randint(0,1000)
                passq = False
                while(passq == False):
                    count = 0
                    query_ref = user_doc_ref.where('id', '==', Random).stream()
                    for doc in query_ref:
                        count = count + 1
                    if (count == 0):
                        passq = True
                    else:
                        Random = random.randint(0,1000)

                data2 = {
                    'id': Random,
                    'estado': True,
                    'filename': CloudFilename
                }
                
                emg_namefile = str(data2['id'])

                db.collection('files').document(emg_namefile).set(data2)

                datos_post = {'id': Random}
                
                requests.post('http://localhost:7000/emgp', data=datos_post)

                CLOUD_CONTROL = True
        except:
            print("Error en la comunicación con la base de datos")
        
        time.sleep(10)

#EJECUCIÓN DE LOS HILOS

try:
    hilo1 = threading.Thread(target=f1)
    hilo2 = threading.Thread(target=f2)
    hilo1.start()
    hilo2.start()
except:
    print("Error en la ejecución del programa")