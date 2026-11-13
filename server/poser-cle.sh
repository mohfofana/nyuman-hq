#!/bin/sh
# Pose la clé des chiffres de l'app dans server/.env, sans l'afficher. À lancer par Mohamed ou Kevin.
cd "$(dirname "$0")" && python3 -c "
import getpass, re, pathlib
k = getpass.getpass('Collez la clé (elle reste invisible), puis appuyez sur Entrée : ').strip()
p = pathlib.Path('.env')
p.write_text(re.sub(r'(?m)^HQ_STATS_KEY=.*$', lambda m: 'HQ_STATS_KEY=' + k, p.read_text()))
print('Clé posée. Vous pouvez fermer cette fenêtre et prévenir Kwame.' if k else 'Rien collé : relancez.')
"
