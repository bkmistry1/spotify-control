from discord import Interaction
import pymongo
from pymongo import ReturnDocument
import os
from dotenv import load_dotenv
from datetime import timedelta
import datetime

load_dotenv()

dbName = os.getenv("dbName")

async def insertIntoCollection(colName, mydict):
    myclient = pymongo.MongoClient(os.getenv("mongoConn"))
    mydb = myclient[dbName]
    mycol = mydb[colName]

    inserted = mycol.insert_one(mydict)
    insertedId = inserted.inserted_id

    myclient.close()

    return insertedId

async def findFromDb(colName, dict):

    myclient = pymongo.MongoClient(os.getenv("mongoConn"))
    mydb = myclient[dbName]
    mycol = mydb[colName]

    received = []
    for item in mycol.find(dict):
        received.append(item)

    myclient.close()

    return received

async def findOneFromDb(colName, dict):

    myclient = pymongo.MongoClient(os.getenv("mongoConn"))
    mydb = myclient[dbName]
    mycol = mydb[colName]

    received = mycol.find_one(dict)

    myclient.close()

    return received

async def deleteOneFromDb(colName, dict):

    myclient = pymongo.MongoClient(os.getenv("mongoConn"))
    mydb = myclient[dbName]
    mycol = mydb[colName]

    received = mycol.delete_one(dict)

    myclient.close()

    return received

async def findOneAndUpdate(colName, filter, dict):
    myclient = pymongo.MongoClient(os.getenv("mongoConn"))
    mydb = myclient[dbName]
    mycol = mydb[colName]

    newDoc = mycol.find_one_and_update(filter=filter, update=dict, return_document = ReturnDocument.AFTER)    
    myclient.close()
    return newDoc