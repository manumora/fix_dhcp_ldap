#!/usr/bin/env python3
# filepath: fix_dhcp_ldap.py

import ldap3
import logging
import sys
from ldap3 import MODIFY_REPLACE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LDAP_SERVER = 'servidor'
LDAP_USER = 'cn=admin,ou=people,dc=instituto,dc=extremadura,dc=es'
LDAP_PASSWORD = ''  # Actualiza con tu contraseña
LDAP_BASE_DN = 'dc=instituto,dc=extremadura,dc=es'
HOSTS_BASE = 'ou=hosts,dc=instituto,dc=extremadura,dc=es'
DHCP_BASE = 'cn=group1,cn=INTERNAL,cn=DHCP Config,dc=instituto,dc=extremadura,dc=es'
DOMAIN = '' # Actualiza con el dominio de tu centro

def connect_to_ldap():
    """Establece conexión con servidor LDAP"""
    try:
        server = ldap3.Server(LDAP_SERVER, get_info=ldap3.ALL)
        connection = ldap3.Connection(server, LDAP_USER, LDAP_PASSWORD, auto_bind=True)
        logger.info("Conexión LDAP establecida correctamente")
        return connection
    except Exception as e:
        logger.error(f"Error al conectar con LDAP: {e}")
        sys.exit(1)

def get_hosts_info(conn):
    """Obtiene información de hosts desde LDAP"""
    hosts_info = []

    base_dn = f"dc={DOMAIN},{HOSTS_BASE}"
    search_filter = "(objectclass=dNSDomain2)"
    attributes = ['dc', 'arecord', 'associateddomain']

    logger.info(f"Buscando hosts en {base_dn}")
    conn.search(base_dn, search_filter, attributes=attributes)

    for entry in conn.entries:
        try:
            hostname = entry.dc.value
            ip = entry.arecord.value
            hosts_info.append({
                'hostname': hostname,
                'ip': ip
            })
            logger.info(f"Encontrado host: {hostname} con IP: {ip}")
        except Exception as e:
            logger.warning(f"Error procesando host {entry.entry_dn}: {e}")
    
    return hosts_info

def update_dhcp_entries(conn, hosts_info):
    """Actualiza entradas DHCP con la IP correcta"""
    updated = 0
    errors = 0

    for host in hosts_info:
        hostname = host['hostname']
        ip = host['ip']

        dhcp_dn = f"cn={hostname},{DHCP_BASE}"

        conn.search(dhcp_dn, "(objectclass=dhcpHost)", attributes=['dhcpstatements'])
        if not conn.entries:
            logger.warning(f"No se encontró configuración DHCP para {hostname}")
            continue

        current_value = conn.entries[0].dhcpstatements.value
        if current_value and 'fixed-address' in current_value:
            if f"fixed-address {ip}" == current_value:
                logger.info(f"El host {hostname} ya tiene la IP correcta: {ip}")
                continue

            try:
                conn.modify(dhcp_dn, {'dhcpstatements': [(MODIFY_REPLACE, [f"fixed-address {ip}"])]})
                if conn.result['result'] == 0:  # 0 = éxito
                    logger.info(f"Actualizado {hostname}: '{current_value}' -> 'fixed-address {ip}'")
                    updated += 1
                else:
                    logger.error(f"Error al actualizar {hostname}: {conn.result['description']}")
                    errors += 1
            except Exception as e:
                logger.error(f"Excepción al actualizar {hostname}: {e}")
                errors += 1

    return updated, errors

def main():
    logger.info("Iniciando actualización de entradas DHCP en LDAP")
    conn = connect_to_ldap()

    hosts_info = get_hosts_info(conn)
    logger.info(f"Se encontraron {len(hosts_info)} hosts")

    updated, errors = update_dhcp_entries(conn, hosts_info)

    logger.info(f"Proceso completado: {updated} entradas actualizadas, {errors} errores")

    conn.unbind()
    logger.info("Desconexión LDAP realizada")

if __name__ == "__main__":
    main()