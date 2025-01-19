import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import os
from typing import List

class MailManager:
    def __init__(self, username: str = None, password: str = None, target_subject: str = None, target_sender: str = None, banco: str = None):
        self.username = username or 'guillermotc2@gmail.com'
        self.password = password or 'bqbm zakz ithq ilwy'
        self.mail = None
        self.banco = banco or "ICBC"
        self.target_subject = target_subject or "ICBC ERESUMEN"
        self.target_sender = target_sender or "eresumen@icbc.com.ar"

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
                                            self.banco + ' ' + filename+fecha_datetime.strftime('%Y-%m-%d'))
                            
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

# Ejemplo de uso
if __name__ == "__main__":
    mail_manager = MailManager()
    mail_manager.process_emails()