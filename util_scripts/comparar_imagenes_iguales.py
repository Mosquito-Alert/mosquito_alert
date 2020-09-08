import os, sys
#proj_path = "/home/webuser/webapps/tigaserver/"
proj_path = "/home/christian/Documentos/MosquitoAlert/tigatrapp-server-python36/tigatrapp-server"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from os import listdir
import cv2
tigapics_path = "../media/tigapics/"
repetigapics_path = "../media/tigapics/repetidas/"
#tigapics_path = "../media/testFotosRepe/"
#repetigapics_path = "../media/testFotosRepe/repetidas/"
import numpy
import filecmp
import shutil
import itertools

from tigaserver_app.models import Photo


def sameImages():
    listaRepetidas = []

    #images = os.listdir(tigapics_path)
    #print(images)
    diff = 0
    igual = 0
    images = []
    for (dirpath, dirnames, filenames) in os.walk(tigapics_path):
        for f in filenames:
            images.append(os.path.join(dirpath, f))

    for f1, f2 in itertools.combinations(images, 2):
        if f1 == f2 or f1 in listaRepetidas or f2 in listaRepetidas:
            continue
        else:
            if filecmp.cmp(f1, f2, shallow=False):
                #print('F1: '+f1)
                #print('F2: '+f2)

                igual = igual + 1
                listaRepetidas.append(f2)
            else:
                diff = diff + 1

    print(listaRepetidas)
    Photo.objects.filter(photo__in=listaRepetidas).delete()
    print('Fin')



'''         
    for t in listdir(tigapics_path):
        filename1 = tigapics_path + t
        for x in listdir(tigapics_path):
            filename2 = tigapics_path + x

            #if x == t or not os.path.exists(tigapics_path+t) or not os.path.exists(tigapics_path+x):
            if x == t or x in listaRepetidas or t in listaRepetidas:
                continue
            else:
                print('1: ' + filename1)
                print('2: ' + filename2)

                if filecmp.cmp(filename1, filename2, shallow=False) == False:
                    #print(filecmp.cmp(filename1, filename2, shallow=False))
                    print('Diferentes')
                else:
                    print('Iguales')
                    #shutil.move(filename2, tigapics_path+'/repe_' + x)
                    listaRepetidas.append('tigapics/'+x)
    print(listaRepetidas)
    print('--------------------------------------------------------------------')

    #for i in listaRepetidas:
        #shutil.move(tigapics_path + i, repetigapics_path + i)

    Photo.objects.filter(photo__in=listaRepetidas).delete()
    # imagen repetida 0b64af61-17dd-4604-afb8-4886629fea84.jpg
'''

sameImages()