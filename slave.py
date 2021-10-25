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
            #Archivo de credenciales
Credencial = storage.Client.from_service_account_json(json_credentials_path=globals()['path_cred'])
#Nombre Bucket
bucket = Credencial.get_bucket(BucketName)

# FUNCIONES
fecha = datetime.now().strftime("%Y-%m-%d")
CONTROL = False

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
                CONTROL = True

    except:
        print("Error en la obtención de las credenciales del evaluado")

    time.sleep(5)


IMG = []

def f1():

    to = time.time()
    while(True):
        f = open(path_control,'r')
        stra = f.readline()
        f.close()
        if(stra == "TRUE"):
            break
        else:
            print("ESPERANDO POR SEÑAL DE CONTROL")

    while(True):
        hora_time = datetime.now()
        f = open(path_control,'r')
        stra = f.readline()
        f.close()
        if(stra == "TRUE"):

            #COLOCAR SCREESOHOT

            if(time.time() - to >= 1):

                filename = "17_20_51.jpg"
                IMG.append(filename)

                print(time.time())
                
                to = time.time()
            

        else:
            break


def f2():
    while(hilo1.is_alive() == True):
        print("Measuring")
        time.sleep(10)



    print(IMG)
    
    dir = os.path.join(path_origin, 'imagenes') #####3 IMAGENES ES LA CARPETA DONDE ESTAN LAS IMAGENES

    for imagen in IMG:

        filename = os.path.join(dir,imagen)

        CloudFilename = globals()['identificacion']+"/" +globals()['fecha'] + "d/" + filename.replace(".jpg","")

        try:
            #NOMBRE EN LA NUBE
            CloudName = bucket.blob(CloudFilename)

            #Dirección archivo local
            CloudName.upload_from_filename(filename, predefined_acl = "publicRead")
        except:
            print("No se pudo envar a la nube")


try:
    hilo1 = threading.Thread(target=f1)
    hilo2 = threading.Thread(target=f2)
    hilo1.start()
    hilo2.start()
except:
    print("Error en la ejecución del programa")