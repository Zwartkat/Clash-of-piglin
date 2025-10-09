# Clash-of-piglin

## Tutoriels
...

### Afficher un élement dans la map

Les coordonnées traitées en arrière plan sont les coordonnées de l'élément **dans le monde**, celui n'est cependant pas afficher à cet emplacement.
Pour afficher un élément sur la carte, il est impératif de passer par la [`Camera`](#caméra).

Il n'est pas nécessaire d'accéder directement à la caméra pour afficher l'élément souhaité. La classe [`RenderSystem`](#rendersystem) permet directement de passer l'élément souhaité pour l'afficher dans la carte

Pour cela, on doit récupérer l'instance de `RenderSystem` est utiliser les méthodes suivantes:
- `draw_surface` : pour afficher une Surface pygame
- `draw_rect` : pour dessiner un Rect de pygame 
- `draw_polygon` : pour dessiner un Polygon de pygame 

```py

from systems.rendersystem import RenderSystem

screen : pygame.Surface
map : Map
sprites : dict[CaseType,pygame.Surface]

render = RenderSystem(screen,map,sprites)

frame = sprite.get_frame()
render.draw_surface(frame, x, y)

render.draw_rect((x, y, width, height), color)

diamond_points: list[tuple[int]] = [
            (x, y - 10),  # Top
            (x + 2, y - 8),  # right
            (x, y - 6),  # bottom
            (x - 2, y - 8),  # left
        ]
render.draw_polygon(diamond_points, color)

```

### Animer une entité

L'animation d'une entité dépend du composant [`Sprite`](#sprite) à sa création. 

La frame courante peut ensuite être récupérée à partir de la méthode `get_frame`.<br>
La méthode `set_animation` permet de définir l'animation et la direction à afficher. Elle est généralement utilisée dans des méthodes appelées par l'émission d'un `Event`.<br> [Voir EventBus](#eventbus) <br>

Le Sprite est mis à jour via la méthode `update`, qui utilise le `delta_time` pour décider du changement de frame. Le [`RenderSystem`](#rendersystem) permet d'effectuer automatiquement la mise à jour de la frame à afficher


## Core

### EventBus
L'EventBus est un système permettant de transmettre des événements à n'importe quelle méthode de classe abonné <br>
Cette classe est sous la forme d'un singleton et peut être récupérée avec `EventBus.get_event_bus()`. <br>
La méthode `subscribe` permet en fournissant une classe `Event` et une méthode sous forme de `Callable`. Pour désabonner, il faut utiliser `unsubcribe`. <br>
Pour émettre un événement, il doit être donné à la méthode `emit` qui exécutera toutes les objets méthodes abonnés. Ces méthodes doivent posséder en argument l'event qui lui sera transmis<br>
```py
from core.event_bus import EventBus

render = RenderSystem()

event_bus : EventBus = EventBus.get_event_bus()

event_bus.subscribe(MoveEvent, render.animate_move)

class RenderSystem:

    def __init__(self):
        pass

    ...

    def animate_move(self, event : MoveEvent):
        print(event.pos_x,event.pos_y)
```

### IteratingProcessor
La classe `IteratingProcessor` est une classe abstraite qui permet d'effectuer une action à définir dans la classe fille. Elle permet d'executer cette action pour toutes les entités qui possèdent les `Component` fournis à l'instanciation de la classe par l'intermédiaire de la méthode `process_entity`.<br> 
Celle-ci fournit les données suivantes:
- `ent` (int) : l'identifiant de l'entité dans esper
- `dt` (float) : le delta_time 
- `*comps` (Component) : le ou les components fournis à la création de la classe fille

Exemple 
```py
from component.component1 import Component1
from component.component2 import Component2

class ExempleSystem(IteratingProcessor):
    def __init__(self):
        super().__init__(Component1,Component2)
    
    def process_entity(self, ent : int, dt : float, comp1: Component1, comp2 : Component2):
        pass
```

### Caméra

La caméra affiche uniquement les éléments aux coordonnées correspondant au delta x et y de la caméra (le décalage de la caméra par rapport au monde)

Pour utiliser la caméra, il est impératif d'executer ces deux fonctions : `set_size` et `set_world_size`

```py

from core.camera import CAMERA

CAMERA.set_size(300,300)
CAMERA.set_world_size(700,800)
```

## Composants

Toutes les entités sont définis par des composants, ceux-ci servent de stockage de données. Ils dépendent tous de `Component`.

### Attack

### Case

### Collider

### Cost

### Effects

### Fly

### Health

### Map
Le composant `Map` permet de créer des cartes de jeu, représentées par des tables de `Case`.<br> <br>
On peut en créer sans communiquer de paramètres. Le tableau représentant le contenu de la carte sera alors initialisé comme vide.
On peut cependant également créer une carte à partir d'une autre (la nouvelle copiera alors le tableau du modèle) via la méthode `initFromModel`, ou créer une carte à partir d'un tableau (list[list[CaseType]) (la carte utilisera le tableau pour initialiser le sien) via la méthode `initFromTab`.

Les propriétés d'une carte sont : <br>

- `tab` (list[list[Case]]) : Le tableau représentant le contenu de la carte.
- `index` (int) : Un index généré à partir d'un compteur statique, permettant d'identifier la carte. 

Les propriétés statiques des cartes sont :

- `counter` (int) : compteur statique s'incrémentant à chaque création de carte, utilisé pour déterminer l'index des cartes créée.
- `list_frequencies` (dict[CaseType, int]) : liste statique définissant la fréquence des différents type de cases sur la carte.
- `generate_on_base` (list[CaseType]) : liste statique définissant les types de case à générer sous les emplacements des bastions.
- `restricted_cases` (list[CaseType]) : liste statique définissant les types de case dont la génération doit être contrôlée, de sorte que toutes les cases de la carte n'étant pas d'un des types présent dans `restricted_cases` soient accessibles sans passer par une case d'un des types présent dans `restricted_cases`.
- `default_block` (CaseType) : type de case statique qui sera utilisé pour générer la carte avant l'ajout des autres types de cases.
- `limit_of_generation_for_type` (int) : nombre statique représentant la limite supérieure du nombre de groupe de cases possible pour chaque type de case (Si `limit_of_generation_for_type` vaut 2, pour chaque type de cases généré dans la fonction `generate`, les cases de ce type peuvent être réparties en 1 à 2 groupes de tailles identiques).

### Money

### Position

### Selection

### Sprite
Le component `Sprite` permet d'ajouter un sprite à une entité.<br> [Voir Animer une entité](#animer-une-entité)<br><br>
Les paramètres à fournir sont :

- `sprite_sheet` (str) : La feuille de sprite à utiliser pour l'animation.  
- `width` (int) : La largeur des frames sur la feuille de sprite.  
- `height` (int) : La hauteur des frames sur la feuille de sprite.  
- `animations` (dict) : Le détail des animations (voir ci-dessous).  
- `frame_duration` (float) : La durée en secondes d'une frame.  
- `spritesheet_direction` (Orientation) : Orientation des frames dans la feuille (HORIZONTAL ou VERTICAL). Défaut = `HORIZONTAL`.  
- `default_animation` (Animation) : L'animation par défaut de l'entité. Défaut = `IDLE`.  
- `default_direction` (Direction) : La direction par défaut de l'entité. Défaut = `DOWN`.  

Le paramètre `animations` est un dictionnaire qui associe pour chaque type d'animation et pour chaque direction, une liste d'entiers correspondant aux indices des frames sur la feuille de sprite (la première frame = 0).

Exemple de paramètre animation: 
```py
{
    Animation.IDLE: {
        Direction.DOWN: [1, 5],
        Direction.UP: [3, 7],
        Direction.LEFT: [2, 6],
        Direction.RIGHT: [0, 4],
    },
    Animation.WALK: {
        Direction.DOWN: [1, 10, 1, 11],
        Direction.UP: [3, 14, 3, 15],
        Direction.LEFT: [2, 12, 2, 13],
        Direction.RIGHT: [0, 8, 0, 9],
    },
}
```
### Squad

### Stats

### Structure

### Target

### Team

### Velocity

## Systèmes

...

### RenderSystem

RenderSystem est une classe qui gère de façon globale l'affichage. Elle hérite de [`IteratingProcessor`](#iteratingprocessor) ce qui permet d'effectuer des actions sur chaque entités possédant un composant `Position` et `Sprite`.<br><br>
Avant l'exécution du `process_entity`, les entités sont triés par `Layer` définie par la propriété `priority` de Sprite <br><br>
Son `process_entity` va afficher les entités concernées et également mettre à jour l'animation. <br><br>
Lorsque le type d'animation ne vaut pas `None`, l'entité est considéré comme un personnage jouable. Dans ce cas, une barre de vie lui ai ajouté au dessus du sprite ainsi qu'un point avec une couleur réprésentant son équipe et son état de sélection.

A sa création `RenderSystem` a besoin des 3 éléments suivants : 
- une Surface issue de pygame
- une [`Map`](#map)
- un dictionnaire de sprite pour les cases : ```dict[CaseType,pygame.Surface]```

Méthodes : 
- `show_map` : affiche la carte (carte définie à l'instanciation)
- `animate_move` : méthode qui passe les animations de sprite des entités fournit par `EventMoveTo`
- `draw_surface` : Dessine une surface pygame sur le screen du RenderSystem
- `draw_rect` : Dessine une surface pygame sur le screen du RenderSystem
- `draw_polygon` : Dessine une surface pygame sur le screen du RenderSystem
