from django.utils.translation import get_language


def localized(fr, ar):
    """Renvoie le texte arabe si la langue active est l'arabe et qu'il existe, sinon le français
    (et inversement), pour qu'une traduction manquante ne rende jamais un objet illisible."""
    if (get_language() or "fr").startswith("ar") and ar:
        return ar
    return fr or ar
