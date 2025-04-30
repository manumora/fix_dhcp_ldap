# Actualizador de Entradas DHCP en LDAP

Este script automatiza la actualización de direcciones IP fijas en las entradas DHCP de un servidor LDAP. Sincroniza la información entre los registros de hosts y la configuración DHCP correspondiente.

## Descripción

El script `fix_dhcp_ldap.py` realiza las siguientes acciones:

1. Conecta con el servidor LDAP especificado
2. Extrae información de hosts (nombres e IPs) desde la base LDAP
3. Para cada host, verifica si existe una entrada DHCP correspondiente
4. Actualiza la dirección IP en la configuración DHCP si es necesario
5. Registra todas las operaciones en un log detallado

## Requisitos

- Python 3.6 o superior
- Biblioteca `ldap3` para Python
- Acceso a un servidor LDAP con privilegios de escritura

Para instalar las dependencias:

```bash
apt install python3-ldap3
```
o
```bash
pip install ldap3
```

## Configuración

El script utiliza las siguientes variables de configuración que pueden necesitar modificación:

```python
LDAP_SERVER = 'servidor'
LDAP_USER = 'cn=admin,ou=people,dc=instituto,dc=extremadura,dc=es'
LDAP_PASSWORD = ''  # Actualiza con tu contraseña
LDAP_BASE_DN = 'dc=instituto,dc=extremadura,dc=es'
HOSTS_BASE = 'ou=hosts,dc=instituto,dc=extremadura,dc=es'
DHCP_BASE = 'cn=group1,cn=INTERNAL,cn=DHCP Config,dc=instituto,dc=extremadura,dc=es'
```

**Importante**: Es necesario configurar `LDAP_PASSWORD` antes de ejecutar el script.

## Copia de seguridad

**IMPORTANTE**: Antes de ejecutar el script, es esencial realizar una copia de seguridad completa del directorio LDAP.

Para crear una copia de seguridad del servidor LDAP:

```bash
# Conectar al servidor LDAP
sudo slapcat -n 1 -l backup_ldap_$(date +%Y%m%d).ldif

# Verificar la copia de seguridad
ls -la backup_ldap_*.ldif
```

En caso de necesitar restaurar la copia de seguridad:

```bash
# Detener el servicio LDAP
sudo systemctl stop slapd

# Restaurar desde la copia de seguridad
sudo slapadd -n 1 -l backup_ldap_YYYYMMDD.ldif

# Corregir permisos
sudo chown -R openldap:openldap /var/lib/ldap/

# Reiniciar el servicio LDAP
sudo systemctl start slapd
```

## Uso

Para ejecutar el script:

```bash
python3 fix_dhcp_ldap.py
```

## Funcionamiento

El proceso se divide en tres pasos principales:

### 1. Conexión al servidor LDAP

El script establece una conexión autenticada con el servidor LDAP utilizando las credenciales proporcionadas.

### 2. Obtención de información de hosts

Recopila información de los hosts almacenados en la ruta `dc=santaeulalia,ou=hosts,...` extrayendo:
- Nombre del host (atributo `dc`)
- Dirección IP (atributo `arecord`)

### 3. Actualización de entradas DHCP

Para cada host encontrado:
- Busca la entrada DHCP correspondiente en `cn={hostname},cn=group1,cn=INTERNAL,cn=DHCP Config,...`
- Compara la dirección IP actual en la configuración DHCP con la IP del host
- Actualiza la configuración DHCP si es necesaria

## Logs

El script registra todas las operaciones con diferentes niveles de detalle:
- INFO: Operaciones normales y resultados
- WARNING: Problemas no críticos (hosts sin entrada DHCP)
- ERROR: Fallos en operaciones de actualización

## Ejemplo de salida

```
2023-11-10 10:15:23 - INFO - Iniciando actualización de entradas DHCP en LDAP
2023-11-10 10:15:24 - INFO - Conexión LDAP establecida correctamente
2023-11-10 10:15:24 - INFO - Buscando hosts en dc=santaeulalia,ou=hosts,dc=instituto,dc=extremadura,dc=es
2023-11-10 10:15:25 - INFO - Encontrado host: servidor01 con IP: 192.168.1.10
2023-11-10 10:15:25 - INFO - Encontrado host: servidor02 con IP: 192.168.1.11
2023-11-10 10:15:26 - INFO - Se encontraron 2 hosts
2023-11-10 10:15:26 - INFO - Actualizado servidor01: 'fixed-address 192.168.1.5' -> 'fixed-address 192.168.1.10'
2023-11-10 10:15:27 - INFO - El host servidor02 ya tiene la IP correcta: 192.168.1.11
2023-11-10 10:15:27 - INFO - Proceso completado: 1 entradas actualizadas, 0 errores
2023-11-10 10:15:27 - INFO - Desconexión LDAP realizada
```

## Descargo de responsabilidad

**AVISO**: Este script modifica entradas en el servidor LDAP y puede causar problemas en la configuración de red si se utiliza incorrectamente. El autor no se responsabiliza de los posibles daños que pueda causar el uso de este script en entornos de producción. Se recomienda encarecidamente:

1. Realizar siempre copias de seguridad antes de ejecutar el script
2. Probar primero en un entorno de desarrollo o prueba
3. Revisar los logs generados para verificar las modificaciones realizadas

El uso de este script implica la aceptación de estos términos y la responsabilidad de las consecuencias derivadas de su ejecución.
