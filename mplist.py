import requests as rq
import json
import os
url = 'https://cloud.magicplan.app/api/v2/workgroups/plans'

if __name__ == '__main__':
    page = 1

    customerID = os.environ['MP_CUST_ID']
    apiKey = os.environ['MP_API_KEY']
    data = rq.get(url=url, headers={'key': apiKey, 'customer': customerID, 'Content-Type': 'application/json'}, params={'page': page})
    json_data = json.loads(data.content)
    next_page = json_data['data']['paging']['next_page']
    while next_page:
        page += 1
        data = rq.get(url=url, 
                      headers={
                          'key': apiKey,
                          'customer': customerID,
                          'Content-Type': 'application/json'
                        }, 
                        params={
                            'page': page
                        })
        new_data = json.loads(data.content)
        next_page = new_data['data']['paging']['next_page']
        json_data['data']['plans'].extend(new_data['data']['plans'])
    
    data_complete = json.dumps(json_data)
    f = open('projects_list.json', 'w')
    f.write(data_complete)
    f.close()



        

        