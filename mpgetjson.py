import os
import requests as rq
import json
url = 'https://cloud.magicplan.app/api/v2/plans/statistics/'
plan_ID = ''

# This may be scrapped - the perimeter listed as part of the json data is incorrect. 
# It remains to be seen if this data is necessary for anything else. 

if __name__ == '__main__':

    customerID = os.environ['MP_CUST_ID']
    apiKey = os.environ['MP_API_KEY']
    headers = {'key': apiKey, 'customer': customerID, 'Content-Type': 'application/json'}
    url += plan_ID
    
    floor_areas = []
    floor_heights = []
    floor_perims = []
    door_area = 0
    response = rq.get(url=url, headers=headers)
    jres = json.loads(response.content)

    stats = jres['data']['project_statistics']
    volume = stats['volume']
    living_area = stats['above_grade_living_area']
    heat_loss_wall_area = stats['walls_surface'] - stats['windows_surface']

    for floor in stats['floors']:
        floor_areas.append(floor['area'])
        floor_heights.append(floor['height'])
        floor_perims.append(floor['perimeter'])
        for room in floor['rooms']:
            for wall_item in room['wall_items']:
                if wall_item['name'] == 'External Door':
                    door_area += wall_item['height'] * wall_item['width']