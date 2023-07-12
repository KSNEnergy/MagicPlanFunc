import json
from math import sqrt
import azure.functions as func
import os, logging, uuid
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import urllib.request
import xml.etree.ElementTree as ET

app = func.FunctionApp()
@app.function_name(name="MagicplanTrigger")
@app.route(route="magicplan", auth_level=func.AuthLevel.ANONYMOUS)
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    try:

        email = req._HttpRequest__params['email']
        
        if email not in []:
            return func.HttpResponse(status_code=200)
        
        root : ET.Element
        with urllib.request.urlopen(req._HttpRequest__params['xml']) as f:
            s = f.read().decode('utf-8')
            root = ET.fromstring(s)
        
        internal_width = float(root.get('interiorWallWidth'))
        extern_width_offset = internal_width * 4
        
        floor_enum = ['Floor']
        walls_area_net = []
        walls_area_gross = []
        floors_heights = []
        floors_perims = []
        floors_area = []
        doors_area = []
        windows_area = []
        cielings_area = []
        wall_index = 0
    
        floors = root.findall('interiorRoomPoints/floor')
        for floor in floors:
            
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
            floor_enum.append(str(wall_index))

            wall_index += 1

        floor_enum.append('Total')  
        values = {
            'Floor Area' :   floors_area,
            'Cieling Area' : cielings_area,
            'Floor Height' : floors_heights, 
            'Net Wall Area' : walls_area_net,
            'Gross Wall Area' : walls_area_gross,
            'Door Area' : doors_area,
            'Window Area' : windows_area,
            'Perimeter' : floors_perims
        }
        output = '<table border="1"><tr>'
    
        for floor in floor_enum:
            output += f'<th>{floor}</th>'
        output += '</tr>'

        for key in values:
            output += f'<tr><td>{key}</td>'
            for elem in values[key]:
                output += f'<td>{elem}</td>'
            if key in ['Floor Height']:
                output += '<td>N/A</td></tr>'
            else:
                output += f'<td>{sum(values[key])}</td></tr>'

        output += '</table>'

        account_url = os.environ['AZ_STR_URL']
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=default_credential)
        container_name = os.environ['AZ_CNTR_ST']
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client = blob_service_client.create_container(container_name)
        
        json_data = json.dumps({
            'email' : email, 
            'table' : output
        })

        local_file_name = str(uuid.uuid4()) + '.json'

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

        blob_client.upload_blob(json_data)

    except Exception as ex:
        logging.error(ex)
        print(f"Exception: {ex}")
    return func.HttpResponse(status_code=200)