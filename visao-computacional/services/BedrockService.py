import boto3
import json
import re

class BedrockService:
    # Construtor da classe
    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Função que implementa as Dicas para cada tipo de pet
    def get_tip_for_label(self, labels):
        # Define modelo a ser utilizado para gerar Dicas
        model_id = "amazon.titan-text-express-v1"

        # Define o prompt para gerar as Dicas
        prompt = f'''
            Escreva brevemente (no máximo uma linha/sentença) sobre os tópicos Nível de energia e necessidades de exercícios, Temperamento e Comportamento, Cuidados e Necessidades, e Problemas de Saúde Comuns sobre um pet que foi detectado através do Amazon Rekognition e que tem as seguintes labels (em inglês) de retorno do Amazon Rekognition: {labels}. Através dos labels fornecidos identifique de qual tipo de pet se trata (cavalos, ovelhas, gados, cães, patos, galinhas, gatos, porcos, hamsters, abelhas e outros) e devolva uma resposta em português brasileiro exatamente no formato abaixo de acordo com o tipo de pet que foi identificado pelos labels fornecidos:

            Formato da de resposta:

            Dicas sobre [tipo de pet identificado a partir dos labels fornecidos (cavalos, ovelhas, gados, cães, patos, galinhas, gatos, porcos, hamsters, abelhas e outros)]:
            Nível de Energia e Necessidades de Exercícios: [texto gerado para o tópico Nível de energia e necessidades de exercícios]
            Temperamento e Comportamento: [texto gerado para o tópico Temperamento e Comportamento]
            Cuidados e Necessidades: [texto gerado para o tópico Cuidados e Necessidades]
            Problemas de Saúde Comuns: [texto gerado para o tópico Problemas de Saúde Comuns]
        '''

        # Define parâmetros do texto a ser gerado
        native_request = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 400,
                "temperature": 0.5,
                "topP": 0.7
            },
        }

        request = json.dumps(native_request)

        try:
            response = self.bedrock.invoke_model(modelId=model_id, body=request)
            model_response = json.loads(response["body"].read())
            response_text = model_response["results"][0]["outputText"]

            # Remove caracteres de escape antes dos caracteres acentuados
            response_text = re.sub(r'\\([áéíóúãõâêîôûàèìòùäëïöüñçÁÉÍÓÚÃÕÂÊÎÔÛÀÈÌÒÙÄËÏÖÜÑÇ])', r'\1', response_text)

            # Remove qualquer outro caractere de escape desnecessário
            response_text = response_text.replace('\\"', '"').replace('\\\\', '\\')

            # Substituir '\\n' por '\n' para que as quebras de linha sejam interpretadas corretamente
            response_text = response_text.replace('\\n', '\n')

            return response_text
            
        except Exception as e:
            print(f"Erro ao invocar o modelo: {str(e)}")
            return {
                'body': json.dumps({"error": str(e)})
            }
    