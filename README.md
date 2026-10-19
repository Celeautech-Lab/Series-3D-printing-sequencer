# Series-3D-printing-sequencer

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Interface](https://img.shields.io/badge/interface-Tkinter-2E8B57)](https://docs.python.org/3/library/tkinter.html)
[![Licence](https://img.shields.io/badge/licence-PolyForm_Noncommercial-orange.svg)](LICENSE)

> **Générateur de séries G-code pour l'impression 3D** — prépare une séquence de pièces à partir de plusieurs fichiers, avec une transition configurable entre deux pièces.

Application de bureau Python/Tkinter. Elle importe un dossier de fichiers G-code, valide leurs marqueurs, permet d'ordonner les fichiers et de définir le nombre d'occurrences par cycle, puis exporte un fichier G-code composé. Le projet ne choisit pas une stratégie d'éjection universelle : le bloc de transition doit être adapté et validé sur la machine cible.

> **Dépôt :** [github.com/Celeautech-Lab/Series-3D-printing-sequencer](https://github.com/Celeautech-Lab/Series-3D-printing-sequencer)

## En bref

- Import d'un dossier et détection des extensions `.gcode`, `.gco` et `.g`.
- Validation des marqueurs `; BODYSTART` / `; BODYEND`.
- Table graphique réordonnable, édition des occurrences et nombre de cycles.
- Import et export optionnels de `serie.csv`.
- Composition : en-tête du premier fichier, corps concaténés, transition après chaque pièce, pied de page du dernier fichier.
- Transition G-code éditable dans l'interface et persistée dans `settings.json`.
- Export manuel du fichier compilé, par défaut nommé `serie.gcode`.

## Fonctionnement exact

Chaque fichier source doit contenir exactement un marqueur de début et un marqueur de fin :

```gcode
; BODYSTART
; ... commandes d'impression de la pièce ...
; BODYEND
```

Le composeur sépare alors :

- **En-tête** : toutes les lignes avant `; BODYSTART` ;
- **Corps** : les lignes entre les deux marqueurs, marqueurs exclus ;
- **Pied de page** : toutes les lignes après `; BODYEND`.

Dans le fichier final, l'en-tête du premier fichier effectivement imprimé est écrit une seule fois, puis `; BODYSTART`, les corps dans l'ordre choisi et le nombre demandé, et enfin `; BODYEND` suivi du pied de page du dernier fichier effectivement imprimé. La transition est insérée **après chaque corps, y compris le dernier**, avant le pied de page final.

### Exemple de plan

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

Un cycle contient `4 + 5 + 6 = 15` pièces. Sept cycles produisent donc 105 pièces et 105 transitions, si tous les fichiers sont valides et si la composition aboutit. Une occurrence égale à `0` exclut la ligne ; si toutes les occurrences valent `0`, la génération est refusée.

## Installation et lancement depuis les sources

Le projet utilise Python et la bibliothèque standard, notamment Tkinter.

```bash
git clone https://github.com/Celeautech-Lab/Series-3D-printing-sequencer.git
cd Series-3D-printing-sequencer
python src/main.py
```

Sous Debian/Ubuntu, installer Tkinter si nécessaire :

```bash
sudo apt install python3-tk
```

Le point d'entrée du paquet est `src/main.py`. Le script prend aussi en charge l'import direct depuis le répertoire `src`.

## Générer un exécutable

`build_exe.py` prépare un build PyInstaller depuis la racine du dépôt. PyInstaller doit être installé dans l'environnement utilisé :

```bash
python -m pip install pyinstaller
python build_exe.py --asset PrintSeriesGenerator-Linux-x64
```

Sans `--asset`, le nom par défaut dépend de la plateforme :

- Windows : `PrintSeriesGenerator-Windows-x64.exe` ;
- Linux : `PrintSeriesGenerator-Linux-x64` ;
- macOS : `PrintSeriesGenerator-macOS-AppleSilicon`, empaqueté dans une archive `.tar.gz`.

Le script supprime les répertoires `build/` et `dist/` précédents, utilise `--onefile` sur Windows/Linux et `--onedir` sur macOS, puis supprime le répertoire intermédiaire `build/`. Le fichier `src/settings.json` est inclus dans le bundle. Une application compilée lit et écrit ses réglages persistants à côté de l'exécutable ; une exécution depuis les sources utilise `src/settings.json`.

Cette description reflète la configuration du dépôt et du script de build ; elle ne constitue pas une validation d'exécution ou de compatibilité sur chaque plateforme.

## Préparer les fichiers G-code

### Marqueurs obligatoires

Le validateur lit les fichiers en UTF-8 avec remplacement des erreurs de décodage et compare les lignes après suppression des espaces en début et fin. Une ligne doit donc être exactement `; BODYSTART` ou `; BODYEND` après ce nettoyage. Contrairement à une recherche de sous-chaîne, un commentaire supplémentaire sur la même ligne n'est pas accepté par le validateur actuel.

Chaque fichier doit avoir :

1. un seul `; BODYSTART` ;
2. un seul `; BODYEND` ;
3. `BODYSTART` avant `BODYEND` ;
4. au moins une ligne entre les deux marqueurs.

Les marqueurs sont des commentaires : ils ne déplacent pas la machine. Ils constituent le contrat de découpage du séquenceur.

### Dans le slicer

Ajoutez `; BODYSTART` à l'endroit où commence réellement le corps de la pièce et `; BODYEND` juste après ses dernières commandes, avant le pied de page à conserver. Selon le slicer et le profil, les commandes de chauffe, de référencement et de fin peuvent se trouver avant ou après ces marqueurs. Inspectez le G-code exporté et vérifiez que chaque marqueur apparaît une seule fois.

Les emplacements d'interface varient selon les versions :

- **PrusaSlicer** : champs de G-code de début et de fin personnalisés dans les réglages imprimante ;
- **OrcaSlicer** : G-code de démarrage machine et champs de G-code personnalisé du profil ;
- **Bambu Studio** : champs de démarrage/fin machine ou réglages imprimante selon le profil ;
- **Cura** : réglages de l'imprimante, puis paramètres de G-code de début et de fin.

Le point important n'est pas le menu exact, mais le contenu exporté : le corps doit être délimité proprement.

## Importer un dossier et construire une série

1. Lancez `python src/main.py`.
2. Cliquez sur **Select folder** et choisissez le dossier contenant les fichiers G-code.
3. Seul ce dossier est parcouru, sans sous-dossiers ; les autres extensions sont ignorées.
4. Les fichiers valides apparaissent dans la table. Les fichiers invalides sont exclus et détaillés dans **Validation report**.
5. Si `serie.csv` existe, il est chargé après validation ; les noms absents ou les fichiers invalides sont signalés.
6. Modifiez les occurrences par double-clic, réordonnez les lignes par glisser-déposer et définissez le nombre de cycles.
7. Ouvrez **Settings** pour examiner ou modifier la transition, puis cliquez sur **Generate G-code** et choisissez le chemin de sortie.

Le bouton **Save series** crée ou remplace `serie.csv` dans le dossier sélectionné. Sans dossier chargé, l'interface demande un dossier. Une annulation ferme l'interface sans générer de séquence.

## Format de `serie.csv`

Le fichier doit être nommé exactement `serie.csv` et suivre cette structure :

```csv
Cycles,7
Rank,Filename,Occurrences
1,PART_1.gcode,4
2,PART_2.gcode,5
3,PART_3.gcode,6
```

Le parseur :

- attend la ligne d'en-tête `Rank,Filename,Occurrences` en deuxième ligne ;
- accepte un BOM UTF-8 et ignore les lignes complètement vides ;
- exige un nombre de cycles entier supérieur ou égal à `1` ;
- exige des rangs entiers supérieurs ou égaux à `1`, sans doublon ;
- exige des occurrences entières supérieures ou égales à `0` ;
- trie les éléments par rang ;
- exige que les noms de fichiers référencés correspondent aux fichiers valides du dossier.

L'interface limite la saisie directe à `0–999`. Le parseur de CSV, lui, accepte tout entier d'occurrences supérieur ou égal à zéro : ces deux limites ne sont donc pas identiques. La sauvegarde depuis l'interface écrit une virgule finale sur la première ligne (`Cycles,7,`), format accepté par le parseur.

## Transition et compatibilité machine

Le bloc par défaut présent dans `settings.json` est :

```gcode
; --- BELT TRANSITION ---
G91
G1 Z15 F600
G90
G28 X Y
MANUAL_STEPPER STEPPER=convoyeur MOVE=400 SPEED=50 STOP_ON_ENDSTOP=1
G28
; --- END BELT TRANSITION ---
```

Il s'agit d'un exemple configuré pour un environnement précis, pas d'une commande universelle prête à l'emploi. `MANUAL_STEPPER`, le nom `convoyeur`, les distances, vitesses, fins de course, axes, températures et positions dépendent du firmware, de la carte et de la mécanique. L'application ne peut pas déduire ces paramètres.

Le champ **Settings** permet d'enregistrer un autre bloc. Le bloc courant est injecté tel quel après chaque corps ; l'application ne recherche pas de fichier d'éjection séparé et ne vérifie pas la validité sémantique des commandes.

### Points à vérifier selon le firmware

- **Klipper** : définir et calibrer le `manual_stepper` ou une macro comme `EJECT_PART` dans `printer.cfg` avant de l'appeler.
- **Marlin** : utiliser uniquement un axe auxiliaire, une macro, un extrudeur ou une sortie configurée et documentée pour la carte ; ne pas supposer que `MANUAL_STEPPER` existe.
- **RepRapFirmware/Duet** : définir l'axe, le pilote, les pas/mm, le sens, les limites et les fins de course dans `config.g`, puis appeler une macro validée.
- **Poussée par portique** : calibrer séparément la levée, le balayage XY et les éventuelles attentes de refroidissement/réchauffage.

### Modes de mouvement et d'extrusion

La transition doit rendre à la pièce suivante les modes attendus par son G-code. `G90` correspond au positionnement absolu et `G91` au relatif ; `M82` et `M83` sélectionnent respectivement l'extrusion absolue et relative ; `G92 E0` réinitialise la position logique de l'extrudeur sans extruder. Ces commandes doivent être placées selon les hypothèses du slicer. Une transition qui laisse `G91` actif ou qui gère mal la valeur `E` peut décaler les mouvements suivants ou provoquer une extrusion/rétraction inattendue.

Évitez de désactiver les moteurs avec `M84` ou `M18` dans la transition. Vérifiez aussi le comportement du délai d'inactivité du firmware, les limites mécaniques et les zones de pincement.

### Vérification avant production

Avant une longue série, inspectez le fichier final et testez la transition sur la machine cible selon ses procédures habituelles : sans pièce si possible, buse dégagée, vitesse réduite et arrêt d'urgence accessible. Contrôlez notamment :

1. les modes `G90`/`G91` et `M82`/`M83` avant chaque corps ;
2. le placement de `G92 E0` si le flux d'extrusion l'exige ;
3. la distance, la vitesse, le sens, les limites et les fins de course de l'éjection ;
4. les températures, câbles, clips, sonde, buse et position réelle de la pièce ;
5. la présence de la dernière transition avant le pied de page final.

Le logiciel valide une structure de marqueurs et un plan de fichiers ; il ne valide ni la compatibilité machine, ni les limites de déplacement, ni les températures, ni la sécurité physique de la séquence.

## Erreurs courantes

### Rapport de validation

Le rapport peut signaler : marqueurs absents, marqueur dupliqué, ordre inversé, corps vide, échec de lecture, fichier CSV mal formé, fichier manquant ou fichier référencé mais invalide. Après fermeture du rapport, les fichiers valides peuvent continuer à être utilisés.

### Messages de génération

- `No file selected` : aucun fichier valide chargé ;
- `Invalid cycles value` : le nombre de cycles n'est pas un entier ;
- `No parts selected (all occurrences are 0)` : toutes les occurrences valent zéro ;
- `G-code composition failed:` : échec pendant le découpage ou la composition ;
- `Save failed:` : échec d'écriture du G-code ;
- `Series save failed:` : échec d'écriture de `serie.csv`.

## Licence et contact

Ce projet est présenté comme distribué sous la **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

- Usage personnel, amateur ou éducatif : autorisé selon les termes de la licence.
- Usage commercial et dérivés : soumis aux restrictions de cette licence ; consultez le texte de `LICENSE`.

Pour les demandes de licence commerciale, d'intégration ou de partenariat :
**Antoine Navarro EI — [celeautech.contact@gmail.com](mailto:celeautech.contact@gmail.com)**
