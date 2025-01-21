#Clave de acceso: AKIAYKFQQ5THCP5UZYG4
#Clave de acceso secreta: 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

#export AWS_ACCESS_KEY_ID="AKIAYKFQQ5THCP5UZYG4"
#export AWS_SECRET_ACCESS_KEY="lNiKOuLBSe+2llQRakBXFLqMnO4JfbWmWhO0YXjB"
#export AWS_DEFAULT_REGION="us-east-1"  # (e.g., us-east-1)
import boto3
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from botocore.exceptions import NoCredentialsError, ClientError
from typing import List


class S3Manager:
    """
    Clase para gestionar la carga y lectura de archivos en un bucket S3 de AWS.
    """

class S3Manager:

    def __init__(self, bucket_name: str = None, s3_client=None):
        self.bucket_name = bucket_name
        self.s3_client = s3_client
        
    def upload_file(self, local_file_path, s3_file_name):
        """
        Carga un archivo local al bucket S3.

        Args:
            local_file_path (str): Ruta local del archivo a cargar.
            s3_file_name (str): Nombre del archivo en S3 (puede incluir la ruta dentro del bucket).

        Returns:
            bool: True si la carga fue exitosa, False en caso contrario.
        """
        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_file_name)
            print(f"Archivo '{local_file_path}' cargado exitosamente a '{self.bucket_name}/{s3_file_name}'")
            return True
        except FileNotFoundError:
            print(f"El archivo local '{local_file_path}' no fue encontrado.")
            return False
        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return False
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return False

    def upload_directory(self, local_directory_path, s3_prefix=""):
        """
        Carga un directorio local completo al bucket S3.

        Args:
            local_directory_path (str): Ruta local del directorio a cargar.
            s3_prefix (str, optional): Prefijo opcional para los archivos en S3 (ruta dentro del bucket).

        Returns:
            bool: True si la carga fue exitosa, False en caso contrario.
        """
        try:
            for root, dirs, files in os.walk(local_directory_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, local_directory_path)
                    s3_file_name = os.path.join(s3_prefix, relative_path) if s3_prefix else relative_path

                    self.upload_file(local_file_path, s3_file_name)
            return True

        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return False
        except Exception as e:
            print(f"Error al cargar el directorio: {e}")
            return False


    def download_file(self, s3_file_name, local_file_path):
        """
        Descarga un archivo del bucket S3 a una ruta local.

        Args:
            s3_file_name (str): Nombre del archivo en S3 (puede incluir la ruta dentro del bucket).
            local_file_path (str): Ruta local donde se descargará el archivo.

        Returns:
            bool: True si la descarga fue exitosa, False en caso contrario.
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_file_name, local_file_path)
            print(f"Archivo '{self.bucket_name}/{s3_file_name}' descargado exitosamente a '{local_file_path}'")
            return True
        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return False
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                print(f"El archivo '{self.bucket_name}/{s3_file_name}' no fue encontrado en S3.")
            else:
                print(f"Error al descargar el archivo: {e}")
            return False
        except Exception as e:
            print(f"Error al descargar el archivo: {e}")
            return False

    def download_directory(self, s3_prefix, local_directory_path):
        """
        Descarga un directorio (prefijo) completo de S3 a una ruta local.

        Args:
            s3_prefix (str): Prefijo de S3 para descargar (ruta dentro del bucket).
            local_directory_path (str): Ruta local donde se descargará el directorio.

        Returns:
            bool: True si la descarga fue exitosa, False en caso contrario.
        """
        try:
            result = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=s3_prefix)
            if 'Contents' not in result:
                print(f"No se encontraron archivos en el prefijo '{s3_prefix}' en el bucket '{self.bucket_name}'.")
                return False
            
            for key in result['Contents']:
                file_name = key['Key']
                # Evitar descargar el prefijo mismo como un directorio vacío.
                if file_name.endswith('/'):
                    continue
                local_file_path = os.path.join(local_directory_path, os.path.relpath(file_name, s3_prefix))
                # Asegurarse de que el directorio padre exista
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                self.download_file(file_name, local_file_path)
            return True

        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return False
        except Exception as e:
            print(f"Error al descargar el directorio: {e}")
            return False
    
    def read_file_content(self, s3_file_name):
        """
        Lee el contenido de un archivo de texto en el bucket S3.

        Args:
            s3_file_name (str): Nombre del archivo en S3 (puede incluir la ruta dentro del bucket).

        Returns:
            str: Contenido del archivo como una cadena, o None si hay un error.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_file_name)
            file_content = response['Body'].read().decode('utf-8')  # asumiendo codificación utf-8
            return file_content
        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return None
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                print(f"El archivo '{self.bucket_name}/{s3_file_name}' no fue encontrado en S3.")
            else:
                print(f"Error al leer el archivo: {e}")
            return None
        except Exception as e:
            print(f"Error al leer el archivo: {e}")
            return None
    
    def list_files(self, bucket_name, prefix=""):
        """
        Lista los archivos en un bucket S3 con un prefijo opcional.

        Args:
            prefix (str, optional): Prefijo para filtrar los archivos listados.

        Returns:
            list: Lista de nombres de archivo en el bucket S3 que coinciden con el prefijo.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in response:
                return [item['Key'] for item in response['Contents']]
            else:
                print(f"No se encontraron archivos en el prefijo '{prefix}' en el bucket '{bucket_name}'.")
                return []
        except NoCredentialsError:
            print("No se encontraron credenciales de AWS. Configura tus credenciales o variables de entorno.")
            return []
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return []
        
    @contextmanager
    def get_s3_session(self):
        """Context manager para sesiones S3"""
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        try:
            yield s3_client
        finally:
            s3_client._endpoint.http_session.close()


    def get_s3():
        """Dependencia para FastAPI"""
        s3_manager = S3Manager(bucket_name="aws-resumen")
        with s3_manager.get_s3_session() as session:
            yield session


    def get_files_by_keywords(self, bucket_name: str, keyword1: str, keyword2: str) -> List[str]:
        """
        Obtiene archivos que contengan ambas palabras clave
        
        Args:
            bucket_name (str): Nombre del bucket
            keyword1 (str): Primera palabra a buscar
            keyword2 (str): Segunda palabra a buscar
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                return []
                
            # Filtrar por ambas palabras
            filtered_files = [
                obj['Key'] for obj in response['Contents']
                if keyword1.lower() in obj['Key'].lower() 
                and keyword2.lower() in obj['Key'].lower()
            ]
            
            return filtered_files
            
        except ClientError as e:
            print(f"Error al listar archivos: {e}")
            return []
'''
# Ejemplo de uso
if __name__ == "__main__":
    # Reemplaza con tus credenciales y nombre del bucket
    # O usa variables de entorno:
    # export AWS_ACCESS_KEY_ID="tu_clave_de_acceso"
    # export AWS_SECRET_ACCESS_KEY="tu_clave_secreta"
    # export AWS_DEFAULT_REGION="tu_region"

    bucket_name = "your-bucket-name"
    # descomentar las siguientes líneas si deseas utilizar credenciales explicitas, sino usara las variables de entorno
    # aws_access_key_id = "YOUR_AWS_ACCESS_KEY"
    # aws_secret_access_key = "YOUR_AWS_SECRET_ACCESS_KEY"
    # region_name = "YOUR_AWS_REGION"

    # Inicializar el manager
    # s3_manager = S3Manager(bucket_name, aws_access_key_id, aws_secret_access_key, region_name)
    s3_manager = S3Manager(bucket_name)

    # Cargar un archivo
    s3_manager.upload_file("local_file.txt", "folder/remote_file.txt")

    # Cargar un directorio
    s3_manager.upload_directory("my_local_directory", "remote_directory")
    
    # Descargar un archivo
    s3_manager.download_file("folder/remote_file.txt", "downloaded_file.txt")

    # Descargar un directorio
    s3_manager.download_directory("remote_directory", "my_downloaded_directory")
    
    # Leer el contenido de un archivo
    content = s3_manager.read_file_content("folder/remote_file.txt")
    if content:
        print(f"Contenido del archivo:\n{content}")

    # Listar archivos
    files = s3_manager.list_files("folder/")
    if files:
        print("Archivos en 'folder/':")
        for file in files:
            print(file)

'''