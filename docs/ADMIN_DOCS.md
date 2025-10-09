# 🧾 Documentation Technique – **Clash of piglin**

## 1. Informations générales
| Élément | Détail |
|----------|---------|
| **Titre** | Documentation Administrateur - Clash of piglin |
| **Version** | 1.0 |
| **Auteur** | Zwartkat |
| **Date de révision** | 09/10/2025 |
| **Référence du document** | DOC-GD-TECH-001 |
| **Public cible** | Développeurs, testeurs, intégrateurs |
| **Langage** | Python 3.11+ |
| **Bibliothèques principales** | Pygame 2.6, esper |

---

## 2. Objet du document
Ce document décrit l’**architecture logicielle**, les **modules**, la **procédure d’installation**, les **configurations**, et la **structure du code** du jeu **Clash of piglin**.

L’objectif est de permettre à tout développeur de comprendre le fonctionnement interne du jeu, de le modifier ou de le maintenir.

---

## 3. Références normatives
- ISO/IEC/IEEE 26514:2008 — *Design and development of information for users*  
- [Documentation Pygame](https://www.pygame.org/docs/)  
- [Python 3.11 Standard Library Reference](https://docs.python.org/3/library/)

---

## 4. Vue d’ensemble du jeu
**Clash of piglin** est un jeu type RTS inspiré de Minecraft Deux joueurs s'affrontent dans l'objectif de détruire le bastion de l'adversaire.

### Fonctionnalités principales
- Déplacement des troupes 
- Achat de troupes
- Système de génération d'argent automatique
- Interface graphique simple avec menus.  

---

## 5. Environnement logiciel requis
| Composant | Spécification |
|------------|----------------|
| **Langage** | Python 3.11 ou supérieur |
| **Bibliothèque graphique** | Pygame 2.6 |
| **OS compatibles** | Windows, macOS, Linux |
| **Dépendances** | `pip install -r requirements.txt` |
| **IDE recommandé** | VS Code |

---

## 6. Procédure d’installation

### 6.1. Cloner le dépôt
```bash
git clone https://github.com/Zwartkat/Clash-of-Piglin
cd Clash-of-Piglin
```