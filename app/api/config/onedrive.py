#Id. de aplicación (cliente):1fab313e-8599-47ec-aaba-2ba2a34db8a0
#Identificador de objeto:9ca34ced-3c51-4106-bb92-6a8df74b50cb
#Id. de directorio (inquilino):c7c2c345-9c23-4f8e-b4a3-8f01abe40d4d

#Descripción: resumenesKey
#Valor: r_68Q~8R_j5qEPw64WNsVaYVtTHUut.GIeZ~IdoK
#secret: c5ea4c1a-e534-417a-b76f-ac8223d4cfd1


#Id. de aplicación (cliente):3c052292-5e66-4f8b-9838-76dbcea01f1c
#Identificador de objeto:9e631e0c-4faa-4bb5-af24-45c4323190b2
#Id. de directorio (inquilino):c7c2c345-9c23-4f8e-b4a3-8f01abe40d4d

#Descripción: resumenv2Key
#Valor: ~cX8Q~cwGedzvPkmdXKk8iICqPKgykGjf.G0vaex
#secret: f80cc4f8-537e-41b8-8b81-ebf9210bb810

import os
import requests
from msal import PublicClientApplication
import time

# Configuración de la aplicación
CLIENT_ID = '3c052292-5e66-4f8b-9838-76dbcea01f1c'
CLIENT_SECRET = '~cX8Q~cwGedzvPkmdXKk8iICqPKgykGjf.G0vaex'
TENANT_ID = 'consumers'  # Cambiamos a 'consumers' para OneDrive personal
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['Files.Read', 'Files.Read.All', 'User.Read']
REDIRECT_URI = 'http://localhost:8000/callback'

# Autenticación
app = PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY
)
"""
# Obtener el token de acceso
result = None
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(SCOPES, account=accounts[0])

if not result:
    flow = app.initiate_device_flow(scopes=SCOPES)
    if 'user_code' not in flow:
        raise Exception('Failed to create device flow')
    
    print(flow['message'])
    
    result = app.acquire_token_by_device_flow(flow)

if 'access_token' in result:
    access_token = result['access_token']
else:
    print(result.get('error'))
    print(result.get('error_description'))
    print(result.get('correlation_id'))
    raise Exception('No se pudo obtener el token de acceso')

# Función para obtener archivos de una carpeta específica
def get_files_in_folder(folder_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error: {response.status_code}')
        print(response.json())
        return None


def list_root_folders():
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    # Endpoint para OneDrive personal
    url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error: {response.status_code}')
        print(response.json())
        return None


# Ejemplo de uso para listar carpetas en la raíz de OneDrive
folders = list_root_folders()
if folders:
    for item in folders['value']:
        if 'folder' in item:  # Verifica si el item es una carpeta
            print(f"Nombre: {item['name']}, ID: {item['id']}")

# Ejemplo de uso para obtener archivos de una carpeta específica
folder_id = 'your_folder_id'  # Reemplaza con el ID de la carpeta deseada
files = get_files_in_folder(folder_id)
if files:
    for file in files['value']:
        print(f"Nombre: {file['name']}, ID: {file['id']}")
"""