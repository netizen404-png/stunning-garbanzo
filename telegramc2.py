import os
import subprocess
from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, filters


HELP_TEXT = """
Available commands:
/login <password> - Authenticate with the bot
/logout - logout
/run <command> - Run a shell command
/upload <absolute_directory> - Save uploaded files in this directory
/download <absolute_file_path> - Download a file
"""


class ManageClient:
    def __init__(self):
        self.__auth_user_ids = []
        self.__auth_password = "alhamdulillah17"
        self.upload_dir = os.getcwd()
        
        
    def __check_logged_in(self, update: Update) -> bool:
        if update.message.from_user.id in self.__auth_user_ids:
            return True
        else:
            return False
        
    
    async def __send_msg(self, update: Update, msg: str):
        MAX_MESSAGE_LEN = 4096
        if len(msg) <= MAX_MESSAGE_LEN:
            await update.message.reply_text(msg)
        else:
            msg_parts = [msg[i:i+MAX_MESSAGE_LEN] for i in range(0, len(msg), MAX_MESSAGE_LEN)]
            for part in msg_parts:
                await update.message.reply_text(part)

        
    async def start(self, update: Update, context: CallbackContext):
        user_name = update.message.from_user.full_name
        print(f"Got connection from user : {user_name}")
        await self.__send_msg(update, "Telegram System Control Bot\nRefer to /help for usage")
    
    
    async def help(self, update: Update, context: CallbackContext):
        await update.message.reply_text(HELP_TEXT)
    
    
    async def login(self, update: Update, context: CallbackContext):
        if self.__check_logged_in(update):
            await self.__send_msg(update, "You are already logged in")
            return
        
        if context.args:
            password = context.args[0]
        else:
            await self.__send_msg(update, "You need to specify password")
            await self.__send_msg(update, "Usage: /login <password>")
            return
        
        if password == self.__auth_password:
            user_id = update.message.from_user.id
            self.__auth_user_ids.append(user_id)
            await self.__send_msg(update, "Successfully authenticated !")
            print(f"Authenticated user id : {user_id}")
        else:
            await self.__send_msg(update, "Password is invalid")
    
            
    async def logout(self, update: Update, context: CallbackContext):
        if not self.__check_logged_in(update):
            await self.__send_msg(update, "You are not logged in")
        else:
            user_id = update.message.from_user.id
            self.__auth_user_ids.remove(user_id)
            await self.__send_msg(update, "You have been logged out")
            
            
    async def run_command(self, update: Update, context: CallbackContext):
        if not self.__check_logged_in(update):
            await self.__send_msg(update, "You are not logged in")
            return
        
        command = " ".join(context.args)
        
        if not command:
            await self.__send_msg(update, "You need to specify command to execute")
            await self.__send_msg(update, "Usage: /run <command>")
            return
        try:
            result = subprocess.run(command, text=True, capture_output=True, check=True, shell=True)
            if isinstance(result, subprocess.CompletedProcess):
                if result.stdout:
                    await self.__send_msg(update, f"Output :\n{result.stdout}")
                if result.stderr:
                    await self.__send_msg(update, f"Error :\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            await self.__send_msg(update, f"An exception occurred : {e}")
        except Exception as e:
            await self.__send_msg(update, f"Unknown Error :\n{e}")
    
    
    async def upload_command(self, update: Update, context: CallbackContext):
        if not self.__check_logged_in(update):
            await self.__send_msg(update, "You are not logged in")
            return
        
        if context.args:
            dir = ' '.join(context.args)
            if os.path.isdir(dir):
                self.upload_dir = dir
                await self.__send_msg(update, f"All files uploaded from now will be stored in \"{dir}\"")
            elif not os.path.exists(dir):
                try:
                    await self.__send_msg(update, f"Directory: \"{dir}\" does not exists")
                    await self.__send_msg(update, f"Creating directory \"{dir}\"")
                    os.makedirs(dir)
                    self.upload_dir = dir
                    await self.__send_msg(update, f"All files uploaded from now will be stored in \"{dir}\"")
                except Exception as e:
                    await self.__send_msg(update, f"An exception occurred: {e}")
                    return
            else:
                await self.__send_msg(update, "Usage: /upload <absoulte_directory>")
        else:
            await self.__send_msg(update, "You need to specify a directory where uploaded files would be stored")
            await self.__send_msg(update, "Usage: /upload <absoulte_directory>")


    async def upload(self, update: Update, context: CallbackContext):
        if not self.__check_logged_in(update):
            await self.__send_msg(update, "You are not logged in")
            return
        
        if update.message.document:
            try:
                file = update.message.document
                file_path = os.path.join(self.upload_dir, file.file_name)
                upload_file = await file.get_file()
                await upload_file.download_to_drive(file_path)
                await self.__send_msg(update, f"File {file.file_name} is uploaded successfully on \"{self.upload_dir}\"")
            except Exception as e:
                await self.__send_msg(update, f"An exception occurred: {e}")
    
    
    async def download(self, update: Update, context: CallbackContext):
        if not self.__check_logged_in(update):
            await self.__send_msg(update, "You are not logged in")
            return
        
        if context.args:
            filename = ' '.join(context.args)
            try:
                if os.path.exists(filename):
                    with open(filename, "rb") as file:
                        await update.message.reply_document(file)
                else:
                    await self.__send_msg(update, f"{filename} not found")
            except Exception as e:
                await self.__send_msg(update, f"An exception occurred: {e}")
        else:
            await self.__send_msg(update, "Please provide absolute file path of file to download")
            await self.__send_msg(update, "Usage: /download <absoulte_file_path>")


if __name__ == "__main__":
    API_TOKEN = "7439956456:AAGCs9x7VCwWN2FMqoff8jjO_Aqz720hSgA"
    
    application = Application.builder().token(API_TOKEN).build()
    
    client = ManageClient()
    
    application.add_handler(CommandHandler("start", client.start))
    application.add_handler(CommandHandler("help", client.help))
    application.add_handler(CommandHandler("login", client.login))
    application.add_handler(CommandHandler("logout", client.logout))
    application.add_handler(CommandHandler("download", client.download))
    application.add_handler(CommandHandler("upload", client.upload_command))
    application.add_handler(CommandHandler("run", client.run_command))
    
    application.add_handler(MessageHandler(filters.Document.ALL, client.upload))
    
    application.run_polling()