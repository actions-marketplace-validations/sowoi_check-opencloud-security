# Desplegar el escáner de seguridad de OpenCloud con Ansible

Los playbooks de [`ansible/`](../../ansible/README.md) instalan y configuran el
complemento en uno o varios hosts de Icinga2, con una instalación nativa o con
Docker. También crean los objetos `CheckCommand` y `Service` descritos en
[Icinga Director](../icinga-director.md) y en
[Icinga2 / Nagios](../installation.md#icinga2--nagios).

Esta página es la versión breve. [`ansible/README.md`](../../ansible/README.md)
es la referencia y el archivo que se mantiene al día con los propios roles.

<!-- TOC -->
* [Despliegue automatizado con Ansible](#automated-deployment-with-ansible)
  * [Qué rol utilizar](#which-role-to-use)
  * [Inicio rápido](#quick-start)
  * [Configurar la comprobación](#configuring-the-check)
  * [Antes de confirmar un cambio en el rol](#before-you-commit-a-change-to-the-role)
<!-- TOC -->


## Qué rol utilizar {#which-role-to-use}

| Rol | Instala | Úselo cuando |
|:-----|:---------|:------------|
| `opencloud_check_native` | El complemento en un virtualenv propio, enlazado en el directorio de complementos de Nagios | El host de monitorización tiene Python y quiere el menor número posible de piezas |
| `opencloud_check_docker` | La imagen, construida en el host de destino y ejecutada como `docker run` | Prefiere no instalar paquetes de Python en el host de monitorización |

Ambos roles escriben los mismos objetos de Icinga2, así que un host puede pasar
de uno a otro sin reescribir la definición del servicio.

## Inicio rápido {#quick-start}

```shell
cd ansible
cp inventory.example.ini inventory.ini
$EDITOR inventory.ini   # the Icinga2 hosts, and opencloud_check_host per host

# Native (virtualenv) install:
ansible-playbook -i inventory.ini playbooks/deploy_native.yml

# ... or the Docker install:
ansible-galaxy collection install -r requirements.yml
ansible-playbook -i inventory.ini playbooks/deploy_docker.yml
```

Los playbooks son idempotentes, así que volver a ejecutar uno es también la
forma de actualizar: la versión del complemento y los objetos de Icinga2 se
ajustan en cada ejecución.

## Configurar la comprobación {#configuring-the-check}

Cada ajuste es una variable `opencloud_check_*` que se corresponde una a una
con las variables de entorno `COS_*` y las opciones de la CLI de la
[tabla de opciones](../cli-reference.md#options). Una entrada de host realista:

```ini
[icinga_hosts]
monitoring.example.com

[icinga_hosts:vars]
opencloud_check_host=opencloud.example.com
opencloud_check_port=9200
opencloud_check_check_hardening=true
opencloud_check_update_warning=true
opencloud_check_interval=24h
```

`opencloud_check_host` toma por defecto el valor de `inventory_hostname`, lo
cual es correcto cuando el agente de monitorización se ejecuta en el propio
host de OpenCloud e incorrecto en casi todos los demás casos: defínalo
explícitamente.

Mantenga `opencloud_check_interval` en `24h` o más. Cada ejecución es un
análisis real contra una instancia real, no una consulta a una caché, y la
nota de una instancia no cambia de un minuto a otro.

La tabla completa de variables, incluidas las específicas de cada rol, está en
[`ansible/README.md`](../../ansible/README.md#variable-reference).

## Antes de confirmar un cambio en el rol {#before-you-commit-a-change-to-the-role}

`ansible-lint` solo da un resultado limpio cuando se ejecuta dentro de
`ansible/`; desde la raíz del repositorio informa de docenas de falsos
positivos.

```shell
cd ansible
ansible-lint
ansible-playbook -i inventory.ini playbooks/deploy_native.yml --syntax-check
```

---

[Volver al índice de la documentación](../README.md) | [Volver al README principal](../../README.md)
