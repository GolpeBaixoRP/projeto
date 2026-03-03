import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import gzip
from io import BytesIO

def setup_logger(log_name="MeuSonho"):
    # Configuração do nível de log via variável de ambiente (se configurado)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level, logging.INFO)

    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)

    # Se já existe um handler, não criamos outro
    if logger.handlers:
        return logger

    # Formato de log com informações completas
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]"
    )

    # Console Handler - exibe log no console
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Diretorio do log
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Arquivo de log rotacionado (5MB, 3 backups)
    log_path = os.path.join(log_dir, "meusonho.log")
    fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Arquivo de log de erros críticos
    error_log_path = os.path.join(log_dir, "meusonho_errors.log")
    error_fh = RotatingFileHandler(error_log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    error_fh.setFormatter(formatter)
    error_fh.setLevel(logging.ERROR)
    logger.addHandler(error_fh)

    # Arquivo de log rotacionado por tempo (diário)
    timed_log_path = os.path.join(log_dir, "meusonho_timed.log")
    timed_fh = TimedRotatingFileHandler(timed_log_path, when="midnight", interval=1, backupCount=7)
    timed_fh.setFormatter(formatter)
    logger.addHandler(timed_fh)

    # Compressão de arquivos antigos (rotacionados)
    def compress_log(file_path):
        with open(file_path, "rb") as f_in:
            with gzip.open(file_path + ".gz", "wb") as f_out:
                f_out.writelines(f_in)

        os.remove(file_path)

    # Chama compressão de logs antigos
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.doRollover = lambda: (
                compress_log(handler.baseFilename) or handler.doRollover()
            )

    return logger