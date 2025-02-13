import boto3

class S3Service:
    def __init__(self):
        # Construtor da classe
        self.s3_client = boto3.client('s3')

    # Define função para recuperar metadados de objeto do S3
    def get_object_s3(self, bucket, image_name):
        try:
            response = self.s3_client.head_object(
                Bucket=bucket,
                Key=image_name
            )
            return response
        except Exception as e:
            raise e
