# hass-one-pocket

Custom Home Assistant integration for [ONE Pocket](https://oneconnect.edifice.io/) (Edifice), the digital workspace used in French primary schools.

## Features (planned)

- Messages (messagerie)
- Homework (cahier de textes)
- School-home notebook (carnet de liaison)
- News feed (actualités)
- Blog posts

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS
2. Install "ONE Pocket"
3. Restart Home Assistant
4. Add the integration via Settings > Integrations

### Manual

Copy `custom_components/one_pocket` to your Home Assistant `custom_components` directory.

## Configuration

You will need:
- Your school's ONE instance URL
- Parent login credentials
