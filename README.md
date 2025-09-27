# Clash-of-piglin

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

## Composants

Toutes les entités sont définis par des composants, ceux-ci servent de stockage de données. Ils dépendent tous de `Component`.

### Attack

### Collider

### Cost

### Effects

### Fly

### Health

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

## Gestion des entités
...

### Animer une entité

L'animation d'une entité dépend du composant [`Sprite`](#sprite) à sa création. 

La frame courante peut ensuite être récupérée à partir de la méthode `get_frame`.<br>
La méthode `set_animation` permet de définir l'animation et la direction à afficher. Elle est généralement utilisée dans des méthodes appelées par l'émission d'un `Event`.<br> [Voir EventBus](#eventbus) <br>

Le Sprite est mis à jour via la méthode `update`, qui utilise le `delta_time` pour décider du changement de frame. Le [`RenderSystem`](#rendersystem) permet d'effectuer automatiquement la mise à jour de la frame à afficher

## Systèmes

...

### RenderSystem

RenderSystem est une classe qui gère de façon globale l'affichage. Elle hérite de [`IteratingProcessor`](#iteratingprocessor) ce qui permet d'effectuer des actions sur chaque entités possédant un composant `Position` et `Sprite`.<br><br>
Son `process_entity` va afficher les entités concernées et également mettre à jour l'animation. <br><br>
Lorsque le type d'animation ne vaut pas `None`, l'entité est considéré comme un personnage jouable. Dans ce cas, une barre de vie lui ai ajouté au dessus du sprite ainsi qu'un point avec une couleur réprésentant son équipe et son état de sélection.