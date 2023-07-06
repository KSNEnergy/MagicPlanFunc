import json
import azure.functions as func
import os, logging, uuid
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()
@app.function_name(name="MagicplanTrigger")
@app.route(route="magicplan", auth_level=func.AuthLevel.ANONYMOUS)
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(req)
    try:
        account_url = os.environ['AZ_STR_URL']
        default_credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=default_credential)
        container_name = os.environ['AZ_CNTR_ST']
        container_client = blob_service_client.get_container_client(container_name)
        if not container_client.exists():
            container_client = blob_service_client.create_container(container_name)
        
        json_data = json.dumps(req.get_json())
        local_file_name = str(uuid.uuid4()) + '.json'

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
        print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

        blob_client.upload_blob(json_data)

    except Exception as ex:
        logging.error(ex)
        print(f"Exception: {ex}")
    return func.HttpResponse(status_code=200)