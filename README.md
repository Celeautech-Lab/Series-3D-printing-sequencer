# Series-3D-printing-sequencer

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Interface](https://img.shields.io/badge/interface-Tkinter-2E8B57)](https://docs.python.org/3/library/tkinter.html)
[![Licence](https://img.shields.io/badge/licence-PolyForm_Noncommercial-orange.svg)](LICENSE)

Application de bureau en Python/Tkinter qui assemble une série d'impressions à partir de plusieurs fichiers G-code. Elle conserve le **Header** du premier fichier, enchaîne les **Body** dans l'ordre et le nombre demandés, insère une transition/éjection entre chaque pièce, puis conserve le **Footer** du dernier fichier.

> **Dépôt :** [github.com/Celeautech/Series-3D-printing-sequencer](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer)

## Fonctionnement général

L'application parcourt un dossier, vérifie les marqueurs de chaque fichier G-code, lit éventuellement `serie.csv`, affiche la séquence dans une table modifiable et génère un fichier G-code compilé.

### Header, Body et Footer

Chaque fichier source doit avoir exactement un marqueur de début et un marqueur de fin :

```gcode
; BODYSTART
; ... commandes d'impression de la pièce ...
; BODYEND
```

Le compositeur découpe alors chaque fichier en trois zones :

- **Header** : tout ce qui précède `; BODYSTART` — démarrage, chauffage, homing, etc. ;
- **Body** : tout ce qui se trouve entre `; BODYSTART` et `; BODYEND` — le parcours de la pièce ;
- **Footer** : tout ce qui suit `; BODYEND` — refroidissement ou fin de programme.

Dans le fichier final, le Header du premier fichier développé est écrit une seule fois, les Body sont concaténés dans l'ordre, et le Footer du dernier fichier développé est écrit une seule fois. Une séquence d'éjection/transition est insérée **après chaque pièce imprimée, y compris après la toute dernière**. Cette règle permet de libérer également la dernière pièce ; il faut donc prévoir un refroidissement ou une attente dans la transition si le procédé l'exige.

### Exemple exact : 7 cycles

Le plan suivant est utilisé :

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

Un cycle contient donc :

```text
4 × PART_1.gcode + 5 × PART_2.gcode + 6 × PART_3.gcode = 15 pièces
```

Le fichier produit suit cette séquence :

```text
1 chauffage initial / homing (Header)
Cycle 1 : 4 × PART_1 + 5 × PART_2 + 6 × PART_3, avec une éjection après chaque pièce
Cycle 2 : 4 × PART_1 + 5 × PART_2 + 6 × PART_3, avec une éjection après chaque pièce
...
Cycle 7 : 4 × PART_1 + 5 × PART_2 + 6 × PART_3, avec une éjection après chaque pièce
1 refroidissement final (Footer)
```

Le résultat est de **7 cycles de [4 × PART_1 + 5 × PART_2 + 6 × PART_3] = 105 pièces et 105 éjections**, suivis d'un refroidissement final. Le Header global est celui de la première pièce développée et le Footer global celui de la dernière. La dernière éjection est bien présente avant le Footer.

> Le compteur d'occurrences est le nombre d'exemplaires d'une ligne dans chaque cycle. Une occurrence à `0` exclut la ligne ; si toutes les occurrences valent `0`, la génération est refusée.

## Installation et lancement

Le projet utilise Python et la bibliothèque standard, notamment Tkinter :

```bash
git clone https://github.com/Celeautech/Series-3D-printing-sequencer.git
cd Series-3D-printing-sequencer
python main.py
```

Sous Debian/Ubuntu, installer Tkinter si nécessaire :

```bash
sudo apt install python3-tk
```

L'application démarre depuis `main.py` et ouvre l'interface graphique.

## Préparer les fichiers G-code avec le slicer

### Marqueurs requis

Dans le G-code exporté, les lignes suivantes délimitent le Body :

```gcode
; BODYSTART
...
; BODYEND
```

Le validateur travaille ligne par ligne après suppression des espaces extérieurs. Une ligne est acceptée si elle **commence** par le marqueur ; elle peut donc contenir un commentaire complémentaire après celui-ci. Chaque fichier doit contenir un seul `; BODYSTART` et un seul `; BODYEND`, dans cet ordre.

### PrusaSlicer

1. Ouvrir **Printer Settings → Custom G-code**.
2. Ajouter `; BODYSTART` au début du **Start G-code** de la pièce, après les commandes communes de chauffage/homing si celles-ci doivent rester dans le Header.
3. Ajouter `; BODYEND` dans l'**End G-code** de la pièce, avant les commandes qui doivent constituer le Footer.
4. Trancher puis exporter chaque pièce en `.gcode`.

Pour une série, vérifier dans un fichier exporté que les deux commentaires sont présents une seule fois et que le prochain fichier commence avec les mêmes hypothèses de positionnement et d'extrusion.

### OrcaSlicer

1. Aller dans **Printer → Machine start G-code** pour les commandes communes et dans les réglages de **Printer / Process → Custom G-code** selon la version.
2. Placer `; BODYSTART` au point où commence réellement le parcours de la pièce.
3. Placer `; BODYEND` immédiatement après le dernier mouvement propre à la pièce et avant le Footer.
4. Exporter les fichiers et inspecter le texte produit : les noms des menus peuvent varier selon la version et le profil.

### Bambu Studio

1. Ouvrir le profil imprimante et les champs de G-code personnalisé accessibles dans **Machine start G-code** et **Machine end G-code** (ou **Printer settings**, selon la version).
2. Ajouter `; BODYSTART` et `; BODYEND` dans les emplacements personnalisés qui encadrent les commandes propres à la pièce.
3. Vérifier le fichier `.gcode` exporté, car Bambu Studio peut ajouter des commandes machine avant et après les commandes personnalisées.

Si le profil Bambu ne permet pas de placer proprement les deux marqueurs autour du seul Body, ne pas utiliser le fichier tel quel : l'import affichera l'erreur de structure correspondante.

### Cura

1. Ouvrir **Settings → Printer → Manage Printers → Machine Settings**.
2. Utiliser les zones **Start G-code** et **End G-code** pour placer les marqueurs au début et à la fin de la zone à séquencer.
3. Exporter le fichier et rechercher `; BODYSTART` puis `; BODYEND` dans un éditeur texte.

Dans tous les slicers, les marqueurs sont des commentaires : ils ne déplacent pas la machine. Ils servent uniquement de contrat de découpage pour le séquenceur.

## Configuration du Firmware & Prérequis Matériels (Klipper / Marlin / RepRapFirmware)

Cette application ne peut pas deviner la cinématique du tapis, les broches, les fins de course, les limites de course ni la méthode de poussée de votre imprimante. Le fichier d'éjection dépend du matériel et du firmware. Comme aucun tapis roulant réel n'est disponible ici pour tester une éjection déterminée, le dépôt ne fournit pas de fichier d'éjection universel non testé : il faut configurer et valider la transition sur la machine cible.

Avant une longue série, tester la transition à vide, buse dégagée, à faible vitesse et avec un arrêt d'urgence accessible. Les exemples ci-dessous sont des patrons à adapter ; ils ne constituent pas des commandes prêtes à l'emploi pour toutes les cartes.

### Extrudeur entre deux pièces : `M82`, `M83` et `G92 E0`

- `M82` sélectionne l'extrusion **absolue** : la valeur `E` s'accumule pendant le fichier ;
- `M83` sélectionne l'extrusion **relative** : chaque valeur `E` est un déplacement relatif ;
- `G92 E0` remet à zéro la position logique de l'extrudeur sans pousser ni rétracter de filament.

À la frontière entre deux Body, placer `G92 E0` à un endroit cohérent avec le slicer, typiquement en fin de transition ou au début du Body suivant. C'est indispensable lorsque le slicer travaille en absolu : sans ce reset, un fichier qui termine à `E2450` peut faire interpréter la prochaine petite valeur comme une énorme rétraction ou une avance excessive. Vérifier les premiers et derniers mouvements `E` des fichiers sources et conserver une politique cohérente.

Exemple de principe :

```gcode
; fin du Body précédent / transition
G92 E0
; séquence d'éjection validée sur la machine
; avant le prochain Body
G90
M82                 ; ou M83, exactement selon le G-code du slicer
G92 E0              ; si le début du Body l'exige
```

Ne pas ajouter aveuglément `M82` ou `M83` : le mode final doit être celui attendu par le prochain fichier.

### Positionnement absolu : `G90` et relatif : `G91`

`G90` active le positionnement absolu des axes et `G91` le positionnement relatif. Une éjection utilise souvent `G91` pour lever la buse d'une distance contrôlée, puis `G90` pour une position ou un balayage absolu. Le G-code de transition doit **toujours terminer en `G90`**, et remettre aussi `M82` ou `M83` dans le mode attendu avant que le Body suivant commence :

```gcode
M400
G91
G1 Z15 F600
G90                 ; obligatoire avant le Body suivant
G92 E0
M82                 ; ou M83 selon le slicer
```

Laisser la machine en `G91` peut décaler toutes les coordonnées du Body suivant et provoquer une collision.

### Pilotage d'un tapis roulant ou d'un axe auxiliaire

Le tapis doit avoir une direction, une distance, une vitesse, une butée et une zone de sécurité validées. Il est préférable d'appeler une macro dédiée plutôt que d'insérer dans chaque fichier une séquence dépendante de la carte.

#### Klipper

Configurer dans `printer.cfg` un `[manual_stepper belt]` correctement calibré, ou une macro G-code dédiée. La transition peut appeler :

```gcode
EJECT_PART
G92 E0
G90
M82                 ; ou M83, selon le slicer
```

La macro `EJECT_PART` doit contenir les mouvements autorisés, les attentes, les limites et, si nécessaire, les fins de course. Avec un `manual_stepper`, le principe peut être :

```gcode
MANUAL_STEPPER STEPPER=belt MOVE=400 SPEED=50
```

Cette commande n'est valide que si le bloc `[manual_stepper belt]` et ses paramètres existent réellement dans `printer.cfg`. Tester la macro seule avant de l'appeler depuis la série.

#### Marlin

Marlin peut utiliser un axe secondaire configuré (`U`, `V` ou `W`), un second extrudeur `T1` configuré sans chauffe, ou une broche GPIO. Pour un extrudeur utilisé comme axe mécanique, la protection d'extrusion à froid doit être traitée conformément à la configuration de la carte ; `M302 S0` désactive l'extrusion à froid et ne doit être employé que si cette fonction est réellement nécessaire et sûre. Une broche peut être pilotée avec `M42` si le pin et ses niveaux ont été documentés.

```gcode
; Exemple conceptuel : axe U/V/W, T1 ou macro définie dans Marlin
; EJECT_PART
; ou commande d'axe configurée par le firmware
M42 P<pin> S<0-ou-1>  ; seulement après validation du pin et du niveau
G92 E0
G90
```

Ne pas supposer que `MANUAL_STEPPER` existe sous Marlin. La commande exacte dépend de la version, de la carte et de `Configuration.h`/`Configuration_adv.h`.

#### RepRapFirmware (Duet)

Définir l'axe linéaire supplémentaire et son driver dans `config.g`, avec ses pas/mm, limites, sens et fins de course. Une macro système peut ensuite être appelée depuis la transition :

```gcode
M98 P"eject.g"
G92 E0
G90
```

Le chemin peut être par exemple `0:/sys/macros/eject.g` selon l'installation. Le fichier macro et l'axe doivent être validés manuellement sur la Duet ; le nom du driver et la syntaxe peuvent varier avec la configuration.

### Alternative sans tapis : éjection par poussée du portique

Sur une CoreXY ou une cartésienne standard équipée d'un pousse-pièce, lever la buse, attendre si nécessaire le refroidissement du plateau, puis effectuer un balayage XY calibré :

```gcode
M400
G91
G1 Z15 F600
G90
M190 R30           ; attendre environ 30 °C si le procédé le nécessite
; balayage/poussée XY calibré ici
G92 E0
G90
M190 S<temperature_plateau> ; remettre en chauffe pour la pièce suivante
M109 S<temperature_buse>    ; si le procédé l'exige
```

`M190 R30` est seulement un exemple : choisir une température adaptée au matériau. Après l'éjection, maintenir ou remettre en chauffe le plateau (`M190 S...`) et la buse (`M109 S...`) avant la pièce suivante. Contrôler les limites, clips, sonde, câbles, nozzle et position réelle de la pièce ; ne jamais copier des coordonnées de balayage sans les mesurer.

### Moteurs actifs, homing et temps d'inactivité

Il est **interdit** de mettre `M84` ou `M18` dans le G-code de transition : désactiver les moteurs peut faire perdre des pas et la référence entre deux pièces. Sous Klipper, régler `[idle_timeout]` pour qu'un refroidissement ou une longue éjection ne coupe pas inopinément les moteurs ; examiner aussi le comportement équivalent du firmware utilisé.

Après une éjection mécanique, il est possible d'ajouter, si la machine le permet et si la zone est dégagée :

```gcode
G28 X Y
G90
G92 E0
```

`G28 X Y` est optionnel et dépend de la machine. Il peut corriger une perte de pas, mais ne remplace ni le réglage mécanique ni le test de la transition. Un homing complet peut déplacer des mécanismes différemment : ne l'utiliser que si sa sécurité est connue.

### Contrôle avant production

Vérifier que :

1. la transition finit en `G90` et dans le bon mode `M82`/`M83` ;
2. `G92 E0` est placé à une frontière sûre ;
3. le tapis ou le balayage possède des limites, une vitesse et un arrêt fiables ;
4. aucun `M84`/`M18` ne désactive les moteurs et le timeout ne coupe pas le mouvement ;
5. le fichier final contient le nombre attendu de Body, de transitions et d'éjections, y compris la dernière.

## Importer un dossier dans l'application

1. Lancer `python main.py`.
2. Cliquer sur **Select folder** (ou le bouton de sélection de dossier affiché par l'interface).
3. Choisir le dossier qui contient les fichiers `.gcode`, `.gco` ou `.g`.
4. L'application ne parcourt que ce dossier, pas ses sous-dossiers ; les autres extensions sont ignorées.
5. Les fichiers valides apparaissent dans la table. Les fichiers invalides sont exclus de la séquence.
6. Si un problème est détecté, la fenêtre modale **`Validation report`** s'ouvre. Cliquer sur **OK** pour conserver les fichiers valides et poursuivre.
7. Vérifier les occurrences, l'ordre, le nombre de cycles et le G-code de transition dans les paramètres avant de générer.

Si aucun G-code pris en charge n'est trouvé, l'application affiche une erreur `No G-code files found in:` et vide la sélection du dossier.

## Créer ou modifier `serie.csv`

### Depuis l'interface

Après avoir importé un dossier :

1. Modifier le nombre de cycles dans le champ correspondant.
2. Modifier une occurrence directement dans la table (double-clic ou contrôle numérique selon la version de l'interface).
3. Réordonner les lignes par glisser-déposer si nécessaire.
4. Utiliser **Save series** pour écrire `serie.csv` dans le dossier choisi.

Le fichier peut aussi être créé automatiquement par l'interface à partir des lignes visibles. Lors de l'édition dans la table, la valeur est limitée à `0`–`999` et une valeur négative saisie dans l'interface est ramenée à `0`. Lors de la lecture d'un CSV, en revanche, toute occurrence entière `>= 0` est acceptée (il n'y a pas de plafond à `999`) et une valeur négative provoque une erreur de format.

### Avec Excel ou un éditeur de texte

Créer un fichier nommé exactement `serie.csv`, encodé en UTF-8, avec la structure exacte suivante : une ligne `Cycles,<nombre>`, puis l'en-tête `Rank,Filename,Occurrences`, puis une ligne par fichier.

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

`Cycles,7` signifie sept passages du plan. Les lignes suivantes signifient respectivement 4, 5 et 6 exemplaires par cycle. Le parseur exige l'en-tête de la deuxième ligne ; un fichier sans cette ligne, comme une simple succession de lignes de données après `Cycles,7`, est invalide. Les noms doivent correspondre exactement aux fichiers présents dans le dossier importé.

Le parseur lit les deux premières colonnes de la ligne `Cycles` et les trois premières colonnes de l'en-tête et des données. Il accepte un BOM UTF-8 et ignore les lignes entièrement vides. Les rangs sont numériques et sont triés avant la composition. Le nombre de cycles doit être un entier supérieur ou égal à `1`, et les occurrences doivent être des entiers supérieurs ou égaux à `0`.

**Enregistrement depuis l'interface.** Le bouton **Save series** crée ou écrase `serie.csv` dans le dossier sélectionné (ou dans un dossier choisi si aucun dossier n'est chargé). Il écrit la même structure, avec une virgule finale vide sur la première ligne : `Cycles,7,`. Cette virgule est acceptée par le parseur ; pour le format exact demandé ci-dessus, supprimer cette dernière virgule dans un éditeur de texte après l'enregistrement.

## Règles de composition du G-code

Pour le plan développé (cycles × lignes × occurrences), le fichier final prend cette forme logique :

```text
Header du premier fichier
; BODYSTART
Body de la pièce 1
transition / éjection après la pièce 1
Body de la pièce 2
...
Body de la dernière pièce
transition / éjection après la dernière pièce
; BODYEND
Footer du dernier fichier
```

La transition est donc insérée **entre les Body et après le dernier Body**. Le bloc est stocké en ligne dans `settings.json`, sous la clé `transition_gcode`, et est modifiable depuis la fenêtre des paramètres. Il n'existe pas de recherche d'un fichier d'éjection séparé dans l'implémentation actuelle.

Un exemple intégré peut ressembler à ceci, mais il doit être remplacé ou adapté à la machine :

```gcode
; --- TRANSITION A ADAPTER ---
M400
G91
G1 Z15 F600
G90
EJECT_PART
G92 E0
; --- FIN TRANSITION ---
```

Ne pas envoyer cet exemple sans avoir défini `EJECT_PART` et vérifié toute la cinématique.

## Erreurs et dépannage

### Fenêtre modale `Validation report`

Lors de l'import d'un dossier, la fenêtre **`Validation report`** peut s'ouvrir dès qu'un fichier contient un problème de marqueur ou que `serie.csv` comporte une erreur. C'est un rapport informatif : cliquer sur **OK** ne supprime pas les fichiers valides et n'annule pas l'import. Le rapport indique les fichiers exclus et la cause exacte.

Causes de validation courantes :

- `BODYSTART and BODYEND tags missing` : aucun des deux marqueurs n'est trouvé ;
- `BODYSTART tag missing` : le début manque ;
- `BODYEND tag missing` : la fin manque ;
- `BODYSTART tag duplicated` ou `BODYEND tag duplicated` : marqueur répété ;
- `tag order reversed (BODYEND before BODYSTART)` : ordre inversé ;
- `read failed (...)` : fichier impossible à lire.

Un fichier vide est signalé comme dépourvu des deux tags. Le validateur ne vérifie pas la validité sémantique de chaque commande G-code, les températures, les limites mécaniques ni la sécurité de l'éjection.

### Erreurs CSV

Vérifier le nom exact `serie.csv`, l'encodage UTF-8, la première ligne `Cycles,7`, les rangs numériques, les noms de fichiers et les occurrences. Le rapport peut afficher notamment :

```text
CSV must have at least 2 rows (Cycles header and data header)
Row 1: Must start with 'Cycles'
Row 1: Cycles value is not an integer
Row 2: Headers must be 'Rank,Filename,Occurrences'
Row N: Must contain 3 columns
Row N: Filename is empty
Row N: Rank is not an integer
Row N: Occurrences is not an integer
Row N: Occurrences must be >= 0
```

Si une ligne du CSV référence un fichier absent ou invalide, elle est listée dans le même `Validation report`. En cas de CSV illisible ou mal formé, l'import affiche l'erreur puis remplit la table avec les fichiers G-code valides détectés ; les fichiers non listés dans un CSV valide ont alors `0` occurrence, et le champ des cycles conserve sa valeur courante (initialement `1`).

L'absence de `serie.csv` n'est pas une erreur : l'application peut utiliser les fichiers valides découverts dans le dossier.

### Erreurs de génération et d'enregistrement

| Situation | Message attendu |
|---|---|
| Aucun fichier valide chargé | `No file selected` |
| Cycles non entier | `Invalid cycles value` |
| Toutes les occurrences à zéro | `No parts selected (all occurrences are 0)` |
| Échec de composition | `G-code composition failed:` suivi du détail |
| Échec d'écriture | `Save failed:` suivi de l'erreur système |
| Échec d'enregistrement de la série | `Series save failed:` suivi du détail |

Si aucun fichier G-code n'est trouvé, vérifier l'extension et le dossier sélectionné. Si la composition échoue, rouvrir le rapport, corriger les marqueurs, les noms CSV et les occurrences, puis réimporter le dossier. Avant d'imprimer, ouvrir le fichier généré et compter les `; BODYSTART`, `; BODYEND`, transitions et commandes d'éjection attendues.

## Checklist avant génération

1. Chaque fichier prévu possède exactement un `; BODYSTART` et un `; BODYEND` dans le bon ordre.
2. Le dossier importé ne contient pas d'anciens G-code involontairement sélectionnés.
3. `serie.csv` contient les bons cycles, noms, rangs et occurrences.
4. La transition a été adaptée au firmware et au matériel réels.
5. `G92 E0`, `G90`, `M82`/`M83`, les températures, les limites et les moteurs actifs ont été vérifiés.
6. La dernière pièce est bien éjectée avant le Footer/refroidissement final.
7. Le fichier généré a été inspecté et testé avec les procédures de sécurité habituelles de l'imprimante.

L'application valide la structure des marqueurs, les références de fichiers et le plan de série. Elle ne valide pas la compatibilité machine, la signification des commandes G-code, les limites de déplacement, les températures, les vitesses ni la sécurité physique.

## Licence & Usage Commercial

Ce projet est sous licence **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

- **Usage personnel / hobby / éducation :** Libre et encouragé.
- **Usage commercial & dérivés :** Strictement interdit sans accord explicite préalable.

Pour toute demande de licence commerciale, intégration produit ou partenariat :  
**Contact :** Antoine Navarro EI — [celeautech.contact@gmail.com](mailto:celeautech.contact@gmail.com)