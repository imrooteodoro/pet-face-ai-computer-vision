import boto3
from models.Label import Label
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
from services.BedrockService import BedrockService
from services.S3Service import S3Service


class RekognitionService:
    def __init__(self):
        # Inicia client do Rekognition, Bedrock e S3
        self.rekognition = boto3.client('rekognition')
        self.bedrock_service = BedrockService()
        self.s3_service = S3Service()


    # Realiza detecção de faces
    def get_faces(self, bucket, img_name):
        try:
            # Retorna informações das faces reconhecidas
            detected_faces = self.rekognition.detect_faces(
                Image={'S3Object': {'Bucket': bucket, 'Name': img_name}},
                Attributes=['ALL']
            )

            print(detected_faces)

            # Acessando cada uma das faces e retornando valores de interesse
            faces = []
            if detected_faces and 'FaceDetails' in detected_faces:
                for face_detail in detected_faces['FaceDetails']:
                    face_data = {
                        "position": 
                        face_detail['BoundingBox'],
                        "classified_emotion": face_detail['Emotions'][0]['Type'],
                        "classified_emotion_confidence": face_detail['Emotions'][0]['Confidence']
                    }
                    faces.append(face_data)

            return faces

        except Exception as e:
            print(f"Error recognizing faces: {e}")
            return None
    
    # Realiza detecção de faces
    def get_pets(self, bucket, image_name):
        try:
            # Entrada para o Rekognition
            rekognition_image = {
                'S3Object': {
                    'Bucket': bucket,
                    'Name': image_name,
                }
            }

            # Usa o Rekognition para detectar rótulos na imagem
            rekognition_response = self.rekognition.detect_labels(Image = rekognition_image)

            # Cria uma lista vazia para armazenar as imagens dos pets
            pets = []

            # Recupera a imagem no bucket S3
            image_url = f'https://{bucket}.s3.amazonaws.com/{image_name}'
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Recupera dimensões da imagem armazenada no bucket S3
            image_width = image.size[0]
            image_height = image.size[1]

            # Itera sobre cada rótulo detectado pelo Rekognition
            for label in rekognition_response['Labels']:
                # Encontra Labels que tem instâncias e Labels que tenham Pet na lista Parents
                if len(label['Instances']) > 0 and any(child['Name'] == 'Pet' for child in label['Parents']):
                    # Percorre cada instância do Pet encontrado
                    for instance in label['Instances']:
                        # Obtém a caixa delimitadora da instância
                        bounding_box = instance['BoundingBox']
                        
                        # Calcula comprimento e largura reais da imagem
                        width = int(bounding_box['Width'] * image_width)
                        height = int(bounding_box['Height'] * image_height)

                        # Calcula coordenadas da instância encontrada
                        left = int(bounding_box['Left'] * image_width)
                        top = int(bounding_box['Top'] * image_height)
                        right = left + width
                        bottom = top + height

                        # Recorta imagem da instância encontrada baseada nas coordenadas calculadas
                        pet_image = image.crop((left, top, right, bottom))

                        # Adiciona recorte da imagem no vetor de pets
                        pets.append(pet_image)
            
            return pets
        except Exception as e:
            raise Exception(e)
    
    def recognize_faces(self, bucket, img_name):
        try:
            
            faces = self.get_faces(bucket, img_name)
            # Definindo URL da imagem
            url_to_image = f"https://{bucket}.s3-website-us-east-1.amazonaws.com/{img_name}"

            # Define modelo de resposta
            response = {
                'url_to_image': url_to_image,
                'created_image': datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                'faces': faces if len(faces) > 0 else [{ # Retorna Null caso não reconheça nenhuma face
                    "position": {
                    "Height": None,
                    "Left": None,
                    "Top": None,
                    "Width": None
                    },
                    "classified_emotion": None,
                    "classified_emotion_confidence": None
                }]
            }

            return response
        except Exception as e:
            raise Exception(e)

    def recognize_pets(self, bucket, imageName):
        try:
            # Recupera vetor com os recortes das imagens dos pets identificados na imagem
            pets_crops = self.get_pets(bucket, imageName)

            # Recupera os dados da imagem submetida para análise
            s3Response = self.s3_service.get_object_s3(bucket, imageName)


            pets = []

            # Percorre cada recorte que contém a imagem de um Pet
            for pet in pets_crops:
                # Converte o recorte em bytes de uma imagem PNG
                pet_image = BytesIO()
                pet.save(pet_image, "PNG")

                Image = {
                    'Bytes': pet_image.getvalue()
                }

                # Detecta rótulos para o Pet submetido
                rekognitionResponse = self.rekognition.detect_labels(Image = Image)

                print(rekognitionResponse)

                labels = []
                bedrock_labels = []
                
                # Guarda rótulos e confiança encontrados se o Label tem mais que 60% de confiança
                for label in rekognitionResponse['Labels']:
                    if label['Confidence'] >= 60:
                        imageLabel = Label(label['Name'], label['Confidence'])
                        labels.append(imageLabel)
                    
                    if label['Confidence'] >= 90:
                        bedrock_labels.append(label['Name'])

                # Adiciona informações do Pet detectado na lista de pets
                pets.append(
                    {
                        'Labels': [
                            {
                                'Name': label.name,
                                'Confidence': label.confidence
                            } for label in labels
                        ],
                        'Dicas': self.bedrock_service.get_tip_for_label(bedrock_labels)
                    }
                )

            # Define faces detectadas
            faces = self.get_faces(bucket, imageName)

            # Define modelo de resposta
            response = {
                'url_to_image': f'https://{bucket}.s3.amazonaws.com/{imageName}',
                'created_image': datetime.strptime(s3Response['ResponseMetadata']['HTTPHeaders']['last-modified'], '%a, %d %b %Y %H:%M:%S %Z').strftime("%d-%m-%Y %H:%M:%S"),
            }
            if len(faces) > 0:
                response['faces'] = faces
            
            response['pets'] = pets if len(pets) > 0 else [{
            'Labels': [
            {
            'Name': None,
            'Confidence': None
            }
            ],
            'Dicas': None
            }]

            return response
        except Exception as e:
            raise Exception(e)