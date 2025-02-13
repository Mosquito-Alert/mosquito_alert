from typing import Optional

def get_html_color_for_label(taxon, confidence: Optional[float] = None) -> str:
    if not taxon:
        return "#8B4513"

    if taxon.pk == 1: # Insecta (Other species):
        return "black"
    elif taxon.pk == 112: # Aedes Albopictus
        if confidence >= 0.9:
            return "#FF0000"    # Red
        else:
            return "#B22222"    # Light red
    elif taxon.pk == 111: # Aedes albopictus/cretinus (complex)
        return "#708090"        # Light Slate Gray
    elif taxon.pk == 113: # Aedes Aegypti
        if confidence >= 0.9:
            return "#008000"    # Green
        else:
            return "#9ACD32"    # Light Green
    elif taxon.pk == 110: # Aedes Japonicus/Koreicus (complex)
        return "#2F4F4F"    # Dark Slate Gray
    elif taxon.pk == 114: # Aedes Japonicus
        if confidence >= 0.9:
            return "#B8860B"    # Orange
        else:
            return "#DAA520"    # Light Orange
    elif taxon.pk == 115: # Aedes Koreicus
        if confidence >= 0.9:
            return "#BDB76B"    # Yellow
        else:
            return "#F0E68C"    # Light Yellow
    elif taxon.pk == 10: # Culex sp.
        if confidence >= 0.9:
            return "#FF69B4"    # Pink
        else:
            return "#FFB6C1"    # Light Pink

    return 'white; border:1px solid #000; color:black'