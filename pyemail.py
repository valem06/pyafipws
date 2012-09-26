#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"M�dulo para enviar correos electr�nicos"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.04d"

import os
import sys
import traceback

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import sys, os
import smtplib
from ConfigParser import SafeConfigParser


class PyEmail:
    "Interfaz para enviar correos de Factura Electr�nica"
    _public_methods_ = ['Conectar', 'Enviar',
                        ]
    _public_attrs_ = ['Version', 'Excepcion', 'Traceback',]
        
    _reg_progid_ = "PyEmail"
    _reg_clsid_ = "{2BEF3037-BF38-41AA-84A3-6F109D543FC9}"


    def __init__(self):
        self.Version = __version__
        self.Excepcion = self.Traceback = ""

    def Conectar(self, servidor, usuario=None, clave=None, puerto=25):
        "Iniciar conexi�n al servidor de correo electronico"
        try:
            if int(puerto) != 465:
                self.smtp = smtplib.SMTP(servidor, puerto)
            else:
                # creo una conexi�n segura (SSL, no disponible en Python<2.6):
                self.smtp = smtplib.SMTP_SSL(servidor, puerto)
            self.smtp.ehlo()
            if int(puerto) == 587:
                # inicio una sesi�n segura (TLS)
                self.smtp.starttls()
            if usuario and clave:
                self.smtp.login(usuario, clave)
            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def Enviar(self, remitente, motivo, destinatario, mensaje, archivo):
        "Generar un correo multiparte y enviarlo"
        try:
            msg = MIMEMultipart()
            msg['Subject'] = motivo
            msg['From'] = remitente
            msg['Reply-to'] = remitente
            msg['To'] = destinatario
            msg.preamble = 'Mensaje de multiples partes.\n'
            
            part = MIMEText(mensaje)
            msg.attach(part)
            
            if archivo:
                part = MIMEApplication(open(archivo,"rb").read())
                part.add_header('Content-Disposition', 'attachment', 
                                    filename=os.path.basename(archivo))
                msg.attach(part)

            #print "Enviando email: %s a %s" % (msg['Subject'], msg['To'])
            self.smtp.sendmail(msg['From'], msg['To'], msg.as_string())

            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

    def Salir(self):
        "Termino la conexi�n al servidor de correo electronico"
        try:
            self.smtp.quit()
            return True
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            return False

            
if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(PyEmail)
    elif "py2exe" in sys.argv:
        from distutils.core import setup
        from nsis import build_installer, Target
        import py2exe
        setup( 
            name="PyEmail",
            version=__version__,
            description="Interfaz PyAfipWs Email %s",
            long_description=__doc__,
            author="Mariano Reingart",
            author_email="reingart@gmail.com",
            url="http://www.sistemasagiles.com.ar",
            license="GNU GPL v3",
            com_server = ['pyemail'],
            console=[],
            options={ 
                'py2exe': {
                'includes': ['email.generator', 'email.iterators', 'email.message', 'email.utils'],
                'optimize': 2,
                'excludes': ["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui","distutils.core","py2exe","nsis"],
                #'skip_archive': True,
            }},
            data_files = [(".", ["licencia.txt"]),],
            cmdclass = {"py2exe": build_installer}
        )
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([PyEmail._reg_clsid_])
    elif "/prueba" in sys.argv:
        pyemail = PyEmail()
        import getpass
        usuario = raw_input("usuario:")
        clave = getpass.getpass("clave:")
        ok = pyemail.Conectar("smtp.gmail.com", "reingart", clave, 587)
        print "login ok?", ok, pyemail.Excepcion
        print pyemail.Traceback
        ok = pyemail.Enviar(usuario, "prueba", usuario, "prueba!", None)
        print "mail enviado?", ok, pyemail.Excepcion
        ok = pyemail.Salir()
    else:        
        config = SafeConfigParser()
        config.read("rece.ini")

        if len(sys.argv)<3:
            print "Par�metros: motivo destinatario [mensaje] [archivo]"
            sys.exit(1)

        conf_mail = dict(config.items('MAIL'))
        motivo = sys.argv[1]
        destinatario = sys.argv[2]
        mensaje = len(sys.argv)>3 and sys.argv[3] or conf_mail['cuerpo']
        archivo = len(sys.argv)>4 and sys.argv[4] or None
        
        print "Motivo: ", motivo
        print "Destinatario: ", destinatario
        print "Mensaje: ", mensaje
        print "Archivo: ", archivo
        
        pyemail = PyEmail()
        pyemail.Conectar(conf_mail['servidor'], 
                         conf_mail['usuario'], conf_mail['clave'], )
        pyemail.Enviar(conf_mail['remitente'], 
                       motivo, destinatario, mensaje, archivo)

