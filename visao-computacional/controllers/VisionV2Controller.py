import json
from services.RekognitionService import RekognitionService

def vision_v2(event, context):
    response = None

    try:
        # Recupera corpo da requisição
        body = json.loads(event['body'])

        # Guarda informações enviadas na requisição
        bucket = body['bucket']
        imageName = body['imageName']

        rekognition_service = RekognitionService()

        # Cria objeto com modelo de resposta
        response = {
            "statusCode": 200,
            "body": json.dumps(rekognition_service.recognize_pets(bucket, imageName)) # chama função para reconhecimento de pets
        }
    except Exception as e:
        response = {
            "statusCode": 500,
            "body": json.dumps({
                'error': str(e)
            })
        }

    return response