from configobj import ConfigObj

class Config:

    config = ConfigObj("configurations.txt")

    db_host = config.get("db_host")
    db_port = config.get("db_port")
    db_user = config.get("db_user")
    db_paswword = config.get("db_password")
    db_database = config.get("db_database")

    sdn_host = config.get("sdn_host")
    sdn_port = config.get("sdn_port")
    sdn_user = config.get("sdn_user")
    sdn_password = config.get("sdn_password")
    log_file = config.get("log_file")
