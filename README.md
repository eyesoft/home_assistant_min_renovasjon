# Min Renovasjon

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant integration of the norwegian Min Renovasjon app.

## Installation
Under HACS -> Integrations, add custom repository "https://github.com/eyesoft/home_assistant_min_renovasjon/" with Category "Integration". 

Search for repository "Min Renovasjon" and download it. 

Go to Settings > Integrations and Add Integration "Min Renovasjon". Type in address to search, e.g. "Min gate 12, 0153" (street address comma zipcode).
Click Configure and choose fractions to create sensors.

Restart Home Assistant.

## Upgrade from version pre 2.0.0
Install component and configure it as described under Installation. 

If everything work as before after the restart, the old integration "min_renovasjon" and sensor "min_renovasjon" can be deleted from configuration.yaml
