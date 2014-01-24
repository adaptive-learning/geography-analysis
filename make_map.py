#!/usr/bin/python

from models_prior_knowledge import EloModel
from geography_common import *
from colorsys import hsv_to_rgb
from kartograph import Kartograph

K = Kartograph()

def get_config(continent):
    config = {
        "layers": [{
                "src": "kartograph/ne_110m_admin_0_countries.shp",
                "filter": {"continent":continent},
                "class": "states"
                }]
        }
    if continent == "Europe":
        config["bounds"] = { "mode": "bbox", "data": [-15, 36, 50, 70] }
    if continent == "Central America":
        config["layers"][0]["filter"] = lambda state: state['continent'] == "North America" and not (state['name'] in [ 'United States','Canada','Greenland' ])
    return config

### probabilities (values in [0,1]) to colors
        
def color_gray(val):
    s = int(255 * (1- val))
    return "'rgb("+`s`+','+`s`+','+`s`+")'"    

def color_rgspectrum(val): 
    (r,g,b) = hsv_to_rgb(0.37*val,1,1)    
    (r,g,b) = map(lambda x: int(255*x), (r,g,b))
    return "'rgb("+`r`+','+`g`+','+`b`+")'"    

def gen_style(gray = 0):
    f = open('tmp-style.css', 'w')
    states, codes = process_states()
    D = read_dict("data/raschD.csv")
    for i in codes:        
        code = codes[i].upper()
        if i in D:
            val = sigmoid(-D[i])
            if gray:
                color = color_gray(val)
            else:
                color = color_rgspectrum(val)
            f.write('.states[iso_a2='+code+"] { fill: "+color+"; }\n")
    f.close()

def make_maps(gray = 0):
    gen_style(gray)
    css = open('tmp-style.css').read()
    for continent in [ "Africa", "Europe", "Asia", "South America", "Central America" ]:
        name = 'results/'+continent+'.svg'
        print "Creating", name
        config = get_config(continent)
        K.generate(config,
                   outfile = name,
                   stylesheet = css)

if __name__ == "__main__":
    make_maps()
