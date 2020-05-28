def get_html_color_for_label(label):
    default = 'white; border:1px solid #000; color:black'

    color_table = {
        'Unclassified': '#8B4513',
        'Conflict': '#00FFFF; border:1px solid #000; color:black',
        'Other species': 'black',
        'Not sure': default,
        'Definitely Aedes albopictus': '#FF0000',
        'Probably Aedes albopictus': '#B22222',
        'Definitely Aedes aegypti': '#008000',
        'Probably Aedes aegypti': '#9ACD32',
        'Definitely Aedes japonicus': '#B8860B',
        'Probably Aedes japonicus': '#DAA520',
        'Definitely Aedes koreicus': '#BDB76B',
        'Probably Aedes koreicus': '#F0E68C',
        'Definitely Culex sp.': '#FF69B4',
        'Probably Culex sp.': '#FFB6C1',
        'japonicus/koreicus': '#2F4F4F',
        'albopictus/cretinus': '#708090'
    }

    return color_table.get(label, default)