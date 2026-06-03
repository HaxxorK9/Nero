import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from math import ceil

def generate_stats_image(stats, username, output_path="stats.png"):
    """
    Génère un radar chart selon les statistiques du joueur.
    """

    labels = list(stats.keys())
    values = list(stats.values())

    # --- Détermination automatique du maximum ---
    max_stat = max(values)

    # Arrondit à la dizaine supérieure
    max_scale = int(ceil(max_stat / 10.0) * 10)

    # Sécurité minimum
    if max_scale < 10:
        max_scale = 10

    # --- Préparation du radar ---
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    # Ferme le cercle
    values += values[:1]
    angles += angles[:1]

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Fond noir
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    # Rotation pour mettre la première stat en haut
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Labels
    plt.xticks(angles[:-1], labels, color="white", fontsize=12)

    # Échelle
    ax.set_rlabel_position(180 / num_vars)

    step = max_scale // 5

    plt.yticks(
        range(step, max_scale + step, step),
        [str(x) for x in range(step, max_scale + step, step)],
        color="gray",
        fontsize=10
    )

    plt.ylim(0, max_scale)

    # Radar rempli
    ax.plot(angles, values, color="#ffb300", linewidth=3)
    ax.fill(angles, values, color="#ffb300", alpha=0.5)

    # Sauvegarde
    plt.title(
        username,
        color="white",
        size=20,
        pad=20
    )

    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    plt.close()