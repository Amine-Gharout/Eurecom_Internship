# Architecture Technique : Déploiement UERANSIM eBPF

**BLUF :** Ce document déconstruit la configuration `docker-compose-ueransim-ebpf.yaml`. Il explique comment le simulateur de réseau radio (RAN) contourne les goulots d'étranglement du noyau standard via eBPF, et comment il s'intègre au système hôte pour permettre le routage du trafic d'application réel, une condition stricte pour extraire des métriques de latence fiables pour un pipeline d'apprentissage par renforcement.

---

## 1. Le Service Principal : `ueransim`
Ce bloc définit le conteneur unique qui simule à la fois le gNodeB (l'antenne) et l'UE (le smartphone).

* **`image: oaisoftwarealliance/ueransim:...`** : Spécifie l'image Docker pré-compilée contenant les binaires C++ de UERANSIM.
* **`privileged: true` / `cap_add: - NET_ADMIN`** : Commandes critiques. Elles accordent au conteneur les droits d'administration sur le sous-système réseau du noyau de la machine hôte. Sans cela, le conteneur ne peut pas créer l'interface virtuelle (`uesimtun0`) sur Pop!_OS.
* **`devices: - /dev/net/tun:/dev/net/tun`** : Mappe le périphérique de tunnel réseau de l'hôte à l'intérieur du conteneur. C'est le pont matériel qui permet au trafic IP standard d'être encapsulé dans des paquets 5G.
* **`environment:`** :
    * `USE_EBPF=true` : Active le traitement des paquets via eBPF (Extended Berkeley Packet Filter). Cela permet d'exécuter le code de routage directement dans l'espace noyau à haute vitesse, évitant la surcharge CPU de l'espace utilisateur. Cela garantit que les baisses de débit mesurées par l'agent RL proviennent de la 5G, et non d'une surcharge du CPU local.
    * `MCC`, `MNC`, `SST`, `SD` : Identifiants cryptographiques (Mobile Country Code, Network Code, Slice/Service Type). Ils doivent correspondre exactement à la configuration de l'AMF et du SMF pour que la connexion N1/N2 soit autorisée.

## 2. Déclaration des Réseaux (Networks)
Le conteneur doit se connecter à deux réseaux distincts gérés par le cœur 5G.

* **`demo-oai-public-net`** : Le réseau de gestion et du Control Plane. UERANSIM l'utilise pour envoyer des requêtes d'authentification (N1/N2) à l'AMF.
* **`demo-oai-n3-net`** : Le réseau haut débit du Data Plane. UERANSIM l'utilise pour envoyer le trafic utilisateur brut (N3) directement à l'UPF eBPF. 

*Note : Ces réseaux portent la balise `external: true`, ce qui signifie que ce fichier Docker Compose ne les créera pas. Ils doivent déjà exister (déployés par le cœur OAI) avant le lancement de ce fichier.*

## 3. Gestion des Volumes
* **`volumes: - ./config:/openair-ueransim/config`** : Injecte les fichiers de configuration locaux (YAML ou JSON) dans le conteneur. Cela permet de modifier l'adresse IP de destination de l'AMF ou de l'UPF sans avoir à recompiler l'image Docker UERANSIM complète.

## 4. Dépendances (`depends_on`)
Si cette section est présente, elle indique au moteur Docker d'attendre que des conteneurs spécifiques (comme `oai-amf` ou `oai-upf`) soient marqués comme "sains" (healthy) avant de tenter de démarrer le simulateur radio. Cela évite que UERANSIM ne sature le réseau avec des requêtes de connexion avant que le cœur ne soit prêt à les traiter.