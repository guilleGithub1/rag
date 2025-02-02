import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
from typing import List
import re
from typing import Optional, Dict
from contextlib import contextmanager
from datetime import datetime, timedelta, date


class MailManager:
    def __init__(self, username: str = None, password: str = None, target_subject: str = None, target_sender: str = None, banco: str = None):
        self.username = username or 'guillermotc2@gmail.com'
        self.password = password or 'bqbm zakz ithq ilwy'
        self.mail = None
        self.banco = banco or "ICBC"
        self.target_subject = target_subject or "ICBC ERESUMEN"
        self.target_sender = target_sender or "eresumen@icbc.com.ar"
        self.fecha= date
        self.contenido = ""
        self.link_descarga = []

    @contextmanager
    def get_mail_session(self):
        mail_manager = MailManager()
        try:
            mail_manager.connect()
            yield mail_manager
        finally:
            if mail_manager and mail_manager.mail:
                mail_manager.mail.close()
                mail_manager.mail.logout()

    def get_mail_dependency():
        mail_manager = MailManager()
        with mail_manager.get_mail_session() as mail:
            yield mail
        
    def connect(self) -> None:
        """Conectar al servidor IMAP"""
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self.mail.login(self.username, self.password)
            self.mail.select("inbox")
        except Exception as e:
            raise Exception(f"Error al conectar: {str(e)}")

    def search_emails(self, subject: str, sender: str) -> List[bytes]:
        """Buscar correos por asunto y remitente"""
        status, messages = self.mail.search(None, f'(FROM "{sender}" SUBJECT "{subject}")')
        if status != "OK":
            print("No se encontraron mensajes.")
            return []
        return messages[0].split()

    def download_attachments(self, email_id: bytes) -> None:
        """Descargar adjuntos de un correo"""
        status, msg_data = self.mail.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue
                    filename = part.get_filename()
                    if filename:
                        filename = decode_header(filename)[0][0]
                        if isinstance(filename, bytes):
                            filename = filename.decode()


                        # Validar si contiene 'eresumen'
                        if 'eresumen' in filename.lower():
                            fecha_datetime = parsedate_to_datetime(msg['Date'])
                            filepath = os.path.join(".", 'resumenes', 
                                            self.banco + '_' + fecha_datetime.strftime('%Y-%m-%d') + '_' +filename)
                            
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"Adjunto guardado: {filepath}")

    def process_emails(self) -> None:
        """Procesar todos los correos"""
        try:
            self.connect()
            email_ids = self.search_emails(self.target_subject, self.target_sender)
            print(f"Se encontraron {len(email_ids)} correos.")
            
            for email_id in email_ids:
                self.download_attachments(email_id)
        finally:
            if self.mail:
                self.mail.close()
                self.mail.logout()

    def extract_links_from_emails(self, subject: str, sender: str) -> List[Dict]:
        """
        Busca emails por asunto y remitente, extrae fecha y link
        Args:
            subject: Asunto del correo
            sender: Remitente del correo
        Returns:
            List[Dict]: Lista de diccionarios con {fecha, link}
        """
        try:
            results = []
            status, messages = self.mail.search(None, f'(FROM "{sender}" SUBJECT "{subject}")')
            
            if status != "OK" or not messages[0]:
                return results

            for email_id in messages[0].split():
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Obtener fecha
                fecha = parsedate_to_datetime(email_message['Date'])
                

                for part in email_message.walk():
                    if part.get_content_type() == "text/html":
                        content = part.get_payload(decode=True).decode()


                    
                    # Eliminar duplicados
            unique_results = list({(d['fecha'], d['link']): d for d in results}.values())
            return unique_results

        except Exception as e:
            print(f"Error procesando emails: {str(e)}")
            return []
        
        
    def get_lista_mails(self, patron_busqueda: str, sender: str) -> List[Dict]:
        """
        Busca mails que coincidan con el patrón y extrae su información
        Args:
            patron_busqueda: Patrón regex para buscar en asunto
            sender: Remitente del correo
        Returns:
            List[Dict]: Lista con {mail_id, fecha, contenido, adjuntos}
        """
        try:

            results = []
            # Búsqueda básica por remitente y palabra clave
            search_criteria = f'(FROM "{sender}")'
            status, messages = self.mail.search(None, search_criteria)
            
            if status != "OK" or not messages[0]:
                return results

            # Compilar regex una sola vez
            subject_pattern = re.compile(patron_busqueda)
            
            for email_id in messages[0].split():
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                email_message = email.message_from_bytes(msg_data[0][1])
                


                # Verificar si el asunto coincide con el patrón
                if subject_pattern.match(email_message['Subject']):
                    mail_info = {
                        'mail_id': int(email_id.decode()),
                        'fecha': parsedate_to_datetime(email_message['Date']).date(),
                        'contenido': '',
                        'adjuntos': []
                    }
                    
                    # Extraer contenido y adjuntos
                    for part in email_message.walk():
                        if part.get_content_type() == "text/html":
                            mail_info['contenido'] = part.get_payload(decode=True).decode()
                        
                        filename = part.get_filename()
                        if filename:
                            mail_info['adjuntos'].append(filename)
                    
                    results.append(mail_info)
                    print(f"Mail encontrado: {mail_info['mail_id']} - {mail_info['fecha']}")
                    
            return results
            
        except Exception as e:
            print(f"Error obteniendo mails: {str(e)}")
            return []



    def get_lista_attachments(self, mail_id: str) -> List[str]:
        """
        Obtiene los nombres de los adjuntos de un correo
        Args:
            mail_id: ID del correo
        Returns:
            List[str]: Lista con los nombres de los adjuntos
        """
        try:
            results = []
            status, msg_data = self.mail.fetch(mail_id, '(RFC822)')
            email_message = email.message_from_bytes(msg_data[0][1])
            
            for part in email_message.walk():
                filename = part.get_filename()
                if filename:
                    results.append(filename)
            return results
        except Exception as e:
            print(f"Error obteniendo adjuntos: {str(e)}")
            return []

    
    def get_payload(self, mail_id: str):
        #obtiene el payload del mail
        try:
            status, msg_data = self.mail.fetch(mail_id, '(RFC822)')
            email_message = email.message_from_bytes(msg_data[0][1])
            return email_message.get_payload(decode=True).decode()
        except Exception as e:
            print(f"Error obteniendo payload: {str(e)}")
            return ""

# Ejemplo de uso
if __name__ == "__main__":
    mail_manager = MailManager()
    mail_manager.process_emails()



