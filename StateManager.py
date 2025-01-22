import sqlite3
from copyreg import pickle
from typing import Optional


class CharacterNotFound(Exception):
    pass

class StateManager:
    def __init__(self):
        self.databaseConnection = sqlite3.connect('states.db')
        # validate table existence
        cursor = self.databaseConnection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, datetime INTEGER, message TEXT, linkedmessageid INTEGER, remindees TEXT, channel INTEGER)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS userscolors (id INTEGER PRIMARY KEY, updateddatetime INTEGER, userid INTEGER, color TEXT, colorname TEXT)''')

        #cursor.execute('''CREATE TABLE IF NOT EXISTS snitchdb (id INTEGER PRIMARY KEY, datetime INTEGER, message TEXT, linkedmessageid INTEGER)''')
        cursor.close()






    #TODO could there be some dumb issue with race conditions?
    def updateUserColor(self, user: int, updateDateTime: int, color:str, colorname:str, override=False):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''INSERT INTO userscolors (updateddatetime, userid, color, colorname) VALUES (?,?,?,?)''',
                           (updateDateTime, user, color, colorname))
        cursor.connection.commit()
        return True


    def getUserColor(self, user: int):
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT MAX(updateddatetime), color, colorname FROM userscolors WHERE userid=?", (user,))
        headers = list(map(lambda attr: attr[0], cursor.description))
        row = cursor.fetchone()
        rowMapped = {header: row[i] for i, header in enumerate(headers)}
        return (rowMapped['color'],rowMapped['colorname'])

    def getUsedColors(self):
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT MAX(updateddatetime), color, colorname FROM userscolors group by userid", ())
        rows = cursor.fetchall()
        ids = [row[1].removeprefix("https://lh3.googleusercontent.com/d/") for row in rows]
        print(len(ids))
        return ids


    def setUserInitialCharacter(self, userID: int, character):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''UPDATE characters SET cur_user = ? WHERE name = ?''',(userID, character['name']))
        cursor.connection.commit()
        return True

    #TODO could there be some dumb issue with race conditions?
    def updateUserCharacter(self, userID: int, character, oldcharacter):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''UPDATE characters SET cur_user = NULL WHERE name = ?''',(oldcharacter['name'],))
        cursor.execute('''UPDATE characters SET cur_user = ? WHERE name = ?''',(userID, character['name']))
        cursor.connection.commit()
        return True

    def getCurrentCharacter(self,userID):
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT name, avatar_url, category, user_id_lock, cur_user FROM characters WHERE cur_user IS ?", (userID,))
        headers = list(map(lambda attr: attr[0], cursor.description))
        row = cursor.fetchone()
        if row is None:
            return None
        rowMapped = {header: row[i] for i, header in enumerate(headers)}
        return rowMapped

    def upsertCharacter(self, name, url):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''INSERT INTO characters(name,avatar_url) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET avatar_url = excluded.avatar_url''', (name, url))
        cursor.connection.commit()
        return True

    def getRandomCharacter(self):
        #todo add error for if somehow all characters are used
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT name, avatar_url, category, user_id_lock, cur_user FROM characters WHERE cur_user IS NULL AND user_id_lock IS NULL ORDER BY RANDOM() LIMIT 1", ())
        headers = list(map(lambda attr: attr[0], cursor.description))
        row = cursor.fetchone()
        if row is None:
            return None
        rowMapped = {header: row[i] for i, header in enumerate(headers)}
        return rowMapped

    def getMyCharacter(self, userID):
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT name, avatar_url, category, user_id_lock, cur_user FROM characters WHERE  user_id_lock IS ?", (userID,))
        headers = list(map(lambda attr: attr[0], cursor.description))
        row = cursor.fetchone()
        if row is None:
            return None
        rowMapped = {header: row[i] for i, header in enumerate(headers)}
        return rowMapped

    #TODO allow users to get their own name?
    def getSpecificCharacter(self, name):
        cursor = self.databaseConnection.cursor()
        cursor.execute("SELECT name, avatar_url, category, user_id_lock, cur_user FROM characters WHERE name IS ? AND USER_ID_LOCK is NULL", (name,))
        headers = list(map(lambda attr: attr[0], cursor.description))
        row = cursor.fetchone()
        if row is None:
            raise CharacterNotFound("No such character")
        rowMapped = {header: row[i] for i, header in enumerate(headers)}
        return rowMapped


    #TODO add ability for users to control their reminders
    #     add in-discord storage capabilities
    def addReminder(self, creator: int, unixTimestamp, channelID: int, text: Optional[str], linkedMessageID: Optional[int]):
        cursor = self.databaseConnection.cursor()
        remindeeString=str(creator)+","
        cursor.execute('''INSERT INTO reminders (datetime, message, linkedmessageid, remindees, channel) VALUES (?,?,?,?,?)''', (unixTimestamp, text, linkedMessageID, remindeeString, channelID))
        cursor.connection.commit()
        id = cursor.lastrowid
        cursor.close()
        return id

    def setReminderPost(self, messageID,reminderID):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''UPDATE reminders SET linkedmessageid = ? WHERE id = ?''', (messageID, reminderID, ))
        cursor.connection.commit()
        id = cursor.lastrowid
        cursor.close()
        return id

    def removeReminder(self, id: int):
        cursor = self.databaseConnection.cursor()
        cursor.execute(''' DELETE from reminders where id = ?''',(id,))
        cursor.connection.commit()
        cursor.close()
        return True

    def addReminderPost(self, id: int):
        #TODO I actually wanna build this two ways, one with a database, one by using discord as a database, essentially
        cursor = self.databaseConnection.cursor()
        cursor.execute(''' DELETE from reminders where id = ?''',(id,))
        cursor.connection.commit()
        cursor.close()
        return True


    def getAllReminderTimes(self):
        cursor = self.databaseConnection.cursor()
        cursor.execute('SELECT id, datetime FROM reminders ORDER BY datetime') #grabbing all might be cumbersome later but right now its fine
        idTimes = {}
        for unixTime in cursor:
            if unixTime[0] not in idTimes:
                idTimes[unixTime[0]] = unixTime[1]
        cursor.close()
        return idTimes

    def getReminder(self, reminderID: int):
        cursor = self.databaseConnection.cursor()
        cursor.execute('SELECT * FROM reminders WHERE id = ?',(reminderID,))
        results = cursor.fetchall()
        cursor.close()
        return results[0]

    def addRemindeeFromMessageID(self,remindeeID, reminderMessageID):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''SELECT remindees FROM reminders WHERE linkedmessageid = ?''', (reminderMessageID,))
        results = cursor.fetchall()[0][0]
        resultsSplit = results.split(",")
        for result in resultsSplit:
            if result != '' and remindeeID == int(result):
                cursor.close()
                return
        results += str(remindeeID)+","
        cursor.execute('''UPDATE reminders SET remindees = ? WHERE linkedmessageid = ?''', (results,reminderMessageID,))
        cursor.connection.commit()
        cursor.close()
        return

    def remove_remindee_from_message_id(self, remindeeID, reminderMessageID):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''SELECT remindees FROM reminders WHERE linkedmessageid = ? ''', (reminderMessageID,))
        results = cursor.fetchall()[0][0]
        resultsSplit = results.split(",")
        resultsSplitPurged = [x for x in resultsSplit if not (str(remindeeID) in x)]
        resultsSplitPurgedString = ",".join(resultsSplitPurged)
        cursor.execute('''UPDATE reminders SET remindees = ? WHERE linkedmessageid = ?''', (resultsSplitPurgedString,reminderMessageID,))
        cursor.connection.commit()
        cursor.close()
        return

    def getReminderAlertData(self, reminderID: int):
        cursor = self.databaseConnection.cursor()
        cursor.execute('SELECT channel, message, remindees FROM reminders WHERE id = ?',(reminderID,))
        results = cursor.fetchall()
        cursor.close()
        return results[0]

    """def addSnitchLog(self, author: int, unixTimestamp, text: Optional[str], linkedMessageID: int):
        cursor = self.databaseConnection.cursor()
        cursor.execute('''INSERT INTO reminders (datetime, message, linkedmessageid, remindees) VALUES (?,?,?,?)''', (unixTimestamp, text, linkedMessageID, remindeeString))
        cursor.connection.commit()
        cursor.close()
        return True"""
