# 🛡️ pytds — Tower Defense Simulator in Python

A custom 2D Tower Defense game built from scratch using Python and Pygame, heavily inspired by Tower Defense Simulator (TDS).

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-Green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Archived-red?style=for-the-badge)

---

## ✨ Core Features

* Custom Towers & Upgrades:
  - Unique tower classes: Archer, Cowboy, Swarmer, Harvester, Castbound.
  - Custom stats, upgrade trees, and distinct targeting logic (First, Last, Strongest, Weakest).
* Wave Engine:
  - Configurable wave spawning system.
  - Dynamic enemy health scaling and smooth waypoint pathfinding.
* UI & Interactive Placement System:
  - Clean and intuitive tower shop.
  - Grid-based placement preview with visual radius indicators and collision checks.
* Game Loop & Mechanics:
  - Economy system (earning cash per kill/wave/tower ability).
  - Game Over / Victory state conditions.

---

## 🛠️ Tech Stack & Requirements

* Language: Python 3.8+
* Library: Pygame 2.x

---

## 🚀 Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/z1gres/pytds.git
   cd pytds
   ```
3. Install dependencies:
   ```bash
   pip install pygame
   ```
5. Run the game:
   ```bash
   python main.py
   ```
---

## ⚠️ Notes & Disclaimers

> 🔴 Project Status: Archived / EOL (End of Life)
> * No Further Updates: This project is no longer actively maintained or supported. No new features, bug fixes, or updates will be released.
> * Lost Commit History: Due to repository resets/migrations, a large portion of the original commit history and development logs was unfortunately lost.
> * Reset Data / Lock Everything: If you want to reset your progress, lock all towers/features back to default, or fix corrupted save states, delete every .json file in the project directory (they will be re-created automatically on the next launch).

---

## 🎮 How to Play / Controls

* Left Mouse Button (LMB): Select towers from the shop / Place tower on the grid / Upgrade existing tower.
* Right Mouse Button (RMB) / Esc: Cancel placement or deselect tower.
* U Key: Quickly upgrade selected tower.
* Sell: Use the in-game UI panel when a tower is selected.

---

## 📄 License

Distributed under the MIT License. See LICENSE for more information.
