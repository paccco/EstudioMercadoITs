import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def subir_a_s3(ruta_local: Path, bucket_name: str, clave_s3: str) -> bool:
    """Sube un archivo local a Amazon S3 usando credenciales del entorno."""
    s3_client = boto3.client("s3")
    try:
        logger.info("Subiendo '%s' a s3://%s/%s ...", ruta_local.name, bucket_name, clave_s3)
        s3_client.upload_file(str(ruta_local), bucket_name, clave_s3)
        logger.info("Subida a S3 completada con éxito.")
        return True
    except ClientError as e:
        logger.error("Error de cliente AWS al subir a S3: %s", e)
        return False
    except Exception as e:
        logger.error("Error inesperado subiendo a S3: %s", e)
        return False