from math import sqrt
import os
import requests as rq
import pandas as pd
import json
import xml.etree.ElementTree as ET

endpoint = 'https://cloud.magicplan.app/api/v2/plans/get/{}'
plan_ID = ''


def cart_distance(p1 : tuple[float, float], p2 : tuple[float, float]) -> float:
    (x1, y1) = p1
    (x2, y2) = p2
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def create_table(dict : dict[str, list[float]], headers : list,
                  do_not_sum : list[str] = [], 
                  styling: str = "", colour_table : bool = False) -> str:
    
    output = f'<table {styling}><tr>'
    
    for header in headers:
        output += f'<th>{header}</th>'
    output += '</tr>'
    
    for i, key in enumerate(dict):
        if colour_table:
            output += f'<tr><td><b style="color:{key}">Colour {i}<b></td>'
        else:
            output += f'<tr><td>{key}</td>'
        for elem in dict[key]:
            output += f'<td>{round(elem, 2)}</td>'
        if key in do_not_sum:
            output += '<td>N/A</td></tr>'
        else:
            output += f'<td>{round(sum(dict[key]), 2)}</td></tr>'
    
    output += '</table>'
    return output

if __name__ == '__main__':
    
    window_type_key = 'qf.90b60e42q{}'
    lookup = {
        'LED/CFL'           : 'co-2f58f502-264c-4374-812e-567720171980',
        'Halogen Lamp'      : 'co-d829711d-35d6-4239-9cdf-66f5d107d7eb',
        'Halogen LV'        : 'co-76c448a3-1d97-4d99-be46-9ba6b87ca68c',
        'Linear Fluorescent': 'co-db1fd5c3-1ed9-43c5-b430-1be89b7b5e1b',
        'Incandescent'      : 'co-a81c5e44-754e-4c43-998c-55f75b0b0571',
        'EMV'               : 'co-0c7d0ada-8a17-41f9-8746-e7007a1c40b1',
        'NMV'               : 'co-accd48a4-43b8-4381-b569-c8404f52dec5',
        'NPV'               : 'co-483ab20e-2762-4733-9db5-19d21e1d090d',
        'NBV'               : 'co-88da8a48-da48-4c3d-a459-ee8eef96bcdd',
        'EPV'               : 'co-4d2e52df-c793-4c02-953a-f4ed0b7eaae0',
        'DCH'               : 'co-03b80e12-32b7-45be-8b44-9b4b03a09b4c',
        'EMVB'              : 'co-33fd6b69-25ae-4e55-bf7b-f91af6112ac4',
        'ECHB'              : 'co-d0f4acd2-8598-49ec-ac3c-8b39edc724e9',
        'Chimney'           : 'co-5651e005-f73c-4d26-8b75-6d07291d7839',
        'Flue'              : 'co-9276562f-535a-4c1f-a708-d869f581194d',
        'Flueless'          : 'co-86083af5-5a40-4831-9990-4f60aa537d99'
    }

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
    window_type_lookup = []

    for i in range(5):
        type = root.find(f'values/value[@key="{window_type_key.format(i)}"]')
        if type != None:
            window_type_lookup.append(type.text.replace('.', ' '))
    
    internal_width = float(root.get('interiorWallWidth'))
    extern_width_offset = internal_width * 4
    
    walls_area_net = []
    walls_area_gross = []
    floors_heights = []
    floors_perims = []
    floors_area = []
    doors_area = []
    windows_area = []
    cielings_area = []

    led_count = []
    lf_count = []
    inc_count = []
    hlv_count = []
    hl_count = []

    in_f_count = []
    pnc_count = []

    flue_count = []
    chimney_count = []
    flueless_count = []

    floor_enum = ['Floor']
    floor_index = 0
    
    wall_types = {}
    colours : dict[str, dict[int, int]]
    colours = {}

    floors = root.findall('interiorRoomPoints/floor')
    empty_array = [0] * len(floors)
    
    window_data = pd.DataFrame(None, columns=['North', 'North East', 'East', 'South East', 'South', 'South West', 'West', 'North West'])
    window_data_list = []

    for i in range(5):
        window_data_list.append(window_data.copy()) # Can't do [window_data.copy()] * 5 because this does a deep copy of window data, then shallow copies that 5 times. I just want my pointers back.



    for floor in floors:
        
        extern_perim = 0
        wall_height = 0
        window_area = 0
        nwalls = 0
        door_area = 0
        rooflight_area = 0
        wall_area_gross = 0

        room_points_list: list[tuple[float, float, str]]
        room_points_list = []
        room_points = floor.findall('floorRoom/point/values/value[@key="qcustomfield.e8660a0cq0.lo6b23iucno"]../../..')
        
        window_keys = ['qcustomfield.bebb2096q0.5s6ahr5olj', 
                       'qcustomfield.bebb2096q0.9pqleon5rmg', 
                       'qcustomfield.bebb2096q0.h0serf6b2po', 
                       'qcustomfield.bebb2096q0.q05mtrjuu18', 
                       'qcustomfield.bebb2096q0.ofru5eoj50o']
        
        windows_doors = floor.findall('symbolInstance')
        windows_doors = [window for window in windows_doors if 'W' in window.get('id')]

        window_door_table : dict[str, list[float]] = {}
    
        for window in windows_doors:
            id = window.get('id')

            if window.find('values/value[@key="clonedFrom"]') == None:
                continue
            if 'window' not in window.find('values/value[@key="clonedFrom"]').text:
                continue
            wall_elem : ET.Element
            
            for key in window_keys:
                wall_elem = window.find(f'values/value[@key="{key}"]')
                if wall_elem != None:
                    break
            
            wall_type = wall_elem.text[-1] if wall_elem != None else ''
            window_elem = floor.find(f'exploded/window[@symbolInstance="{id}"]')
            area = float(window_elem.get('height')) * float(window_elem.get('width'))
            wall_type_win_area = f'W.A. in W.T. {wall_type}'
            if wall_type_win_area not in window_door_table and wall_type_win_area != '':
                window_door_table[wall_type_win_area] = empty_array.copy()
            window_door_table[wall_type_win_area][floor_index] += area
            
            shading_type = window.find('values/value[@key="qcustomfield.bebb2096q0.vvvvtj3gbp8"]')
            window_type = window.find('values/value[@key="qcustomfield.bebb2096q2"]')
            direction = window.find('values/value[@key="qcustomfield.bebb2096q0.b8o7vbr534"]')
            
            if window_type != None and direction != None and \
                not 'skylight' in window.find('values/value[@key="clonedFrom"]'):
                shading_type_text = ''
                if shading_type == None:
                    shading_type_text = 'Average or Unknown 20 60'
                else:
                    shading_type_text = shading_type.text.replace('.', ' ')
                direction_text = direction.text.replace('.', ' ')
                window_type_int = int(window_type.text.split('Type.')[1][0]) - 1
                if shading_type_text not in window_data_list[window_type_int].index:
                    window_data_list[window_type_int].loc[shading_type_text] = [0] * 8
                window_data_list[window_type_int].loc[shading_type_text, direction_text] += area


        door_keys = ['qcustomfield.ddc14d2eq0.dge5jfv5gn8', 
                     'qcustomfield.ddc14d2eq0.afcmuvtdagg']

        for door in windows_doors:
            id = door.get('id')
            if door.find('values/value[@key="clonedFrom"]') == None:
                continue
            if 'door' not in door.find('values/value[@key="clonedFrom"]').text:
                continue
            
            wall_elem : ET.Element
            for key in door_keys:
                wall_elem = door.find(f'values/value[@key="{key}"]')
                if wall_elem != None:
                    break
            if wall_elem == None:
                continue

            wall_type = wall_elem.text[-1]
            door_elem = floor.find(f'exploded/door[@symbolInstance="{id}"]')
            area = float(door_elem.get('height')) * float(door_elem.get('width'))
            w_t_area = f'D.A. in W.T. {wall_type}'
            if w_t_area not in window_door_table:
                window_door_table[w_t_area] = empty_array.copy()
            window_door_table[w_t_area][floor_index] += area
        
        
        for room in room_points:
            points = room.findall('point/values/value[@key="qcustomfield.e8660a0cq0.lo6b23iucno"]../..')
            all_points = room.findall('point')
            for point in points:
                wall_type = point.find('values/value[@key="qcustomfield.e8660a0cq0.lo6b23iucno"]')
                if len(wall_type.text) == 3:
                    continue
                w_type = wall_type.text[-1] if wall_type.text[-1].isnumeric() else wall_type.text.replace('.', ' ')
                area = f'{w_type} Area Gross'
                perim = f'{w_type} Perimeter'
                x1 = float(point.get('snappedX'))
                y1 = float(point.get('snappedY'))
                next_index = all_points.index(point) + 2 #Elemet Tree Indexes from 1, this index returns the index from 0, to get the next element we add 2.
                next = room.find(f'point[{next_index}]')
                if next == None:
                    next = room.find('point[1]')
                x2 = float(next.get('snappedX'))
                y2 = float(next.get('snappedY'))
                height = (float(point.get('height')) + float(next.get('height')))/2
                wall_length = cart_distance((x1, y1), (x2, y2))
                wall_area = wall_length * height
                if area not in wall_types:
                    wall_types[area] = empty_array.copy()
                wall_types[area][floor_index] += wall_area
                if perim not in wall_types:
                    wall_types[perim] = empty_array.copy()
                wall_types[perim][floor_index] += wall_length
                

        for wall in floor.findall('exploded/wall'):
            if wall.find('type').text == 'exterior':
                points = wall.findall('point')
                p1, p2, *rest = points
                x1 = float(p1.get('x'))
                x2 = float(p2.get('x'))
                y1 = float(p1.get('y'))
                y2 = float(p2.get('y'))
                length = cart_distance((x1, y1), (x2, y2))
                wall_height = (float(p1.get('height')) + float(p2.get('height')))/2
                wall_area_gross += wall_height * length
                extern_perim += length
        
        extern_perim -= extern_width_offset
        wall_height = wall_height/nwalls if nwalls != 0 else wall_height
        wall_area_gross -= wall_types['Party Wall Area'][floor_index] if 'Party Wall Area' in wall_types else 0
        
        for window in floor.findall('exploded/window'):
            if 'window count' not in window_door_table:
                window_door_table['Window Count'] = empty_array.copy()
            window_door_table['Window Count'][floor_index] += 1
            window_area += float(window.get('height')) * float(window.get('width'))                  
        
        for room in floor.findall('floorRoom/values/value[@key="ground.color"]../..'):
            colour = room.find('values/value[@key="ground.color"]').text
            area = float(room.get('area'))
            if colour not in colours:
                colours[colour] = empty_array.copy()
            colours[colour][floor_index] += area
        
        for type in window_door_table:
            if type[-1].isnumeric() and 'A.' in type:
                window_door_area = window_door_table[type][floor_index]
                gross_area_key = f'{type[-1]} Area Gross'
                net_area_key = f'{type[-1]} Area Net'
                try:
                    area : float
                    if net_area_key in wall_types:
                        area = wall_types[net_area_key][floor_index]
                    else:
                        wall_types[net_area_key] = empty_array.copy() 
                        area = wall_types[gross_area_key][floor_index]
                    net_area = area - window_door_area
                    wall_types[net_area_key][floor_index] = net_area
                except:
                    print('Could not find wall type in wall_type dict')
        
        for key in window_door_table:
            if 'D.A.' in key:
                door_area += sum(window_door_table[key])
        
        wall_area_net = wall_area_gross - window_area - door_area 

        floor_area = float(floor.get('areaWithInteriorWallsOnly'))
        cieling_area = floor_area - rooflight_area

        floors_area.append(floor_area)
        cielings_area.append(cieling_area)
        floors_heights.append(wall_height)
        walls_area_net.append(wall_area_net)
        walls_area_gross.append(wall_area_gross)
        floors_perims.append(extern_perim)
        doors_area.append(door_area)
        windows_area.append(window_area)
        floor_enum.append(str(floor_index))

        led_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["LED/CFL"]}\']')))
        lf_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Linear Fluorescent"]}\']')))
        hl_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Halogen Lamp"]}\']')))
        inc_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Incandescent"]}\']')))
        hlv_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Halogen LV"]}\']')))
        
        flueless_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Flueless"]}\']')))
        chimney_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Chimney"]}\']')))
        flue_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["Flue"]}\']')))

        in_f_count.append(
            len(floor.findall(f'symbolInstance[@symbol=\'{lookup["NMV"]}\']')) + 
            len(floor.findall(f'symbolInstance[@symbol=\'{lookup["EMV"]}\']')) + 
            len(floor.findall(f'symbolInstance[@symbol=\'{lookup["DCH"]}\']')) + 
            len(floor.findall(f'symbolInstance[@symbol=\'{lookup["EMVB"]}\']')) + 
            len(floor.findall(f'symbolInstance[@symbol=\'{lookup["ECHB"]}\']'))
        )

        pnc_count.append(len(floor.findall(f'symbolInstance[@symbol=\'{lookup["EPV"]}\']')))
        floor_index += 1
    
    floor_enum.append('Total')
    
    for frame in window_data_list:
        frame.loc['Total'] = frame.sum(numeric_only=True)
        frame.loc[:,'Shading Total'] = frame.sum(numeric_only=True, axis=1)

    summary_values = {
        'Floor Area'                      : floors_area,
        'Cieling Area'                    : cielings_area,
        'Floor Height'                    : floors_heights, 
        'Net Wall Area'                   : walls_area_net,
        'Gross Wall Area'                 : walls_area_gross,
        'Door Area'                       : doors_area,
        'Window Area'                     : windows_area,
        'Perimeter'                       : floors_perims,
    }

    deap_values = {
        'LED/CFL'                         : led_count,
        'Halogen Lamp'                    : hl_count,
        'Halogen LV'                      : hlv_count,
        'Linear Fluorescent'              : lf_count,
        'Incandescent'                    : inc_count,
        'Intermittent Fan Count'          : in_f_count,
        'Passive Non-Closable (Add Note)' : pnc_count,
        'Flueless Combustion Room Heater' : flueless_count,
        'Flue'                            : flue_count,
        'Chimney'                         : chimney_count
    }
    table_list = ''

    for i, frame in enumerate(window_data_list):
        if i < len(window_type_lookup):
            table_list += f'<h2>{window_type_lookup[i]} Window Table</h2>{frame.to_html()}' if not frame.empty else f'<h2>No Windows of type {window_type_lookup[i]}</h2>'
        else:
            table_list += f'<h2>Window Type {i+1} Table</h2>{frame.to_html()}' if not frame.empty else f'<h2>No Windows of type {i+1}</h2>'
    
    table_list += '</ol>'

    f = open('{}.html'.format(root.get('name')).replace(' ', ''), 'w')
    styling = "border=\"1\""
    output = f"""<div><h1>Plan Summary Table</h1> \
        {create_table(summary_values, floor_enum, styling=styling, do_not_sum=["Floor Height"])} \
        <h1>Objects Table</h1> \
        {create_table(deap_values, floor_enum, styling=styling)} \
        {"<h1>Colour Area Table</h1>" + create_table(colours, floor_enum, styling=styling, colour_table=True) if len(colours) > 0 else ""} \
        <h1>Wall Types</h1> \
        {create_table(wall_types, floor_enum, styling=styling)} \
        <h1>Window Tables</h1> \
        {table_list} \
        <div>"""

    f.write(output)
    f.close()