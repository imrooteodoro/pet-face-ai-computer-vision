import json
from services.RekognitionService import RekognitionService

def vision_v1(event, context):
    response = None
    
    try:
        # Define corpo da requisição e atribui suas variáveis
        body = json.loads(event['body'])
        bucket = body['bucket']
        img_name = body['imageName']

        rekognition_service = RekognitionService()

        # Chama função que reconhece as faces e retorna resposta
        response = rekognition_service.recognize_faces(bucket, img_name)
        
        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }
    except Exception as e:
        print(f"Error processing request: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
