# ONE Pocket for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/pikipixel/hass-one-pocket)](https://github.com/pikipixel/hass-one-pocket/releases)
[![License: MIT](https://img.shields.io/github/license/pikipixel/hass-one-pocket)](LICENSE)

Integration Home Assistant pour [ONE Pocket](https://edifice.io/nos-produits/one/one-pocket/) (Edifice), l'espace numerique de travail (ENT) utilise dans les ecoles primaires francaises.

## Fonctionnalites

| Capteur | Description |
|---------|-------------|
| **Messages non lus** | Nombre de messages non lus + liste des derniers messages |
| **Devoirs** | Cahier de textes avec contenu des devoirs |
| **Actualites** | Publications de l'ecole (fil d'actualites) |
| **Blog** | Articles des blogs de classe |
| **Carnet de liaison** | Communications ecole-famille |
| **Notifications** | Timeline des notifications ONE Pocket |

Chaque capteur expose les donnees detaillees dans ses attributs, utilisables dans des cartes Lovelace et des automations.

## Installation

### HACS (recommande)

1. Ouvrir HACS dans Home Assistant
2. Cliquer sur **Integrations** > **+ Explorer et telecharger des depots**
3. Rechercher **"ONE Pocket"**
4. Cliquer sur **Telecharger**
5. Redemarrer Home Assistant
6. Aller dans **Parametres** > **Appareils et services** > **Ajouter une integration** > **ONE Pocket**

### Installation manuelle

1. Copier le dossier `custom_components/one_pocket` dans votre repertoire `custom_components`
2. Redemarrer Home Assistant
3. Ajouter l'integration via l'interface

## Configuration

Lors de l'ajout de l'integration, vous aurez besoin de :

- **URL de l'instance ONE** : l'adresse de votre ENT (ex: `https://oneconnect.edifice.io`)
- **Identifiant** : votre login parent ONE Pocket
- **Mot de passe** : votre mot de passe parent ONE Pocket

Si votre compte parent est lie a plusieurs enfants, vous pourrez choisir l'enfant a suivre.

### Options

| Option | Defaut | Description |
|--------|--------|-------------|
| Intervalle de mise a jour | 15 min | Frequence de rafraichissement des donnees (5-60 min) |

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

Cette integration fonctionne avec toutes les instances ONE (Edifice) :
- `oneconnect.edifice.io`
- Instances academiques et departementales
- Toute plateforme utilisant le framework Edifice/entcore

## Credits

- API basee sur le framework open source [entcore](https://github.com/edificeio/entcore) par Edifice
- Inspire par [hass-pronote](https://github.com/delphiki/hass-pronote) et [hass-ecoledirecte](https://github.com/hacf-fr/hass-ecoledirecte)

## Licence

[MIT](LICENSE)
