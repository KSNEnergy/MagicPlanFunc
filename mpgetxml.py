from math import sqrt
import os
import requests as rq
import json
import xml.etree.ElementTree as ET

endpoint = 'https://cloud.magicplan.app/api/v2/plans/get/{}'
plan_ID = ''

if __name__ == '__main__':

    customerID = os.environ['MP_CUST_ID']
    apiKey = os.environ['MP_API_KEY']
    
    headers = {
        'key'         : apiKey, 
        'customer'    : customerID, 
        'Content-Type': 'application/json'
    }

    url = endpoint.format(plan_ID)
    response = rq.get(url=url, headers=headers)

    jres = json.loads(response.content)
    root = ET.fromstring(jres['data']['plan_detail']['magicplan_format_xml'])
        
    internal_width = float(root.get('interiorWallWidth'))
    extern_width_offset = internal_width * 4
    
    walls_area_net = []
    walls_area_gross = []
    floors_heights = []
    floors_perims = []
    doors_area = []
    windows_area = []
    cielings_area = []

    floors = root.findall('interiorRoomPoints/floor')
    for floor in floors:
        
        extern_wall_area = 0
        extern_perim = 0
        wall_height = 0
        window_area = 0
        nwalls = 0
        door_area = 0
        rooflight_area = 0
        
        for wall in floor.findall('exploded/wall'):
            if wall.find('type').text == 'exterior':
                points = wall.findall('point')
                p1, p2, *rest = points
                x1 = float(p1.get('x'))
                x2 = float(p2.get('x'))
                y1 = float(p1.get('y'))
                y2 = float(p2.get('y'))
                length = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                wall_height += (float(p1.get('height')) + float(p2.get('height')))/2
                nwalls += 1
                extern_perim += length
        
        extern_perim -= extern_width_offset
        wall_height = wall_height/nwalls if nwalls != 0 else wall_height
        wall_area_gross = extern_perim * wall_height
        
        symbols = floor.findall('symbolInstance')
        for door in floor.findall('exploded/door'):
            if door.get('type') == '0':
                symbol_instance = door.get('symbolInstance')
                for symbol in symbols:
                    if symbol.get('id') == symbol_instance and symbol_instance != '':
                        values = symbol.findall('values/value')
                        for value in values:
                            if value.get('key') == 'clonedFrom' and value.text.__contains__('door'):
                                door_area += float(door.get('width')) * float(door.get('height'))
        
        for window in floor.findall('exploded/window'):
            window_area += float(window.get('height')) * float(window.get('width'))
        
        for furniture in floor.findall('exploded/furniture'):
            symbol_instance = furniture.get('symbolInstance')
            for symbol in symbols:
                if symbol.get('id') == symbol_instance and symbol_instance != '' and symbol.get('symbol').__contains__('windowtskylight'):
                    rooflight_area += float(furniture.get('width')) * float(furniture.get('height'))                    
        
        wall_area_net = wall_area_gross - window_area - door_area
        cieling_area = float(floor.get('areaWithInteriorWallsOnly')) - rooflight_area
        
        cielings_area.append(cieling_area)
        floors_heights.append(wall_height)
        walls_area_net.append(wall_area_net)
        walls_area_gross.append(wall_area_gross)
        floors_perims.append(extern_perim)
        doors_area.append(door_area)
        windows_area.append(window_area)
    
    values = {
        'Cieling Area' : cielings_area,
        'Floor Height' : floors_heights, 
        'Net Wall Area' : walls_area_net,
        'Gross Wall Area' : walls_area_gross,
        'Door Area' : doors_area,
        'Window Area' : windows_area,
        'Perimeter' : floors_perims
    }

    f = open('{}.txt'.format(root.get('name')).replace(' ', ''), 'w')
    i = 0
    space_str = '                 '
    output = 'Floor:' + space_str[0:11] # 11 Spaces
    while i < len(floors_heights):
        output += str(i) + space_str[0:8] # 9 Spaces
        i += 1
    
    output += 'Total'

    for key in values:
        output += '\n' + key + ':' +  space_str[0:len(space_str) - (len(key)+1)]
        for elem in values[key]:
            output += str(elem)[0:8] + ' ' if len(str(elem)) > 9 else str(elem) + space_str[0:9-len(str(elem))]
        if key == 'Door Area':
            output += 'N/A'
        else:
            output += str(sum(values[key]))[0:9] if len(str(sum(values[key]))) > 10  else str(sum(values[key]))

    f.write(output)
    f.close()