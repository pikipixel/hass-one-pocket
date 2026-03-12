# ONE Pocket for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/pikipixel/hass-one-pocket)](https://github.com/pikipixel/hass-one-pocket/releases)
[![License: MIT](https://img.shields.io/github/license/pikipixel/hass-one-pocket)](LICENSE)

Intégration Home Assistant pour [ONE Pocket](https://edifice.io/nos-produits/one/one-pocket/) (Edifice), l'espace numérique de travail (ENT) utilisé dans les écoles primaires françaises.

## Fonctionnalités

| Capteur | Description |
|---------|-------------|
| **Messages non lus** | Nombre de messages non lus + liste des derniers messages |
| **Devoirs** | Cahier de textes avec contenu des devoirs |
| **Actualités** | Publications de l'école (fil d'actualités) |
| **Blog** | Articles des blogs de classe |
| **Carnet de liaison** | Communications école-famille |
| **Notifications** | Timeline des notifications ONE Pocket |

Chaque capteur expose les données détaillées dans ses attributs, utilisables dans des cartes Lovelace et des automations.

## Installation

### HACS (recommandé)

1. Ouvrir HACS dans Home Assistant
2. Cliquer sur **Intégrations** > **+ Explorer et télécharger des dépôts**
3. Rechercher **"ONE Pocket"**
4. Cliquer sur **Télécharger**
5. Redémarrer Home Assistant
6. Aller dans **Paramètres** > **Appareils et services** > **Ajouter une intégration** > **ONE Pocket**

### Installation manuelle

1. Copier le dossier `custom_components/one_pocket` dans votre répertoire `custom_components`
2. Redémarrer Home Assistant
3. Ajouter l'intégration via l'interface

## Configuration

Lors de l'ajout de l'intégration, vous aurez besoin de :

- **URL de l'instance ONE** : l'adresse de votre ENT (ex: `https://oneconnect.edifice.io`)
- **Identifiant** : votre login parent ONE Pocket
- **Mot de passe** : votre mot de passe parent ONE Pocket

Si votre compte parent est lié à plusieurs enfants, vous pourrez choisir l'enfant à suivre.

### Options

| Option | Défaut | Description |
|--------|--------|-------------|
| Intervalle de mise à jour | 15 min | Fréquence de rafraîchissement des données (5-60 min) |

## Exemples d'utilisation

### Automation : notification nouveau message

```yaml
automation:
  - alias: "ONE Pocket - Nouveau message"
    triggers:
      - trigger: state
        entity_id: sensor.one_pocket_mon_enfant_messages_non_lus
    conditions:
      - condition: template
        value_template: >-
          {{ trigger.to_state.state | int(0) > trigger.from_state.state | int(0) }}
    actions:
      - action: notify.mobile_app_mon_telephone
        data:
          title: "ONE Pocket - Nouveau message"
          message: >-
            {% set messages = state_attr('sensor.one_pocket_mon_enfant_messages_non_lus', 'messages') %}
            {% if messages and messages | length > 0 %}
            De {{ messages[0].from }} : {{ messages[0].subject }}
            {% endif %}
```

### Carte Lovelace : devoirs

```yaml
type: markdown
content: >-
  {% set entries = state_attr('sensor.one_pocket_mon_enfant_devoirs', 'entries') %}
  {% if entries %}
    {% for hw in entries %}
  **{{ hw.date }}** — _{{ hw.title }}_ : {{ hw.content | truncate(150) }}
    {% endfor %}
  {% else %}
  Aucun devoir
  {% endif %}
```

## Plateformes ONE compatibles

Cette intégration fonctionne avec toutes les instances ONE (Edifice) :
- `oneconnect.edifice.io`
- Instances académiques et départementales
- Toute plateforme utilisant le framework Edifice/entcore

## Crédits

- API basée sur le framework open source [entcore](https://github.com/edificeio/entcore) par Edifice
- Inspiré par [hass-pronote](https://github.com/delphiki/hass-pronote) et [hass-ecoledirecte](https://github.com/hacf-fr/hass-ecoledirecte)

## Licence

[MIT](LICENSE)
