# Planification sans Icinga2 / Nagios
Planifiez des scans réguliers avec un minuteur systemd ou avec cron lorsque vous
n'utilisez ni Icinga2 ni Nagios. Les exemples de [`contrib/`](../../contrib/)
fournissent des fichiers de service, de minuteur et d'environnement que vous
pouvez adapter à votre installation :

- [`contrib/systemd/check-opencloud-security.service`](../../contrib/systemd/check-opencloud-security.service)
  et [`.timer`](../../contrib/systemd/check-opencloud-security.timer)
- [`contrib/systemd/check-opencloud-security.env.example`](../../contrib/systemd/check-opencloud-security.env.example)

Le minuteur distinct
[`check-opencloud-security-refresh.timer`](../../contrib/systemd/check-opencloud-security-refresh.timer)
maintient à jour le calendrier des versions et la base d'avis de sécurité du
scanner. Configurez le scanner pour qu'il lise les deux fichiers sous
`/var/lib/check-opencloud-security` avant de l'activer ; la commande
d'actualisation valide les deux documents et les écrit de façon atomique.
- [`contrib/cron/check-opencloud-security.cron`](../../contrib/cron/check-opencloud-security.cron)

<!-- TOC -->
* [Planification sans Icinga2 / Nagios](#scheduling-without-icinga2--nagios)
  * [Minuteur systemd](#systemd-timer)
  * [cron](#cron)
<!-- TOC -->


## Minuteur systemd {#systemd-timer}
```shell
sudo mkdir -p /etc/check-opencloud-security
sudo cp contrib/systemd/check-opencloud-security.env.example /etc/check-opencloud-security/env
sudo $EDITOR /etc/check-opencloud-security/env   # set COS_HOST (and any other options)

sudo cp contrib/systemd/check-opencloud-security.service /etc/systemd/system/
sudo cp contrib/systemd/check-opencloud-security.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now check-opencloud-security.timer

# Run it once immediately to verify the setup:
sudo systemctl start check-opencloud-security.service
journalctl -u check-opencloud-security.service
```

## cron {#cron}
```shell
sudo cp contrib/cron/check-opencloud-security.cron /etc/cron.d/check-opencloud-security
sudo chmod 644 /etc/cron.d/check-opencloud-security
sudo $EDITOR /etc/cron.d/check-opencloud-security   # set COS_HOST (and any other options)
```

Les deux exemples configurent le contrôle entièrement au moyen de
[variables d'environnement](reference.md#environment-variables), si bien que le
même binaire ou la même image Docker est réutilisé tel quel d'un hôte à l'autre -
seuls le fichier d'environnement ou l'entrée cron changent.

Deux pièges reviennent souvent ici, et tous deux sont traités dans
[Dépannage](troubleshooting.md) : cron et systemd n'ont ni le `PATH` ni
l'environnement d'un shell de connexion ; utilisez donc le chemin complet vers
`check-opencloud-security` et définissez `COS_HOST` explicitement.

Sur un cluster, l'équivalent est un `CronJob` - voir
[Kubernetes](kubernetes.md). Pour plus de quelques instances, voir
[Contrôler un parc d'instances](many-instances.md).

---

[Retour à l'index de la documentation](../README.md) | [Retour au README principal](../../README.md)
