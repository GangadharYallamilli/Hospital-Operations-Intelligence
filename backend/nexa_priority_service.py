from contextlib import contextmanager
import os
import logging

import mysql.connector
from mysql.connector import Error as MySQLError
import pandas as pd

from backend.nexa_priority import build_nexa_priority

from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)


@contextmanager
def equipment_cursor():

    connection = None

    try:

        user = os.getenv("MYSQL_READONLY_USER")
        password = os.getenv("MYSQL_READONLY_PASSWORD")

        if not user or not password:
            raise Exception(
                "MySQL readonly credentials are missing"
            )

        connection = mysql.connector.connect(

            host=os.getenv(
                "MYSQL_HOST",
                "127.0.0.1"
            ),

            port=int(
                os.getenv(
                    "MYSQL_PORT",
                    "3306"
                )
            ),

            user=user,

            password=password,

            database=os.getenv(
                "MYSQL_DATABASE",
                "hospital_operations"
            ),

            connection_timeout=5,

        )


        cursor = connection.cursor(
            dictionary=True
        )


        try:
            yield cursor

        finally:
            cursor.close()


    except MySQLError as error:

        logger.error(
            "Equipment database error: %s",
            error
        )

        raise


    finally:

        if connection:
            connection.close()



def get_equipment_priority(
        top_n=20
):

    """
    Read hospital equipment table
    and generate NexaPriority ranking.
    """


    query = """

    SELECT
        equipment_id,
        department_id,
        equipment_type,
        installation_date,
        last_maintenance_date,
        next_maintenance_date,
        equipment_status,
        usage_hours,
        maintenance_count,
        failure_count

    FROM equipment

    """


    try:

        with equipment_cursor() as cursor:

            cursor.execute(query)

            rows = cursor.fetchall()


        if not rows:

            return {

                "status": "unavailable",

                "message":
                "No equipment records found.",

                "priority_list": []

            }


        dataframe = pd.DataFrame(rows)


        result = build_nexa_priority(
            dataframe,
            top_n=top_n
        )


        result["source"] = (
            "Hospital operational database"
        )


        return result


    except Exception as error:

        return {

            "status": "error",

            "message": str(error),

            "priority_list": []

        }