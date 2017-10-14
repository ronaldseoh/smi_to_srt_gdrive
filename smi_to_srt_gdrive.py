from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile

from convert import convertSMI

class GDriveSmiToSrtConverter(object):

    def __init__(self):
        self.gauth = GoogleAuth()
        self.gauth.CommandLineAuth()

        self.gdrive = GoogleDrive(self.gauth)

    def select_target_files(self, target_files=None):

        if target_files != None:
            self.target_files = target_files
        else:
            self.target_files = []

            execution_mode_complete = False

            while not execution_mode_complete:
                execution_mode = input(
                    "\n1) Convert all the smi files in the drive 2) Convert specific files/folders: "
                )
                
                if execution_mode == '1':
                    target_files = self.gdrive.ListFile(
                        {
                            'q': "trashed=false and mimeType='application/smil'"
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
                            {"q": "trashed=false and '" + current_directory_id + "' in parents"}
                        ).GetList()

                        for i, file in enumerate(root_file_list):
                            print("[" + str(i)+ "] " + file['title'])

                        file_selection_complete = False

                        while not file_selection_complete:
                            file_selection = input(
                                "\nEnter the number in the brackets to change the working directory \n"
                                + "or select the specific smi file. \n"
                                + "Type A to process all the SMI files in the current working directory \n"
                                + "but NOT including the subdirectories: "
                            )

                            if file_selection == 'A':
                                target_files = self.gdrive.ListFile(
                                    {
                                        "q": "trashed=false and not (mimeType='application/vnd.google-apps.folder') and '" 
                                        + current_directory_id + "' in parents"
                                    }
                                ).GetList()

                                file_selection_complete = True
                                target_selection_complete = True

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

            # Check the write permissions for files in target files
            for file in target_files:
                if file['userPermission']['role'] not in ('writer', 'owner'):
                    print(
                        'WARNING: ' + file['title'] + ' is not writable. '
                        + 'We assume its parent folder also isn\'t. Skipping.'
                    )

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
            for file in self.target_files:
                try:
                    converted_file = self.process_target(file, self.gdrive)
                    print("Conversion successful: " + converted_file['title'])
                except:
                    print("WARNING: Conversion FAILED: " + file['title'])
                
        else:
            raise Exception("target_files has not been specified. Please run select_target_files().")

    @staticmethod
    def process_target(original_file, gdrive_object):

        original_file.FetchContent()
        original_file.GetPermissions()

        smi_content = original_file.content.read()

        srt_string = convertSMI(smi_content)

        srt_file = gdrive_object.CreateFile({'title': original_file['title'].replace('.smi', '.srt')})

        srt_file.SetContentString(srt_string)

        # SetContentString() sets mimeType to 'text/plain' by default
        # Let's change it so that '.txt' extension don't get appended
        # to the file name when we download it
        srt_file['mimeType'] = 'application/octet-stream'

        srt_file['permissions'] = original_file['permissions']

        srt_file['parents'] = original_file['parents']

        srt_file.Upload()

        return srt_file

if __name__ == '__main__':
    converter = GDriveSmiToSrtConverter()

    converter.select_target_files()

    converter.process_all()
