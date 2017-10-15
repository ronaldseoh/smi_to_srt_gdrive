import threading
import time

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from convert import convertSMI

class GDriveSmiToSrtConverter(object):

    def __init__(self, gdrive=None):
        if gdrive != None:
            self.gdrive = gdrive
        else:
            self.gauth = GoogleAuth()
            self.gauth.CommandLineAuth()

            self.gdrive = GoogleDrive(self.gauth)

    def select_target_files(self, target_files=None):

        # If this class is imported from another pydrive-based application,
        # you can create target_files from somewhere and directly plug it into
        # self.target_files.
        if target_files != None:
            self.target_files = target_files
        else:
            self.target_files = []

            execution_mode_complete = False

            drive_exploration_history = []

            while not execution_mode_complete:
                execution_mode = input(
                    "\n1) Convert all the smi files in the drive 2) Convert specific files/folders: "
                )
                
                if execution_mode == '1':
                    target_files = self.gdrive.ListFile(
                        {
                            'q': "trashed=false and mimeType='application/smil'",
                            'orderBy': "title"
                        }
                    ).GetList()

                    execution_mode_complete = True

                elif execution_mode == '2':
                    target_selection_complete = False
                    current_directory_id = 'root'

                    self.target_files = []
                    
                    while not target_selection_complete:
                        print("\nGetting the list of files in the current working folder...\n")

                        root_file_list = self.gdrive.ListFile(
                            {
                                "q": "trashed=false and '" + current_directory_id + "' in parents",
                                "orderBy": "title"
                            }
                        ).GetList()

                        drive_exploration_history.append(current_directory_id)

                        for i, file in enumerate(root_file_list):
                            print("[" + str(i)+ "] " + file['title'])

                        file_selection_complete = False

                        while not file_selection_complete:
                            file_selection = input(
                                "\nEnter the number in the brackets to change the working directory \n"
                                + "or select the specific smi file. \n"
                                + "Type B to go back to the upper directory. \n"
                                + "Type A to process all the SMI files in the current working directory \n"
                                + "but NOT including the subdirectories: "
                            )

                            if file_selection == 'A':
                                target_files = self.gdrive.ListFile(
                                    {
                                        "q": "trashed=false and not (mimeType='application/vnd.google-apps.folder') and '" 
                                        + current_directory_id + "' in parents",
                                        "orderBy": "title"
                                    }
                                ).GetList()

                                file_selection_complete = True
                                target_selection_complete = True

                            elif file_selection == 'B':

                                if len(drive_exploration_history) == 1:
                                    print(
                                        "\nThere is no record of previous directories. "
                                        + "This probably means you are at the root folder.\n"
                                    )
                                else:
                                    drive_exploration_history.pop()

                                    current_directory_id = drive_exploration_history.pop()

                                    file_selection_complete = True

                            elif file_selection.isdigit():
                                file_selection = int(file_selection)

                                if file_selection < len(root_file_list):
                                    if root_file_list[file_selection]['mimeType'] == 'application/vnd.google-apps.folder':
                                        current_directory_id = root_file_list[file_selection]['id']

                                        file_selection_complete = True

                                    else:
                                        target_files = [root_file_list[file_selection]]

                                        file_selection_complete = True
                                        target_selection_complete = True

                            else:
                                continue

                    execution_mode_complete = True

                else:
                    continue

            
            # Check the properties of files in target_files
            for i, file in enumerate(target_files):
                # Check the write permissions for files in target files
                if not file['title'].lower().endswith('.smi'):
                    print(
                        "WARNING: The file extension of " + file['title']
                        + " is not '.smi'. Skipping." 
                    )

                elif file['userPermission']['role'] not in ('writer', 'owner'):
                    print(
                        'WARNING: ' + file['title'] + ' is not writable. '
                        + 'We assume its parent folder also isn\'t. Skipping.'
                    )

                # If mimeType of the file isn't that of a SMI file, 
                # check if the user wants to force-convert the file
                elif file['mimeType'] != 'application/smil':
                    while True:
                        force_conversion = input(
                            "\n" + file['title'] + " doesn't look like a SMI file.\n"
                            + "This file\'s MIME type is recognized as "
                            + file['mimeType'] + ". \n"
                            + "Would you like to try converting this file? [y/n] "
                        )

                        if force_conversion.lower() == 'y':
                            self.target_files.append(file)
                            break
                        elif force_conversion.lower() == 'n':
                            break
                else:
                    self.target_files.append(file)

    def process_all(self):
        if hasattr(self, 'target_files'):
            threads = []

            for file in self.target_files:
                # See if a srt file already exists for the target
                smi_title_extension_index  = file['title'].lower().rfind('.smi')
                srt_title = file['title'][0:smi_title_extension_index] + '.srt'

                existing_srt_file_query = "trashed=false and ("

                existing_srt_file_query += "'" + file['parents'][0]['id'] + "' in parents "

                for parent in file['parents'][1:]:
                    existing_srt_file_query += "OR '" + parent['id'] + "' in parents "

                existing_srt_file_query += ") and title contains '" + srt_title + "'"

                existing_srt_file = self.gdrive.ListFile(
                    {
                        'q': existing_srt_file_query,
                        'orderBy': 'title'
                    }
                ).GetList()

                if len(existing_srt_file) > 0:
                    print(srt_title + " already exists in the same directory. Skipping.")

                else:
                    http = self.gdrive.auth.Get_Http_Object()
                    
                    conversion_thread = threading.Thread(target=self.process_target, args=(file, self.gdrive, http))
                    
                    threads.append(conversion_thread)

                    time.sleep(0.5)

                    conversion_thread.start()
        else:
            print("ERROR: target_files has not been specified. Please run select_target_files().")

    @staticmethod
    def process_target(original_file, gdrive_object, http_object):
        try:
            original_file.FetchContent()
            original_file.GetPermissions()

            smi_content = original_file.content.read()

            srt_string = convertSMI(smi_content)

            smi_title_extension_index = original_file['title'].lower().rfind('.smi')

            srt_file = gdrive_object.CreateFile(
                {'title': '%s.srt' % original_file['title'][0:smi_title_extension_index]}
            )

            srt_file.SetContentString(srt_string)

            # SetContentString() sets mimeType to 'text/plain' by default
            # Let's change it so that '.txt' extension don't get appended
            # to the file name when we download it
            srt_file['mimeType'] = 'application/octet-stream'

            srt_file['permissions'] = original_file['permissions']

            srt_file['parents'] = original_file['parents']

            srt_file.Upload(param={"http": http_object})

            print("Conversion successful: " + srt_file['title'])

        except Exception as e:
            print(str(e))
            print("ERROR: Conversion FAILED: " + original_file['title'])


if __name__ == '__main__':
    converter = GDriveSmiToSrtConverter()

    converter.select_target_files()

    converter.process_all()
